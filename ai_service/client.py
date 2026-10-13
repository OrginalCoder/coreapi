"""AI Provider client for CoreAPI.

This module encapsulates all external communication with the AI provider.
Supported provider types:
- groq: Direct Groq Cloud API integration using official Groq SDK / HTTP (Llama 3, openai/gpt-oss-safeguard-20b, etc.)
- openai_compatible: Any standard OpenAI-compatible API endpoint (Groq, OpenRouter, OpenAI, Ollama, etc.)
- freegpt4: Local Free-GPT4-WEB-API server (default: http://127.0.0.1:5500)
"""

import os
import logging
import re
from typing import Optional
import requests
from django.conf import settings

from .prompts import DEFAULT_SYSTEM_INSTRUCTION, format_user_prompt

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """Base exception for all AI client failures."""
    def __init__(self, message: str, code: str = "provider_error"):
        super().__init__(message)
        self.message = message
        self.code = code


class AIProviderUnavailableError(AIClientError):
    """Raised when the AI provider cannot be reached or is temporarily offline."""
    def __init__(self, message: str = "AI xizmati hozircha javob bermayapti."):
        super().__init__(message, code="provider_unavailable")


class AIProviderTimeoutError(AIClientError):
    """Raised when the AI provider takes longer than the configured timeout to respond."""
    def __init__(self, message: str = "AI xizmatidan javob kutish vaqti tugadi."):
        super().__init__(message, code="provider_timeout")


class AIProviderResponseError(AIClientError):
    """Raised when the AI provider returns an error payload or malformed response."""
    def __init__(self, message: str = "AI xizmatida xatolik yuz berdi."):
        super().__init__(message, code="provider_error")


class AIClient:
    """Client for communicating with the external AI provider."""

    def __init__(
        self,
        provider_type: Optional[str] = None,
        base_url: Optional[str] = None,
        keyword: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        raw_type = provider_type or getattr(settings, 'AI_PROVIDER_TYPE', 'groq')
        self.provider_type = raw_type.lower().strip()

        self.base_url = (
            base_url
            or getattr(settings, 'AI_PROVIDER_URL', 'https://api.groq.com/openai/v1')
        ).rstrip('/')

        self.keyword = (
            keyword
            or getattr(settings, 'AI_PROVIDER_KEYWORD', 'text')
        )

        env_groq_key = os.getenv('GROQ_API_KEY', '')
        self.api_key = (
            api_key
            if api_key is not None
            else getattr(settings, 'AI_PROVIDER_API_KEY', '') or env_groq_key
        )

        self.model = (
            model
            or getattr(settings, 'AI_PROVIDER_MODEL', 'openai/gpt-oss-20b')
        )

        self.timeout = (
            timeout
            if timeout is not None
            else getattr(settings, 'AI_PROVIDER_TIMEOUT', 60)
        )

    def ask(self, question: str) -> str:
        """Send question to the configured AI provider and return the answer string."""
        cleaned_question = format_user_prompt(question)

        if self.provider_type == 'groq':
            return self._call_groq(cleaned_question)
        elif self.provider_type == 'openai_compatible':
            return self._call_openai_compatible(cleaned_question)
        return self._call_freegpt4(cleaned_question)

    def _call_groq(self, question: str) -> str:
        """Call Groq Cloud API directly using groq SDK or fallback."""
        api_key = self.api_key or os.getenv('GROQ_API_KEY', '')
        if not api_key:
            raise AIProviderResponseError(
                "Groq API kaliti topilmadi. Iltimos, .env faylida AI_PROVIDER_API_KEY yoki GROQ_API_KEY ni kiriting."
            )

        try:
            from groq import Groq, APIConnectionError, RateLimitError, APITimeoutError, AuthenticationError
        except ImportError:
            # Fallback to OpenAI-compatible HTTP call if groq library is missing
            return self._call_openai_compatible(question)

        try:
            logger.info("Calling Groq API with model %s", self.model)
            client = Groq(api_key=api_key, timeout=float(self.timeout))

            # Configure parameters matching Groq documentation
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": DEFAULT_SYSTEM_INSTRUCTION},
                    {"role": "user", "content": question},
                ],
                temperature=1.0,
                max_completion_tokens=2048,
                top_p=1.0,
            )

            choice = completion.choices[0]
            answer = (choice.message.content or "").strip()

            # Handle reasoning output if model returned reasoning
            if not answer and hasattr(choice.message, 'reasoning') and choice.message.reasoning:
                answer = str(choice.message.reasoning).strip()

            if not answer:
                raise AIProviderResponseError("AI xizmatidan bo‘sh javob qaytdi.")

            return answer

        except APITimeoutError as exc:
            logger.warning("Groq timeout: %s", exc)
            raise AIProviderTimeoutError() from exc
        except APIConnectionError as exc:
            logger.warning("Groq connection error: %s", exc)
            raise AIProviderUnavailableError() from exc
        except AuthenticationError as exc:
            logger.warning("Groq authentication error: %s", exc)
            raise AIProviderResponseError("Groq autentifikatsiya xatosi: API kalit noto‘g‘ri.") from exc
        except RateLimitError as exc:
            logger.warning("Groq rate limit exceeded: %s", exc)
            raise AIProviderUnavailableError("Groq so‘rovlar chegarasi to‘ldi. Birozdan so‘ng urinib ko‘ring.") from exc
        except AIClientError:
            raise
        except Exception as exc:
            logger.error("Groq unexpected error: %s", exc)
            raise AIProviderResponseError(f"Groq xizmatida xatolik yuz berdi: {exc}") from exc

    def _call_freegpt4(self, question: str) -> str:
        """Call Free-GPT4-WEB-API server via GET {base_url}/?{keyword}={question}."""
        target_url = self.base_url or 'http://127.0.0.1:5500'
        if not target_url.endswith('/'):
            target_url += '/'

        params = {self.keyword: question}
        if self.api_key:
            params['token'] = self.api_key

        try:
            logger.info("Calling FreeGPT4 provider at %s", target_url)
            response = requests.get(
                target_url,
                params=params,
                timeout=(5.0, float(self.timeout)),
                headers={'User-Agent': 'CoreAPI/1.0'}
            )
        except requests.exceptions.Timeout as exc:
            logger.warning("FreeGPT4 provider timed out: %s", exc)
            raise AIProviderTimeoutError() from exc
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as exc:
            logger.warning("FreeGPT4 provider connection error: %s", exc)
            raise AIProviderUnavailableError() from exc

        if response.status_code in (502, 503, 504):
            logger.warning("FreeGPT4 provider returned HTTP %s", response.status_code)
            raise AIProviderUnavailableError()
        elif response.status_code >= 400:
            logger.warning("FreeGPT4 provider returned client error HTTP %s", response.status_code)
            raise AIProviderResponseError(f"AI xizmati xatolik qaytardi (HTTP {response.status_code}).")

        raw_text = response.text.strip()

        if "<p id='response'>" in raw_text or '<p id="response">' in raw_text:
            clean_error = re.sub(r'<[^>]+>', '', raw_text).strip()
            if clean_error.lower().startswith('error:') or 'internal server error' in clean_error.lower():
                logger.warning("FreeGPT4 provider returned HTML error: %s", clean_error)
                raise AIProviderResponseError("AI provayderida ichki xatolik yuz berdi.")
            raw_text = clean_error

        if not raw_text:
            raise AIProviderResponseError("AI xizmatidan bo'sh javob qaytdi.")

        return raw_text

    def _call_openai_compatible(self, question: str) -> str:
        """Call standard OpenAI-compatible chat completions endpoint."""
        target_url = self.base_url
        if not target_url.endswith('/chat/completions'):
            if not target_url.endswith('/v1'):
                target_url = f"{target_url}/v1/chat/completions"
            else:
                target_url = f"{target_url}/chat/completions"

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'CoreAPI/1.0',
        }
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': DEFAULT_SYSTEM_INSTRUCTION},
                {'role': 'user', 'content': question},
            ],
            'temperature': 0.7,
        }

        try:
            logger.info("Calling OpenAI-compatible provider at %s", target_url)
            response = requests.post(
                target_url,
                json=payload,
                headers=headers,
                timeout=(5.0, float(self.timeout))
            )
        except requests.exceptions.Timeout as exc:
            logger.warning("OpenAI-compatible provider timed out: %s", exc)
            raise AIProviderTimeoutError() from exc
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as exc:
            logger.warning("OpenAI-compatible provider connection error: %s", exc)
            raise AIProviderUnavailableError() from exc

        if response.status_code in (502, 503, 504):
            raise AIProviderUnavailableError()
        elif response.status_code >= 400:
            raise AIProviderResponseError(f"AI xizmati xatolik qaytardi (HTTP {response.status_code}).")

        try:
            data = response.json()
            answer = data['choices'][0]['message']['content'].strip()
            if not answer:
                raise AIProviderResponseError("AI xizmatidan bo'sh javob qaytdi.")
            return answer
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            logger.warning("Failed to parse OpenAI-compatible response: %s", exc)
            raise AIProviderResponseError("AI xizmati javobini o'qib bo'lmadi.") from exc


def ask_ai(question: str) -> str:
    """Convenience helper to send question to AI provider using default client configuration."""
    client = AIClient()
    return client.ask(question)
