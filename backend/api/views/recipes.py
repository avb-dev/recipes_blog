from http import HTTPStatus

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipeFilter
from api.permissions import IsAuthorOrAdminOrReadOnly
from api.serializers.recipes import (FavoriteSerializer, IngredientSerializer,
                                     RecipeReadSerializer,
                                     RecipeWriteSerializer,
                                     ShoppingCartSerializer, TagSerializer)
from api.services import generate_shopping_cart_txt
from recipes.models import Ingredient, Recipe, Tag


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для тегов, только для чтения.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для ингредиентов, только для чтения.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для рецептов.
    """
    queryset = Recipe.objects.all()
    http_method_names = ('get', 'post', 'patch', 'delete',)
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(url_path='get-link', detail=True)
    def get_link(self, request, pk=None):
        """
        Возвращает короткую ссылку на рецепт.
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        return Response(status=HTTPStatus.OK,
                        data={
                            "short-link": recipe.get_short_link(request)
                        })

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """
        Добавляет или удаляет рецепт из корзины покупок.
        """
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'DELETE':
            instance = request.user.shopping_cart.filter(recipe=recipe)
            if not instance:
                return Response(status=HTTPStatus.BAD_REQUEST)
            instance.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

        serializer = ShoppingCartSerializer(
            data=request.data,
            context={'request': request, 'recipe': recipe},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, recipe=recipe)

        return Response(status=HTTPStatus.CREATED, data=serializer.data)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """
        Генерирует и возвращает файл со списком покупок.
        """
        return generate_shopping_cart_txt(request.user)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """
        Добавляет или удаляет рецепт из избранного.
        """
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'DELETE':
            instance = request.user.favorite.filter(recipe=recipe)
            if not instance:
                return Response(status=HTTPStatus.BAD_REQUEST)
            instance.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

        serializer = FavoriteSerializer(
            data=request.data,
            context={'request': request, 'recipe': recipe},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, recipe=recipe)

        return Response(status=HTTPStatus.CREATED, data=serializer.data)
