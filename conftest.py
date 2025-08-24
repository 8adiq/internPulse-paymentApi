import os
import django
from django.conf import settings

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_api.settings')

# Configure Django
django.setup()
