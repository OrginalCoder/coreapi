"""Automated unit and integration tests for CoreAPI."""

from unittest.mock import patch
import requests
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status

from ai_service.client import (
    AIClient,
    AIProviderUnavailableError,
    AIProviderTimeoutError,
    AIProviderResponseError,
)
from ai_service.prompts import format_user_prompt
from core.throttling import ChatRateThrottle


class WebPagesTests(TestCase):
    """Test suite for public web pages."""

    def setUp(self):
        self.client = Client()

    def test_landing_page_status_200(self):
        """Landing page at '/' should return HTTP 200 and contain brand text in Uzbek."""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bepul AI API")
        self.assertContains(response, "API hujjatlari")
        self.assertContains(response, "POST /api/v1/chat/")

    def test_docs_page_status_200(self):
        """Documentation page at '/docs/' should return HTTP 200 and contain playground elements."""
        response = self.client.get(reverse('docs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Interaktiv API Playground")
        self.assertContains(response, "question-input")
        self.assertContains(response, "btn-submit-playground")

    def test_custom_404_page(self):
        """Requesting a non-existent URL should return HTTP 404 with custom Uzbek template."""
        response = self.client.get('/random-non-existent-url-path/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Sahifa topilmadi", status_code=404)


class SwaggerAndSchemaTests(TestCase):
    """Test suite for OpenAPI schema and Swagger UI."""

    def setUp(self):
        self.client = Client()

    def test_openapi_schema_endpoint(self):
        """OpenAPI schema at '/api/schema/' should return HTTP 200."""
        response = self.client.get(reverse('schema'))
        self.assertEqual(response.status_code, 200)

    def test_swagger_ui_endpoint(self):
        """Swagger UI at '/api/swagger/' should return HTTP 200 and load documentation UI."""
        response = self.client.get(reverse('swagger-ui'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "swagger")


class ChatAPITests(TestCase):
    """Test suite for POST /api/v1/chat/ API endpoint."""

    def setUp(self):
        self.client = Client()
        self.chat_url = reverse('api-chat')

    @patch('core.views.ask_ai')
    def test_successful_question_response(self, mock_ask_ai):
        """Valid question should return HTTP 200 and documented JSON response."""
        mock_ask_ai.return_value = "Python — dinamik dasturlash tili."

        payload = {"question": "Python nima?"}
        response = self.client.post(
            self.chat_url,
            data=payload,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("answer"), "Python — dinamik dasturlash tili.")
        mock_ask_ai.assert_called_once_with("Python nima?")

    def test_missing_question_field(self):
        """Payload without question key should return HTTP 400 with missing_question error."""
        payload = {"other_field": "test"}
        response = self.client.post(
            self.chat_url,
            data=payload,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data["error"]["code"], "missing_question")
        self.assertIn("Savol maydoni kiritilishi kerak.", data["error"]["message"])

    def test_empty_question(self):
        """Empty string question should return HTTP 400 with missing_question error."""
        payload = {"question": ""}
        response = self.client.post(
            self.chat_url,
            data=payload,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data["error"]["code"], "missing_question")

    def test_whitespace_only_question(self):
        """Whitespace-only question should return HTTP 400 with missing_question error."""
        payload = {"question": "     \n\t   "}
        response = self.client.post(
            self.chat_url,
            data=payload,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data["error"]["code"], "missing_question")

    def test_invalid_question_data_type(self):
        """Non-string question (e.g. integer or list) should return HTTP 400 with invalid_request."""
        payload = {"question": 12345}
        response = self.client.post(
            self.chat_url,
            data=payload,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("code", data["error"])

    def test_question_too_long(self):
        """Question exceeding 4,000 characters should return HTTP 400 question_too_long."""
        long_question = "A" * 4005
        payload = {"question": long_question}
        response = self.client.post(
            self.chat_url,
            data=payload,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data["error"]["code"], "question_too_long")

    def test_invalid_content_type(self):
        """Sending raw urlencoded data instead of application/json should return HTTP 400."""
        response = self.client.post(
            self.chat_url,
            data="question=Salom",
            content_type="application/x-www-form-urlencoded"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data["error"]["code"], "invalid_request")

    def test_unsupported_http_methods(self):
        """GET, PUT, DELETE requests to chat endpoint must be rejected with HTTP 405."""
        get_res = self.client.get(self.chat_url)
        self.assertEqual(get_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        put_res = self.client.put(self.chat_url, data={}, content_type="application/json")
        self.assertEqual(put_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        delete_res = self.client.delete(self.chat_url)
        self.assertEqual(delete_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('core.views.ask_ai')
    def test_provider_unavailable_returns_503(self, mock_ask_ai):
        """When AI provider cannot be reached, API must return HTTP 503 provider_unavailable."""
        mock_ask_ai.side_effect = AIProviderUnavailableError()

        response = self.client.post(
            self.chat_url,
            data={"question": "Savol"},
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data["error"]["code"], "provider_unavailable")
        self.assertEqual(data["error"]["message"], "AI xizmati hozircha javob bermayapti.")

    @patch('core.views.ask_ai')
    def test_provider_timeout_returns_504(self, mock_ask_ai):
        """When AI provider times out, API must return HTTP 504 provider_timeout."""
        mock_ask_ai.side_effect = AIProviderTimeoutError()

        response = self.client.post(
            self.chat_url,
            data={"question": "Savol"},
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data["error"]["code"], "provider_timeout")
        self.assertEqual(data["error"]["message"], "AI xizmatidan javob kutish vaqti tugadi.")

    @patch('core.views.ask_ai')
    def test_provider_response_error_returns_502(self, mock_ask_ai):
        """When AI provider returns invalid response, API must return HTTP 502 provider_error."""
        mock_ask_ai.side_effect = AIProviderResponseError()

        response = self.client.post(
            self.chat_url,
            data={"question": "Savol"},
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data["error"]["code"], "provider_error")

    def test_payload_too_large(self):
        """Requests with Content-Length exceeding 256 KB should be rejected with HTTP 400 payload_too_large."""
        response = self.client.post(
            self.chat_url,
            data={"question": "Katta so‘rov"},
            content_type="application/json",
            CONTENT_LENGTH="300000"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data["error"]["code"], "payload_too_large")
        self.assertIn("256 KB", data["error"]["message"])

    @patch('core.views.ask_ai')
    def test_rate_limit_exceeded(self, mock_ask_ai):
        """Exceeding request limit should return HTTP 429 rate_limit_exceeded with wait time in Uzbek."""
        from django.core.cache import cache
        cache.clear()
        mock_ask_ai.return_value = "Test javob"

        with patch.object(ChatRateThrottle, 'get_rate', return_value='2/min'):
            res1 = self.client.post(self.chat_url, data={"question": "Savol 1"}, content_type="application/json")
            self.assertEqual(res1.status_code, status.HTTP_200_OK)

            res2 = self.client.post(self.chat_url, data={"question": "Savol 2"}, content_type="application/json")
            self.assertEqual(res2.status_code, status.HTTP_200_OK)

            res3 = self.client.post(self.chat_url, data={"question": "Savol 3"}, content_type="application/json")
            self.assertEqual(res3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            data3 = res3.json()
            self.assertFalse(data3.get("success"))
            self.assertEqual(data3["error"]["code"], "rate_limit_exceeded")
            self.assertIn("Juda ko‘p so‘rov yuborildi", data3["error"]["message"])
            self.assertIn("qayta urinib ko‘ring", data3["error"]["message"])
        cache.clear()


class PromptSanitizerUnitTests(TestCase):
    """Unit tests for prompt sanitization and adversarial injection protection."""

    def test_clean_standard_prompt(self):
        """Standard question text should remain unchanged."""
        prompt = "Python nima va undan qanday foydalaniladi?"
        self.assertEqual(format_user_prompt(prompt), prompt)

    def test_strip_zero_width_spaces(self):
        """Zero-width spaces used to bypass safety filters must be removed."""
        prompt_with_zw = "Sal\u200Bom\u200C d\u200Dun\uFEFFyo"
        self.assertEqual(format_user_prompt(prompt_with_zw), "Salom dunyo")

    def test_strip_control_characters(self):
        """Control characters like NULL, escape codes must be stripped."""
        prompt_with_ctrl = "Salom\x00 dunyo\x1f\x7f!"
        self.assertEqual(format_user_prompt(prompt_with_ctrl), "Salom dunyo!")

    def test_normalize_line_endings_and_spaces(self):
        """Windows CRLF should normalize to LF and leading/trailing whitespace stripped."""
        prompt_crlf = "  Qator 1\r\nQator 2\r\n  "
        self.assertEqual(format_user_prompt(prompt_crlf), "Qator 1\nQator 2")


class AIClientUnitTests(TestCase):
    """Direct unit tests for ai_service.client.AIClient class."""

    @patch('requests.get')
    def test_freegpt4_successful_call(self, mock_get):
        """AIClient successfully parses plain text from FreeGPT4 server."""
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response._content = b"Bu Python tili haqida javob."
        mock_get.return_value = mock_response

        client = AIClient(provider_type="freegpt4", base_url="http://127.0.0.1:5500")
        answer = client.ask("Python nima?")

        self.assertEqual(answer, "Bu Python tili haqida javob.")
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['text'], "Python nima?")

    @patch('requests.get')
    def test_freegpt4_timeout_raises_custom_exception(self, mock_get):
        """AIClient translates requests.exceptions.Timeout into AIProviderTimeoutError."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        client = AIClient(provider_type="freegpt4", base_url="http://127.0.0.1:5500")
        with self.assertRaises(AIProviderTimeoutError):
            client.ask("Savol")

    @patch('requests.get')
    def test_freegpt4_connection_error_raises_unavailable(self, mock_get):
        """AIClient translates connection failure into AIProviderUnavailableError."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to establish connection")

        client = AIClient(provider_type="freegpt4", base_url="http://127.0.0.1:5500")
        with self.assertRaises(AIProviderUnavailableError):
            client.ask("Savol")

    @patch('requests.get')
    def test_freegpt4_html_error_tag_handled(self, mock_get):
        """AIClient detects FreeGPT4 server HTML error response and raises AIProviderResponseError."""
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response._content = b"<p id='response'>Error: AI API call failed</p>"
        mock_get.return_value = mock_response

        client = AIClient(provider_type="freegpt4", base_url="http://127.0.0.1:5500")
        with self.assertRaises(AIProviderResponseError):
            client.ask("Savol")

    @patch('requests.post')
    def test_openai_compatible_successful_call(self, mock_post):
        """AIClient successfully formats and parses OpenAI-compatible chat completion."""
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response._content = b'{"choices": [{"message": {"content": "Salom, men sun\'iy intellektman."}}]}'
        mock_post.return_value = mock_response

        client = AIClient(
            provider_type="openai_compatible",
            base_url="http://127.0.0.1:1336",
            api_key="test-key"
        )
        answer = client.ask("Salom")

        self.assertEqual(answer, "Salom, men sun'iy intellektman.")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['headers']['Authorization'], "Bearer test-key")

    def test_groq_missing_api_key_raises_error(self):
        """AIClient raises response error when Groq is configured without an API key."""
        client = AIClient(provider_type="groq", api_key="")
        with self.assertRaises(AIProviderResponseError) as ctx:
            client.ask("Salom")
        self.assertIn("Groq API kaliti topilmadi", str(ctx.exception))

    @patch('groq.Groq')
    def test_groq_successful_call(self, mock_groq_class):
        """AIClient successfully calls Groq SDK with requested model."""
        from unittest.mock import MagicMock
        mock_instance = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Salom! Groq orqali javob."
        mock_choice.message.reasoning = None
        mock_completion.choices = [mock_choice]
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_groq_class.return_value = mock_instance

        client = AIClient(
            provider_type="groq",
            api_key="gsk_test123",
            model="openai/gpt-oss-20b"
        )
        answer = client.ask("Salom")

        self.assertEqual(answer, "Salom! Groq orqali javob.")
        mock_instance.chat.completions.create.assert_called_once()
        call_kwargs = mock_instance.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs['model'], "openai/gpt-oss-20b")
