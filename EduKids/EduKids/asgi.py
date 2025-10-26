"""
ASGI config for EduKids project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

# Ensure settings are set before importing Django/application modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduKids.settings')

from django.core.asgi import get_asgi_application

# Initialize Django ASGI application first (this loads app registry)
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import assistant.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            assistant.routing.websocket_urlpatterns
        )
    ),
})
