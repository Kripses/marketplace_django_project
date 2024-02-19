#!/bin/sh
python manage.py migrate
python manage.py collectstatic --noinput

if [ "$load_test_data" = "True" ]; then
  python manage.py loadscript
fi

exec "$@"