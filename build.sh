#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Ensure database directory exists
mkdir -p /tmp

# Run migrations to create database
python manage.py migrate

python manage.py collectstatic --no-input
