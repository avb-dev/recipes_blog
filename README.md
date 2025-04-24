# RecipesBlog

Онлайн-сервис для публикации рецептов с REST API. Основные
возможности:

- Создание рецептов с ингредиентами и тегами
- Добавление рецептов в избранное
- Формирование списка покупок (с возможностью экспорта в TXT)
- Подписка на авторов рецептов

## Развёртывание на сервере

### 1. Подготовка сервера

Установите Docker и Docker Compose:

```bash
sudo apt update && sudo apt install -y curl nano
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

### 3. Настройка инфраструктуры

Скопируйте конфигурационные файлы из папки `infra` на сервер:

```bash
scp infra/docker-compose.prod.yml infra/env.example <username>@<server-ip>:/home/<username>/
```

### 4. Заполните .env

```bash
sudo cp env.example .env
sudo nano .env
``` 

### 5. Переменные окружения

| Variable Name     | Description                     | Default Value                   |
|-------------------|---------------------------------|---------------------------------|
| SECRET_KEY        | Секретный ключ Django           | django-insecure-development-key |
| DEBUG             | Режим отладки                   | False                           |
| ALLOWED_HOSTS     | Разрешенные хосты               | [*]                             |
| DB_ENGINE         | Тип базы данных                 | django.db.backends.sqlite3      |
| DB_NAME           | Имя базы данных                 | foodgram_db                     |
| DB_HOST           | Хост базы данных                | localhost                       |
| DB_PORT           | Порт базы данных                | 5432                            |
| POSTGRES_DB       | Имя базы данных                 | foodgram_db                     |
| POSTGRES_USER     | Логин пользователя базы данных  | postgres                        |
| POSTGRES_PASSWORD | Пароль пользователя базы данных | postgres                        |

### 6. Запуск контейнеров

```bash
sudo docker compose -f docker-compose.prod.yml up -d
```

### 7. Настройка Secrets в GitHub

Добавьте в Secrets репозитория (Settings → Secrets → Actions):

| Secret Name     | Description          |
|-----------------|----------------------|
| DOCKER_USERNAME | Логин Docker Hub     |
| DOCKER_PASSWORD | Пароль Docker Hub    |
| HOST            | IP сервера           |
| USER            | SSH-пользователь     |
| SSH_KEY         | Приватный SSH-ключ   |
| SSH_PASSPHRASE  | Пароль для SSH-ключа |
| TELEGRAM_TOKEN  | Токен бота Telegram  |
| TELEGRAM_TO     | ID пользователя      |

### 8. Создание админа

```bash
sudo docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

---

## Автоматизация (GitHub Actions)

При пуше в ветку `main` автоматически:

1. Проверка кода (flake8)
2. Сборка Docker-образов
3. Пуш образов в Docker Hub
4. Деплой на сервер
5. Уведомление в Telegram

---

## Локальная разработка

1. Клонируйте репозиторий:

```bash
git clone git@github.com:avb-dev/Foodgram.git
```

2. Настройте окружение:

```bash
cp infra/env.example .env
```

3. Запустите контейнеры:

```bash
docker compose up -d
```

После запуска:

- Сайт: http://localhost:8000
- Документация API: http://localhost:8000/api/docs/

---