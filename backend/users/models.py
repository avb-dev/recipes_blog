from django.contrib.auth.models import AbstractUser, UnicodeUsernameValidator
from django.db import models

from .constants import FOR_CHARS_EMAIL, FOR_CHARS_USER, ROLE_LENGTH
from .validators import validate_username


class User(AbstractUser):
    """Модель пользователя Foodgram."""

    USER = 'user'
    ADMIN = 'admin'
    ROLE = (
        (USER, 'Пользователь'),
        (ADMIN, 'Администратор'),
    )

    email = models.EmailField(
        max_length=FOR_CHARS_EMAIL,
        unique=True,
        verbose_name='Электронная почта',
    )
    role = models.CharField(
        max_length=ROLE_LENGTH,
        choices=ROLE,
        default=USER,
        verbose_name='Роль пользователя',
    )
    username = models.CharField(
        max_length=FOR_CHARS_USER,
        unique=True,
        validators=[UnicodeUsernameValidator(), validate_username],
        verbose_name='Имя пользователя',
    )
    first_name = models.CharField(
        max_length=FOR_CHARS_USER,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=FOR_CHARS_USER,
        verbose_name='Фамилия',
    )
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        blank=True,
        verbose_name='Аватар',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-date_joined',)

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки на автора."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscription'),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='no_self_subscription',
            ),
        ]
        ordering = ('-author',)

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
