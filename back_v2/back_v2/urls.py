from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication

schema_view = get_schema_view(
    openapi.Info(
        title="Battle City API",
        default_version='v1',
        description=(
            "API для многопользовательской игры Battle City.\n\n"
            "**REST API**: Эндпоинты для управления комнатами, матчмейкингом, игровыми сессиями, профилями и аутентификацией.\n"
            "**Аутентификация**: Используется JWT. Получите access-токен через /api/authenticator/token/.\n"
            "- **Access-токен**: Используйте в заголовке `Authorization: Bearer <access_token>` для REST API.\n"
            "- **Refresh-токен**: Для обновления access-токена через /api/authenticator/token/refresh/.\n"
            "**WebSocket API**: Подключение к `ws://localhost:8000/ws/game/session/<session_id>/?token=<access_token>`\n"
            "- **Аутентификация**: Передайте JWT access-токен в query-параметре `token`.\n"
            "- **Действия клиента**: `move_up`, `move_down`, `move_left`, `move_right`, `shoot`, `get_stats`\n"
            "- **Сообщения сервера**: `battle_start`, `game_update`, `stats_update`, `game_over`\n"
            "- **Формат**: JSON, например, `{'action': 'move_up'}` для действий, `{'type': 'game_update', 'data': {...}}` для сообщений.\n"
        ),
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@battlecity.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=(JWTAuthentication,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/authenticator/', include('authenticator.urls')),
    path('api/rooms/', include('rooms.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]