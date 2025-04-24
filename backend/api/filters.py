from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """
    Фильтрация рецептов.
    """
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    author = filters.ModelChoiceFilter(queryset=User.objects.all())

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрует рецепты по наличию в избранном у пользователя.
        """
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        if value:
            return queryset.filter(favorite__user=user)
        return queryset.exclude(favorite__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрует рецепты по наличию в корзине у пользователя.
        """
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        if value:
            return queryset.filter(shopping_cart__user=user)
        return queryset.exclude(shopping_cart__user=user)


class IngredientSearchFilter(SearchFilter):
    """
    Поиск ингредиентов.
    """
    search_param = 'name'
