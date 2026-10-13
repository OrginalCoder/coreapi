from rest_framework import serializers

class ChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        max_length=4000,
        help_text="AI modeliga yuboriladigan savol matni (maksimal 4,000 belgi).",
        error_messages={
            'required': 'Savol maydoni kiritilishi kerak.',
            'blank': 'Savol bo‘sh bo‘lishi mumkin emas.',
            'max_length': 'Savol uzunligi 4,000 belgidan oshmasligi kerak.',
            'invalid': 'Savol matn ko‘rinishida bo‘lishi kerak.',
        }
    )

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'question' in data and not isinstance(data['question'], str):
            raise serializers.ValidationError({
                'question': serializers.ErrorDetail(
                    'Savol matn ko‘rinishida bo‘lishi kerak.',
                    code='invalid'
                )
            })
        return super().to_internal_value(data)

    def validate_question(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError(
                "Savol maydoni kiritilishi kerak.",
                code="missing_question"
            )
        return cleaned

class ChatResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(
        default=True,
        help_text="So‘rov muvaffaqiyatli bajarilganligini bildiruvchi mantiqiy qiymat."
    )
    answer = serializers.CharField(
        help_text="AI modeli tomonidan shakllantirilgan javob matni."
    )

class ErrorDetailSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text="Xatolik kodi (masalan, missing_question, provider_unavailable)."
    )
    message = serializers.CharField(
        help_text="Foydalanuvchi yoki dasturchi uchun tushunarli o‘zbek tilidagi xabar."
    )

class ChatErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(
        default=False,
        help_text="So‘rov muvaffaqiyatsiz bo‘lganligini bildiradi."
    )
    error = ErrorDetailSerializer(
        help_text="Xatolik tafsilotlari."
    )
