"""Enum registries of model name strings for each supported LLM provider."""

import enum


class Anthropic(enum.Enum):
    """Anthropic Claude model identifiers."""

    CLAUDE_OPUS_4 = "claude-opus-4-6"
    CLAUDE_SONNET_4 = "claude-sonnet-4-6"
    CLAUDE_HAIKU_4 = "claude-haiku-4-5-20251001"
    CLAUDE_3p5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3p5_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"


class Google(enum.Enum):
    """Google Gemini model identifiers (Google AI Studio)."""

    GEMINI_3p8_FLASH = "gemini-3.8-flash"
    GEMINI_3p6_FLASH = "gemini-3.6-flash"
    GEMINI_3p5_FLASH_LITE = "gemini-3.5-flash-lite"
    GEMINI_3p1_FLASH_LITE = "gemini-3.1-flash-lite"
    GEMINI_3_FLASH = "gemini-3-flash-preview"
    GEMINI_2p5_FLASH = "gemini-2.5-flash"
    GEMINI_2p5_FLASH_LITE = "gemini-2.5-flash-lite"


class Gemma(enum.Enum):
    """Google Gemma model identifiers (served via the Gemini API)."""

    GEMMA_4_26B = "gemma-4-26b-a4b-it"
    GEMMA_4_31B = "gemma-4-31b-it"


class OpenAI(enum.Enum):
    """OpenAI model identifiers."""

    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    O1 = "o1"
    O1_MINI = "o1-mini"
    O3 = "o3"
    O3_MINI = "o3-mini"
    O4_MINI = "o4-mini"
