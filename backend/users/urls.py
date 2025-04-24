from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views.users import UserViewSet

users_router = DefaultRouter()
users_router.register('users', UserViewSet, basename='users')

app = 'users'

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(users_router.urls)),
]
