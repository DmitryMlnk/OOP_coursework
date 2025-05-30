from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/battle/(?P<battle_id>[0-9a-f-]+)/$', consumers.BattleConsumer.as_asgi()),
]