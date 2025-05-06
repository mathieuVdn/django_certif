from django.urls import path
from .consumers import ImportProgressConsumer

websocket_urlpatterns = [
    path("ws/import_progress/", ImportProgressConsumer.as_asgi()),
]