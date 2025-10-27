#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate --no-input

# Create superuser if needed (optional)
# python manage.py shell -c "from students.models import User; User.objects.create_superuser('admin', 'admin@edukids.com', 'admin123')"

