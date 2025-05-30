import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back_v2.settings')

django_asgi_app = get_asgi_application()

def get_websocket_routes():
    from game.routing import websocket_urlpatterns as game_patterns
    return game_patterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(get_websocket_routes())
    ),
})