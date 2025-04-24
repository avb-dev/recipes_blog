from django.contrib import admin
from django.db.models import Count

from .models import Ingredient, Recipe, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    search_fields = ('name', 'author')
    list_filter = ('tags',)
    empty_value_display = '-пусто-'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(fav_count=Count("favorite"))

    def favorites_count(self, obj):
        return obj.fav_count

    favorites_count.short_description = "В избранном (раз)"
