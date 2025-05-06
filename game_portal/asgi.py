"""
ASGI config for game_portal project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import gameboxd.routing  # Importe les WebSockets définis dans `routing.py`

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "game_portal.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Django gère les requêtes HTTP classiques
    "websocket": AuthMiddlewareStack(
        URLRouter(
            gameboxd.routing.websocket_urlpatterns  # Routes WebSocket définies
        )
    ),
})
