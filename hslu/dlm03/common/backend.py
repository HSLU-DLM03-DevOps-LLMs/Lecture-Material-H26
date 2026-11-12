"""This file provides abstractions for interacting with various LLM backends."""

import asyncio
import itertools
import re
import time
from typing import Any, Self

import openai

from hslu.dlm03.common import chat as chat_lib
from hslu.dlm03.common import config as config_lib
from hslu.dlm03.common import types
from hslu.dlm03.util import ratelimit

_MAX_ATTEMPTS = 10
"""How many times a request is attempted before giving up."""
_DEFAULT_RATE_LIMIT_DELAY_SECONDS = 60.0
"""How long to wait after hitting a rate limit if the provider does not say (free-tier quotas are per minute)."""
_REQUEST_TIMEOUT_SECONDS = 120.0
"""How long to wait for a response before retrying (Gemma on Google's endpoint sometimes never answers)."""


def _retry_delay(error: openai.APIError, attempt: int) -> float | None:
    """Returns how long to wait before retrying a failed request.

    Rate limits (HTTP 429), e.g. the free-tier input tokens per minute that agents with long histories easily hit,
    only clear once the quota window moves on, so we wait as long as the provider asks (Google says it in the error
    message). Server errors (HTTP 5xx), e.g. the frequent HTTP 500s of Gemma on Google's endpoint, as well as connection
    errors and timeouts, are retried with exponential backoff.

    Args:
        error: The error returned by the API.
        attempt: The number of the attempt that failed, starting at 0.

    Returns:
        The number of seconds to wait, or `None` if the request should not be retried.
    """
    if attempt + 1 >= _MAX_ATTEMPTS:
        return None
    if isinstance(error, openai.RateLimitError):
        match = re.search(r"retry in ([\d.]+)s", str(error))
        return float(match.group(1)) + 1 if match else _DEFAULT_RATE_LIMIT_DELAY_SECONDS
    if isinstance(error, openai.InternalServerError | openai.APIConnectionError):
        return min(2.0**attempt, 8.0)
    return None


class LLM:
    """A class that provides an interface to an LLM backend.

    It uses an `openai.Client` to interact with the LLM and enforces a
    rate limit on the number of calls per minute.
    """
    _client: openai.Client
    _model: str
    _ratelimiter: ratelimit.RateLimiter

    def __init__(self, *, client: openai.Client, model: str, ratelimiter: ratelimit.RateLimiter) -> None:
        """Initializes an `LLM` instance.

        Args:
            client: The OpenAI client.
            model: The model name.
            ratelimiter: The rate limiter.
        """
        self._client = client
        self._model = model
        self._ratelimiter = ratelimiter

    def __call__(self, *, response_format: type | None = None, **kwargs: Any) -> types.ModelResponse:
        """Calls the LLM backend and returns its output, retrying on rate limits and server errors.

        Args:
            response_format: The type of the expected response from the model.
            **kwargs: Additional keyword arguments to pass to the API call.

        Returns:
            A `types.ModelResponse` object representing the model's response.
        """
        if response_format is not None:
            kwargs["response_format"] = response_format
            fn = self._client.chat.completions.parse
        else:
            fn = self._client.chat.completions.create
        for attempt in itertools.count():
            try:
                with self._ratelimiter:
                    return fn(model=self._model, **kwargs)
            except (openai.APIStatusError, openai.APIConnectionError) as error:
                delay = _retry_delay(error, attempt)
                if delay is None:
                    raise
                time.sleep(delay)
        raise AssertionError  # Unreachable, but makes the type checker happy.

    def generate(self, chat: chat_lib.Chat, /, **kwargs: Any) -> types.ModelResponse:
        """Generates a response from the LLM based on the provided chat history.

        Args:
            chat: A `chat_lib.Chat` object containing the conversation history.
            **kwargs: Additional keyword arguments to pass to the `__call__` method.

        Returns:
            A `types.ModelResponse` object representing the model's response.

        """
        return self(messages=chat.messages, **kwargs)

    @classmethod
    def from_config(cls, config: config_lib.Config) -> Self:
        """Instantiates an `LLM` instance from a configuration object.

        Args:
            config: The configuration object to use.

        Returns:
            An `LLM` instance.
        """
        client, _ = config.get_client()
        # Retries are handled by `__call__`.
        client = client.with_options(max_retries=0, timeout=_REQUEST_TIMEOUT_SECONDS)
        ratelimiter = ratelimit.RateLimiter(config.rpm)
        return cls(client=client, model=config.model_name, ratelimiter=ratelimiter)


class AsyncLLM:
    """A class that provides an asynchronous interface to an LLM backend.

    It uses an `openai.AsyncClient` to interact with the LLM and enforces a
    rate limit on the number of calls per minute.
    """
    _client: openai.AsyncClient
    """The underlying OpenAI async client."""
    _model: str
    """The model name."""
    _ratelimiter: ratelimit.RateLimiter
    """The rate limiter."""

    def __init__(self, *, client: openai.AsyncClient, model: str, ratelimiter: ratelimit.RateLimiter) -> None:
        """Initializes an `AsyncLLM` instance.

        Args:
            client: The OpenAI async client.
            model: The model name.
            ratelimiter: The rate limiter.
        """
        self._client = client
        self._model = model
        self._ratelimiter = ratelimiter

    async def __call__(self, *, response_format: type | None = None, **kwargs: Any) -> types.ModelResponse:
        """Calls the LLM backend and returns its output, retrying on rate limits and server errors.

        Args:
            response_format: `The type of the expected response from the model.`
            **kwargs: Additional keyword arguments to pass to the API call.

        Returns:
            A `types.ModelResponse` object representing the model's response.
        """
        if response_format is not None:
            kwargs["response_format"] = response_format
            fn = self._client.chat.completions.parse
        else:
            fn = self._client.chat.completions.create
        for attempt in itertools.count():
            try:
                with self._ratelimiter:
                    return await fn(model=self._model, **kwargs)
            except (openai.APIStatusError, openai.APIConnectionError) as error:
                delay = _retry_delay(error, attempt)
                if delay is None:
                    raise
                await asyncio.sleep(delay)
        raise AssertionError  # Unreachable, but makes the type checker happy.

    async def generate(self, chat: chat_lib.Chat, /, **kwargs: Any) -> types.ModelResponse:
        """Generates a response from the LLM asynchronously based on the chat history.

        Args:
            chat: A `chat_lib.Chat` object containing the conversation history.
            **kwargs: Additional keyword arguments to pass to the `__call__` method.

        Returns:
            A `types.ModelResponse` object representing the model's response.

        """
        return await self(messages=chat.messages, **kwargs)

    @classmethod
    def from_config(cls, config: config_lib.Config) -> Self:
        """Instantiates an `AsyncLLM` instance from a configuration object.

        Args:
            config: The configuration object to use.

        Returns:
            An `AsyncLLM` instance.
        """
        client, _ = config.get_async_client()
        # Retries are handled by `__call__`.
        client = client.with_options(max_retries=0, timeout=_REQUEST_TIMEOUT_SECONDS)
        ratelimiter = ratelimit.RateLimiter(config.rpm)
        return cls(client=client, model=config.model_name, ratelimiter=ratelimiter)
