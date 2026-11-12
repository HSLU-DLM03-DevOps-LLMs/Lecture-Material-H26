"""Provides a base configuration class for LLM backends."""
import dataclasses

import openai


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Config:
    """Abstract base class for all LLM backends.

    This class defines the common interface and attributes expected from any LLM backend and ways to instantiate
    matching clients using the `openai` library
    """

    name: str
    """A human-readable name for the backend."""
    base_url: str
    """The base URL for the LLM API endpoint."""
    model_name: str
    """The specific model identifier to be used with this backend."""
    api_key: str | None = None
    """The API key required for authentication with the LLM service (optional)."""
    rpm: float | None = None
    """Requests-per-minute cap (free-tier limit). ``None`` means no limit is enforced."""
    max_retries: int = 10
    """How often the client retries failed requests (e.g. the frequent HTTP 500s of Gemma on Google's endpoint)."""

    def get_async_client(self) -> tuple[openai.AsyncClient, str]:
        """Returns an asynchronous OpenAI client configured for this backend and the model name.

        This method abstracts the client creation, allowing different backends to use
        the same `openai.AsyncClient` interface, which is compatible with many LLM APIs.

        Returns:
            tuple[openai.AsyncClient, str]: A tuple containing the configured
                                            `openai.AsyncClient` instance and the model name.
        """
        client = openai.AsyncClient(base_url=self.base_url, api_key=self.api_key, max_retries=self.max_retries)
        return client, self.model_name

    def get_client(self) -> tuple[openai.Client, str]:
        """Returns a synchronous OpenAI client configured for this backend and the model name.

        This method abstracts the client creation, allowing different backends to use
        the same `openai.Client` interface, which is compatible with many LLM APIs.

        Returns:
            tuple[openai.Client, str]: A tuple containing the configured
                                       `openai.Client` instance and the model name.
        """
        client = openai.Client(base_url=self.base_url, api_key=self.api_key, max_retries=self.max_retries)
        return client, self.model_name
