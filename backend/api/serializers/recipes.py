from rest_framework import serializers

from api.constants import MAX_VALUE, MIN_VALUE
from api.serializers.users import Base64ImageField, UserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag.
    """

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Ingredient.
    """

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели RecipeIngredient (только для чтения).
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения рецептов.
    """
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients',
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'image',
            'name',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        """
        Определяет, является ли рецепт избранным для текущего пользователя.
        """
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.favorite.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Определяет, находится ли рецепт в списке покупок текущего пользователя.
        """
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели RecipeIngredient (для записи).
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_VALUE, max_value=MAX_VALUE)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецептов.
    """
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один ингредиент.'
            )

        ingredients_ids = set()
        for item in ingredients:
            if item['id'].id in ingredients_ids:
                raise serializers.ValidationError(
                    'Ингредиенты должны быть уникальными.'
                )
            ingredients_ids.add(item['id'].id)

        return ingredients

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0.'
            )

        tags_ids = set()
        for tag in tags:
            if tag in tags_ids:
                raise serializers.ValidationError(
                    'Теги должны быть уникальными.'
                )
            tags_ids.add(tag)
        return value

    def validate(self, attrs):
        update_required_fields = {
            'ingredients',
            'tags',
            'name',
            'text',
            'cooking_time',
        }
        missing_fields = [field for field in update_required_fields if
                          field not in attrs]
        if missing_fields:
            raise serializers.ValidationError({
                field: 'Это поле обязательно.' for field in missing_fields
            })

        return super().validate(attrs)

    @staticmethod
    def create_ingredients(ingredients_data, recipe):
        """
        Создание ингредиентов для рецепта.
        """
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        user = self.context['request'].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(ingredients_data, instance)

        return instance

    def to_representation(self, instance):
        """
        Представление данных рецепта.
        """
        return RecipeReadSerializer(
            instance,
            context={**self.context, 'force_full': True}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка покупок.
    """
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def validate(self, attrs):
        """
        Валидация данных списка покупок.
        """
        recipe = self.context['recipe']
        user = self.context['request'].user
        if user.shopping_cart.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже есть в списке покупок')
        return attrs


class FavoriteSerializer(ShoppingCartSerializer):
    """
    Сериализатор для избранных рецептов.
    """

    class Meta:
        model = Favorite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def validate(self, attrs):
        """
        Валидация данных избранных рецептов.
        """
        recipe = self.context['recipe']
        user = self.context['request'].user
        if user.favorite.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже есть в избранном')
        return attrs
