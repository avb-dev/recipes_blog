from django.db.models import Sum
from django.http import HttpResponse

from recipes.models import RecipeIngredient


def generate_shopping_cart_txt(user):
    """
    Генерирует текстовый файл со списком покупок.
    """
    content = f"Список покупок для: {user.username}\n\n"

    ingredients = (
        RecipeIngredient.objects
        .filter(recipe__shopping_cart__user=user)
        .values("ingredient__name", "ingredient__measurement_unit")
        .annotate(total=Sum("amount"))
        .order_by("ingredient__name")
    )

    if not ingredients:
        content += "Корзина пуста.\n"
    else:
        for item in ingredients:
            name = item["ingredient__name"]
            unit = item["ingredient__measurement_unit"]
            total = item["total"]
            content += f"{name} ({unit}) — {total}\n"
    response = HttpResponse(content, content_type="text/plain")
    response[
        "Content-Disposition"
    ] = f"attachment; filename={user.username}_shopping_cart.txt"

    return response
