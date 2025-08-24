#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create database directory if it doesn't exist
mkdir -p db

# Run migrations to create database
python manage.py migrate --run-syncdb

python manage.py collectstatic --no-input
