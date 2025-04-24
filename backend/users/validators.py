from django.core.validators import RegexValidator
from rest_framework import serializers

username_validator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='Username может содержать только буквы, цифры и символы . @ + -',
)


def validate_username(value):
    """Проверяет, что username соответствует ограничениям."""
    if value.lower() == 'me':
        raise serializers.ValidationError(
            'Использовать "me" в качестве username запрещено.'
        )
    return value
