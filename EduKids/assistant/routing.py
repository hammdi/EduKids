from django.urls import path
from . import consumers


websocket_urlpatterns = [
    path('ws/assistant/', consumers.AssistantConsumer.as_asgi()),
    # Optionally add conversation-specific paths
    # path('ws/assistant/<int:conversation_id>/', consumers.AssistantConsumer.as_asgi()),
]
