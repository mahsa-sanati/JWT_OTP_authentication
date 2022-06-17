python manage.py makemigrations authentication --noinput
python manage.py migrate
python manage.py collectstatic --no-input --clear

exec "$@"
