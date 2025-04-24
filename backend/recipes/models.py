from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from shortener import shortener

from recipes.constants import (MAX_INGREDIENT_NAME_LENGTH,
                               MAX_MEASUREMENT_UNIT_LENGTH,
                               MAX_RECIPE_NAME_LENGTH, MAX_TAG_NAME_LENGTH,
                               MAX_TAG_SLUG_LENGTH, MAX_VALUE, MIN_VALUE)

User = get_user_model()


class Tag(models.Model):
    """
    Модель тега.
    """
    name = models.CharField(
        max_length=MAX_TAG_NAME_LENGTH,
        verbose_name='Название',
        help_text='Введите название тега',
    )
    slug = models.SlugField(
        max_length=MAX_TAG_SLUG_LENGTH,
        unique=True,
        verbose_name='Слаг',
        help_text='Уникальный идентификатор тега',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """
    Модель ингредиента.
    """
    name = models.CharField(
        max_length=MAX_INGREDIENT_NAME_LENGTH,
        verbose_name='Название',
        db_index=True,
        help_text='Введите название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единица измерения',
        help_text='Например: грамм, мл, штука',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """
    Модель рецепта.
    """
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
        help_text='Выберите теги для рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes',
        help_text='Выберите ингредиенты для рецепта',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение',
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LENGTH,
        db_index=True,
        verbose_name='Название',
        help_text='Введите название рецепта',
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Опишите рецепт',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (мин)',
        validators=[
            MinValueValidator(MIN_VALUE),
            MaxValueValidator(MAX_VALUE),
        ],
        help_text='Укажите время приготовления в минутах',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        default_related_name = 'recipe'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def _get_short_url(self):
        return shortener.create(
            self.author,
            f'/recipes/{self.id}',
        )

    def get_short_link(self, request):
        base_url = request.build_absolute_uri('/').rstrip('/')
        return f'{base_url}/s/{self._get_short_url()}'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Модель ингредиента в рецепте.
    """
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        verbose_name='Название рецепта',
        on_delete=models.CASCADE,
        help_text='Выберите рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Название ингредиента',
        on_delete=models.CASCADE,
        help_text='Выберите ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(MIN_VALUE),
            MaxValueValidator(MAX_VALUE),
        ],
        help_text='Количество ингредиента для рецепта',
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        ordering = ['recipe', 'ingredient']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredients'
            )
        ]

    def __str__(self):
        return (f'{self.ingredient.name} — {self.amount} '
                f'{self.ingredient.measurement_unit}')


class ShoppingCart(models.Model):
    """
    Модель корзины.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
        default_related_name = 'shopping_cart'

    def __str__(self):
        return f'{self.recipe} в корзине {self.user}'


class Favorite(models.Model):
    """
    Модель избранного.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        default_related_name = 'favorite'

    def __str__(self):
        return f'{self.recipe} в избранном {self.user}'
