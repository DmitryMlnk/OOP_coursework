import jwt
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user_from_jwt(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        return User.objects.get(id=user_id)
    except (jwt.InvalidTokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]
        scope["user"] = await get_user_from_jwt(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
