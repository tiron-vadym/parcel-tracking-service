#!/bin/sh
python manage.py migrate --noinput || exit 1
python manage.py ensure_initial_user || exit 1
exec python manage.py runserver 0.0.0.0:8000
