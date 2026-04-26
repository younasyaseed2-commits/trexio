#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations (This fixes the 500 error)
python manage.py migrate

# Collect static files (For CSS/Images)
python manage.py collectstatic --no-input