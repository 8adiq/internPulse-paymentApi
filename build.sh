#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create database directory if it doesn't exist
mkdir -p db

python manage.py collectstatic --no-input
python manage.py migrate
