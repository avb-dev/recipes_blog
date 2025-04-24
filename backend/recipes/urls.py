from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views.recipes import IngredientViewSet, RecipeViewSet, TagViewSet

recipes_router = DefaultRouter()
recipes_router.register('tags', TagViewSet, basename='tags')
recipes_router.register('ingredients', IngredientViewSet,
                        basename='ingredients')
recipes_router.register('recipes', RecipeViewSet, basename='recipes')

app_name = 'recipes'

urlpatterns = [
    path('', include(recipes_router.urls)),
]
