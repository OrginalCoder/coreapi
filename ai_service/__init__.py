"""AI Service package for CoreAPI."""

from .client import (
    AIClient,
    AIClientError,
    AIProviderUnavailableError,
    AIProviderTimeoutError,
    AIProviderResponseError,
    ask_ai,
)

__all__ = [
    'AIClient',
    'AIClientError',
    'AIProviderUnavailableError',
    'AIProviderTimeoutError',
    'AIProviderResponseError',
    'ask_ai',
]
