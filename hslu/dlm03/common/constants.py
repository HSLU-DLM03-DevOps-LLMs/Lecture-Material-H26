"""API base URLs and environment variable names for all supported LLM providers."""

GOOGLE_OPENAI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"
GOOGLE_API_KEY_ENV_VAR = "GOOGLE_API_KEY"  # Legacy name, still supported.

OPENAI_API_BASE_URL = "https://api.openai.com/v1"
OPENAI_API_KEY_ENV_VAR = "OPENAI_API_KEY"

ANTHROPIC_API_BASE_URL = "https://api.anthropic.com/v1/"
ANTHROPIC_API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"

LLAMA_CPP_API_KEY_ENV_VAR = "LLAMA_CPP_API_KEY"
LLAMA_CPP_BASE_URL = "http://localhost:8080/v1"
