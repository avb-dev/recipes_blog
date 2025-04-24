#!/bin/sh

python manage.py makemigrations
python manage.py migrate
python manage.py import_csv
python manage.py collectstatic --noinput

cp -r /app/collected_static/. /backend_static/static/

exec gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi