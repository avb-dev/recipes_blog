from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import IsUserOrAdminOrReadOnly
from api.serializers.users import (ChangePasswordSerializer,
                                   SubscriptionSerializer, UserSerializer)
from users.models import Subscription

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователей."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (IsUserOrAdminOrReadOnly,)

    @action(detail=False,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        """Возвращает информацию о текущем пользователе."""
        user = request.user
        serializer = self.get_serializer(user)
        return Response(status=HTTPStatus.OK, data=serializer.data)

    @action(url_path='me/avatar',
            methods=['put', 'delete'],
            detail=False,
            permission_classes=(IsAuthenticated,))
    def me_avatar(self, request):
        """Изменяет или удаляет аватар."""
        user = request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(status=HTTPStatus.OK, data=serializer.data)

        if user.avatar:
            user.avatar.delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(methods=['post'],
            detail=False,
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        """Изменяет пароль."""
        serializer = ChangePasswordSerializer(data=request.data,
                                              context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=(IsAuthenticated,),
            serializer_class=SubscriptionSerializer)
    def subscribe(self, request, *args, **kwargs):
        """Добавляет или удаляет подписку на автора."""
        user = request.user
        author = get_object_or_404(User, id=kwargs.get('pk'))

        if request.method == 'POST':
            serializer = self.get_serializer(
                data=request.data,
                context={'request': request, 'author': author},
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=author, user=user)
                return Response(status=HTTPStatus.CREATED,
                                data=serializer.data)

        if user.follower.filter(author=author).exists():
            Subscription.objects.get(author=author).delete()
            return Response(status=HTTPStatus.NO_CONTENT)

        return Response(status=HTTPStatus.BAD_REQUEST)

    @action(detail=False,
            permission_classes=(IsAuthenticated,),
            serializer_class=SubscriptionSerializer, )
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        subs = request.user.follower.all()
        pages = self.paginate_queryset(subs)
        return self.get_paginated_response(
            self.get_serializer(
                pages,
                many=True,
                context={'request': request}
            ).data)
