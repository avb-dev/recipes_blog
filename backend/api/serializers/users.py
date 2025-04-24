import base64
import imghdr
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import Recipe
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """
    Класс сериализации изображения в base64
    """

    def to_internal_value(self, data):
        if isinstance(data, str):
            if 'data:' in data and ';base64,' in data:
                _, data = data.split(';base64,')
            try:
                decoded_file = base64.b64decode(data)
            except (TypeError, ValueError):
                self.fail('invalid_image')

            file_name = str(uuid.uuid4())[:12]
            file_ext = imghdr.what(None, decoded_file)
            if file_ext not in ['jpeg', 'jpg', 'png']:
                self.fail('invalid_image')
            complete_file_name = f"{file_name}.{file_ext}"
            return ContentFile(decoded_file, name=complete_file_name)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    """
    Класс сериализации пользователя
    """
    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'is_subscribed': {'read_only': True},
            'avatar': {'required': False, 'allow_null': True}
        }

    def get_is_subscribed(self, obj):
        """
        Определяет, подписан ли текущий пользователь на автора.
        """
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.follower.filter(author=obj).exists()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        force_full = self.context.get('force_full', False)

        if not force_full:
            request = self.context['request']
            if request.method == 'POST':
                representation.pop('is_subscribed', None)
                representation.pop('avatar', None)
            if request.method == 'PUT':
                return {'avatar': representation.pop('avatar', None)}

        return representation

    def validate(self, attrs):
        request = self.context['request']

        if request.method == 'POST':
            try:
                validate_password(attrs.get('password'))
            except ValidationError as e:
                raise ValidationError({'password': e.detail})

        if request.method == 'PUT' and 'avatar' not in request.data:
            raise ValidationError(
                {'avatar': 'Обязательное поле'})

        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля."""
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        user = self.context['request'].user
        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')

        if not user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")

        if current_password == new_password:
            raise ValidationError(
                "New password must be different from the current password.")

        return attrs

    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()


class RecipeSubscriptionSerializer(serializers.ModelSerializer):
    """
    Класс сериализации рецепта для подписки
    """

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Класс сериализации подписки
    """
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source='author.avatar', read_only=True)

    class Meta:
        model = Subscription
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def validate(self, attrs):
        user = self.context['request'].user
        author = self.context['author']
        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя')
        if user.follower.filter(author=author).exists():
            raise ValidationError(f'Вы уже подписаны на {author}')
        return attrs

    def get_is_subscribed(self, obj):
        return obj.user.follower.filter(author=obj.author).exists()

    def get_recipes(self, obj):
        request = self.context['request']
        limit = request.query_params.get('recipes_limit')

        recipes = obj.author.recipes.all()
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]

        return RecipeSubscriptionSerializer(recipes,
                                            many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.all().count()
