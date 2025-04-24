from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy
from shortener.models import UrlMap, UrlProfile

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
    )
    list_filter = ('username', 'email',)
    list_editable = ('role',)
    search_fields = ('username', 'email',)
    list_display_links = ('id', 'username',)
    empty_value_display = '-пусто-'


# Скрываем ненужные модели
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
admin.site.unregister(UrlMap)
admin.site.unregister(UrlProfile)
