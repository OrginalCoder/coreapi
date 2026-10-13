import logging
from django.shortcuts import render
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ParseError, UnsupportedMediaType, Throttled
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from ai_service import (
    ask_ai,
    AIProviderUnavailableError,
    AIProviderTimeoutError,
    AIProviderResponseError,
    AIClientError,
)
from .throttling import ChatRateThrottle
from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatErrorResponseSerializer,
)

logger = logging.getLogger(__name__)

def index_view(request):
    context = {
        'current_year': timezone.now().year,
    }
    return render(request, 'index.html', context)

def docs_view(request):
    context = {
        'current_year': timezone.now().year,
    }
    return render(request, 'docs.html', context)

def custom_404_view(request, exception=None):
    context = {
        'current_year': timezone.now().year,
    }
    return render(request, '404.html', context, status=404)

class ChatAPIView(APIView):
    serializer_class = ChatRequestSerializer
    throttle_classes = [ChatRateThrottle]
    http_method_names = ['post']

    def handle_exception(self, exc):
        if isinstance(exc, Throttled):
            wait_seconds = int(exc.wait) if exc.wait else 60
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": f"Juda ko‘p so‘rov yuborildi. Iltimos, {wait_seconds} soniyadan so‘ng qayta urinib ko‘ring."
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        return super().handle_exception(exc)

    @extend_schema(
        summary="AI modeliga savol yuborish",
        description=(
            "Ushbu endpoint orqali AI modeliga savol yuboriladi va "
            "JSON formatida javob olinadi. Autentifikatsiya talab qilinmaydi."
        ),
        request=ChatRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=ChatResponseSerializer,
                description="Muvaffaqiyatli AI javobi",
                examples=[
                    OpenApiExample(
                        "Muvaffaqiyatli javob namunasi",
                        value={
                            "success": True,
                            "answer": "Python — umumiy maqsadli, o‘qilishi oson dasturlash tili."
                        },
                        response_only=True,
                        status_codes=["200"],
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ChatErrorResponseSerializer,
                description="Noto‘g‘ri so‘rov yoki yetishmayotgan parametrlar",
                examples=[
                    OpenApiExample(
                        "Savol kiritilmagan",
                        value={
                            "success": False,
                            "error": {
                                "code": "missing_question",
                                "message": "Savol maydoni kiritilishi kerak."
                            }
                        },
                        response_only=True,
                        status_codes=["400"],
                    ),
                    OpenApiExample(
                        "So‘rov formati noto‘g‘ri",
                        value={
                            "success": False,
                            "error": {
                                "code": "invalid_request",
                                "message": "So‘rov formati noto‘g‘ri."
                            }
                        },
                        response_only=True,
                        status_codes=["400"],
                    ),
                    OpenApiExample(
                        "So‘rov hajmi me’yordan katta",
                        value={
                            "success": False,
                            "error": {
                                "code": "payload_too_large",
                                "message": "So‘rov hajmi 256 KB dan oshmasligi kerak."
                            }
                        },
                        response_only=True,
                        status_codes=["400"],
                    ),
                ]
            ),
            429: OpenApiResponse(
                response=ChatErrorResponseSerializer,
                description="Juda ko‘p so‘rov yuborildi (Rate Limit oshib ketdi)",
                examples=[
                    OpenApiExample(
                        "Rate limit oshib ketdi",
                        value={
                            "success": False,
                            "error": {
                                "code": "rate_limit_exceeded",
                                "message": "Juda ko‘p so‘rov yuborildi. Iltimos, 30 soniyadan so‘ng qayta urinib ko‘ring."
                            }
                        },
                        response_only=True,
                        status_codes=["429"],
                    )
                ]
            ),
            503: OpenApiResponse(
                response=ChatErrorResponseSerializer,
                description="Tashqi AI provayderi vaqtincha mavjud emas",
                examples=[
                    OpenApiExample(
                        "Provayder mavjud emas",
                        value={
                            "success": False,
                            "error": {
                                "code": "provider_unavailable",
                                "message": "AI xizmati hozircha javob bermayapti."
                            }
                        },
                        response_only=True,
                        status_codes=["503"],
                    )
                ]
            ),
            504: OpenApiResponse(
                response=ChatErrorResponseSerializer,
                description="AI provayderi javob berish vaqti tugadi (Timeout)",
                examples=[
                    OpenApiExample(
                        "Provayder vaqti tugadi",
                        value={
                            "success": False,
                            "error": {
                                "code": "provider_timeout",
                                "message": "AI xizmatidan javob kutish vaqti tugadi."
                            }
                        },
                        response_only=True,
                        status_codes=["504"],
                    )
                ]
            ),
        },
        tags=["Chat"],
    )
    def post(self, request, *args, **kwargs):
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                if int(content_length) > 262144:
                    return Response(
                        {
                            "success": False,
                            "error": {
                                "code": "payload_too_large",
                                "message": "So‘rov hajmi 256 KB dan oshmasligi kerak."
                            }
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                pass

        try:
            if not request.content_type or 'application/json' not in request.content_type.lower():
                return Response(
                    {
                        "success": False,
                        "error": {
                            "code": "invalid_request",
                            "message": "Content-Type application/json bo‘lishi kerak."
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = request.data
        except (ParseError, UnsupportedMediaType) as exc:
            logger.warning("Malformed JSON request received: %s", exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "invalid_request",
                        "message": "So‘rov formati noto‘g‘ri."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as exc:
            logger.warning("Failed parsing incoming request: %s", exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "invalid_request",
                        "message": "So‘rov formati noto‘g‘ri."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(data, dict):
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "invalid_request",
                        "message": "So‘rov formati noto‘g‘ri."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if 'question' not in data:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "missing_question",
                        "message": "Savol maydoni kiritilishi kerak."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.serializer_class(data=data)
        if not serializer.is_valid():
            q_errors = serializer.errors.get('question', [])
            error_code = "invalid_request"
            error_message = "So‘rov formati noto‘g‘ri."

            if q_errors:
                first_err = q_errors[0]
                code = getattr(first_err, 'code', '')
                if code in ('required', 'blank', 'missing_question'):
                    error_code = "missing_question"
                    error_message = "Savol maydoni kiritilishi kerak."
                elif code == 'max_length':
                    error_code = "question_too_long"
                    error_message = "Savol uzunligi 4,000 belgidan oshmasligi kerak."
                else:
                    error_code = "invalid_request"
                    error_message = str(first_err)

            return Response(
                {
                    "success": False,
                    "error": {
                        "code": error_code,
                        "message": error_message
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        question = serializer.validated_data['question']

        try:
            answer = ask_ai(question)
            return Response(
                {
                    "success": True,
                    "answer": answer
                },
                status=status.HTTP_200_OK
            )
        except AIProviderTimeoutError as exc:
            logger.warning("AI provider timeout: %s", exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "provider_timeout",
                        "message": "AI xizmatidan javob kutish vaqti tugadi."
                    }
                },
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except AIProviderUnavailableError as exc:
            logger.warning("AI provider unavailable: %s", exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "provider_unavailable",
                        "message": "AI xizmati hozircha javob bermayapti."
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except AIProviderResponseError as exc:
            logger.warning("AI provider response error: %s", exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "provider_error",
                        "message": "AI xizmatida xatolik yuz berdi."
                    }
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        except AIClientError as exc:
            logger.warning("AI client error: %s", exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": exc.code or "provider_error",
                        "message": "AI xizmatida xatolik yuz berdi."
                    }
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as exc:
            logger.error("Unexpected error in ChatAPIView: %s", exc, exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "server_error",
                        "message": "Kutilmagan server xatoligi yuz berdi."
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
