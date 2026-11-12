"""Pre-configured backends for every supported model."""

import dataclasses
import os

from hslu.dlm03.common import config, constants, models


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class GoogleConfig(config.Config):
    """Base config for Google AI Studio backends."""

    base_url: str = constants.GOOGLE_OPENAI_API_BASE_URL
    api_key: str | None = os.environ.get(
        constants.GEMINI_API_KEY_ENV_VAR, os.environ.get(constants.GOOGLE_API_KEY_ENV_VAR),
    )


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class AnthropicConfig(config.Config):
    """Base config for Anthropic backends."""

    base_url: str = constants.ANTHROPIC_API_BASE_URL
    api_key: str | None = os.environ.get(constants.ANTHROPIC_API_KEY_ENV_VAR, None)


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class OpenAIConfig(config.Config):
    """Base config for OpenAI backends."""

    base_url: str = constants.OPENAI_API_BASE_URL
    api_key: str | None = os.environ.get(constants.OPENAI_API_KEY_ENV_VAR, None)


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class LLamaCpp(config.Config):
    """Backend for local llama.cpp servers (OpenAI-compatible /v1 endpoint)."""

    name: str = "llama.cpp"
    base_url: str = constants.LLAMA_CPP_BASE_URL
    model_name: str = "model"
    api_key: str | None = os.environ.get(constants.LLAMA_CPP_API_KEY_ENV_VAR, "sk-")


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Gemini3p8Flash(GoogleConfig):
    """Gemini 3.8 Flash — free tier: 5 RPM, 250K TPM, 20 RPD."""

    name: str = "Gemini 3.8 Flash"
    model_name: str = models.Google.GEMINI_3p8_FLASH.value
    rpm: float | None = 5.


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Gemini3p6Flash(GoogleConfig):
    """Gemini 3.6 Flash — free tier: 5 RPM, 250K TPM, 20 RPD."""

    name: str = "Gemini 3.6 Flash"
    model_name: str = models.Google.GEMINI_3p6_FLASH.value
    rpm: float | None = 5.


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Gemini3p5FlashLite(GoogleConfig):
    """Gemini 3.5 Flash Lite — free tier: 15 RPM, 250K TPM, 500 RPD."""

    name: str = "Gemini 3.5 Flash Lite"
    model_name: str = models.Google.GEMINI_3p5_FLASH_LITE.value
    rpm: float | None = 15.


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Gemini3p1FlashLite(GoogleConfig):
    """Gemini 3.1 Flash Lite — free tier: 15 RPM, 250K TPM, 500 RPD."""

    name: str = "Gemini 3.1 Flash Lite"
    model_name: str = models.Google.GEMINI_3p1_FLASH_LITE.value
    rpm: float | None = 15.


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Gemini3Flash(GoogleConfig):
    """Gemini 3 Flash (preview) — free tier: 5 RPM, 250K TPM, 20 RPD."""

    name: str = "Gemini 3 Flash"
    model_name: str = models.Google.GEMINI_3_FLASH.value
    rpm: float | None = 5.


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Gemini2p5Flash(GoogleConfig):
    """Gemini 2.5 Flash — free tier: 5 RPM, 250K TPM, 20 RPD."""

    name: str = "Gemini 2.5 Flash"
    model_name: str = models.Google.GEMINI_2p5_FLASH.value
    rpm: float | None = 5.


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Gemini2p5FlashLite(GoogleConfig):
    """Gemini 2.5 Flash Lite — free tier: 10 RPM, 250K TPM, 20 RPD."""

    name: str = "Gemini 2.5 Flash Lite"
    model_name: str = models.Google.GEMINI_2p5_FLASH_LITE.value
    rpm: float | None = 10.


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Gemma4_26B(GoogleConfig):  # noqa: N801
    """Gemma 4 26B — free tier: 30 RPM, 16K TPM, 14.4K RPD."""

    name: str = "Gemma 4 26B"
    model_name: str = models.Gemma.GEMMA_4_26B.value
    rpm: float | None = 30.


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Gemma4_31B(GoogleConfig):  # noqa: N801
    """Gemma 4 31B — free tier: 30 RPM, 16K TPM, 14.4K RPD."""

    name: str = "Gemma 4 31B"
    model_name: str = models.Gemma.GEMMA_4_31B.value
    rpm: float | None = 30.


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class ClaudeOpus4(AnthropicConfig):
    """Claude Opus 4."""

    name: str = "Claude Opus 4"
    model_name: str = models.Anthropic.CLAUDE_OPUS_4.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class ClaudeSonnet4(AnthropicConfig):
    """Claude Sonnet 4."""

    name: str = "Claude Sonnet 4"
    model_name: str = models.Anthropic.CLAUDE_SONNET_4.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class ClaudeHaiku4(AnthropicConfig):
    """Claude Haiku 4."""

    name: str = "Claude Haiku 4"
    model_name: str = models.Anthropic.CLAUDE_HAIKU_4.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Claude3p5Sonnet(AnthropicConfig):
    """Claude 3.5 Sonnet."""

    name: str = "Claude 3.5 Sonnet"
    model_name: str = models.Anthropic.CLAUDE_3p5_SONNET.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Claude3p5Haiku(AnthropicConfig):
    """Claude 3.5 Haiku."""

    name: str = "Claude 3.5 Haiku"
    model_name: str = models.Anthropic.CLAUDE_3p5_HAIKU.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class Claude3Opus(AnthropicConfig):
    """Claude 3 Opus."""

    name: str = "Claude 3 Opus"
    model_name: str = models.Anthropic.CLAUDE_3_OPUS.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class GPT4o(OpenAIConfig):
    """GPT-4o."""

    name: str = "GPT-4o"
    model_name: str = models.OpenAI.GPT_4O.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class GPT4oMini(OpenAIConfig):
    """GPT-4o Mini."""

    name: str = "GPT-4o Mini"
    model_name: str = models.OpenAI.GPT_4O_MINI.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class O1(OpenAIConfig):
    """OpenAI o1."""

    name: str = "o1"
    model_name: str = models.OpenAI.O1.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class O1Mini(OpenAIConfig):
    """OpenAI o1-mini."""

    name: str = "o1-mini"
    model_name: str = models.OpenAI.O1_MINI.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class O3(OpenAIConfig):
    """OpenAI o3."""

    name: str = "o3"
    model_name: str = models.OpenAI.O3.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class O3Mini(OpenAIConfig):
    """OpenAI o3-mini."""

    name: str = "o3-mini"
    model_name: str = models.OpenAI.O3_MINI.value


@dataclasses.dataclass(kw_only=True, unsafe_hash=True)
class O4Mini(OpenAIConfig):
    """OpenAI o4-mini."""

    name: str = "o4-mini"
    model_name: str = models.OpenAI.O4_MINI.value


CONFIGS: set[config.Config] = {
    Gemini3p8Flash(), Gemini3p6Flash(), Gemini3p5FlashLite(), Gemini3p1FlashLite(), Gemini3Flash(),
    Gemini2p5Flash(), Gemini2p5FlashLite(),
    Gemma4_26B(), Gemma4_31B(),
    ClaudeOpus4(), ClaudeSonnet4(), ClaudeHaiku4(),
    Claude3p5Sonnet(), Claude3p5Haiku(), Claude3Opus(),
    GPT4o(), GPT4oMini(), O1(), O1Mini(), O3(), O3Mini(), O4Mini(),
    LLamaCpp(),
}
CONFIGS_BY_NAME: dict[str, config.Config] = {b.name: b for b in CONFIGS}
