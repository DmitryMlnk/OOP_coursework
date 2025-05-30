from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer
import logging

logger = logging.getLogger(__name__)

@permission_classes([AllowAny])
class Register(APIView):
    @swagger_auto_schema(
        operation_summary="Зарегистрировать нового пользователя",
        operation_description="Создаёт нового пользователя. Для получения JWT-токенов используйте /api/authenticator/token/.",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('Данные пользователя', UserSerializer()),
            400: openapi.Response('Ошибка валидации', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'error': openapi.Schema(type=openapi.TYPE_OBJECT, description='Ошибки валидации')
            }))
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User {user.username} registered successfully")
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        logger.error(f"Registration failed: {serializer.errors}")
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class Logout(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Выход пользователя",
        operation_description="Добавляет refresh-токен в чёрный список, завершая сессию пользователя. Требуется Bearer-токен.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh-токен для выхода')
            }
        ),
        responses={
            200: openapi.Response('Успешный выход', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Подтверждение выхода')
            })),
            400: openapi.Response('Неверный токен', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING)
            })),
            401: openapi.Response('Неавторизован', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING)
            }))
        },
        security=[{'Bearer': []}]
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User {request.user.username} logged out successfully")
            return Response({'message': 'Logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GetCurrentUser(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Получить текущего пользователя",
        operation_description="Возвращает данные текущего аутентифицированного пользователя. Требуется Bearer-токен.",
        responses={
            200: openapi.Response('Данные пользователя', UserSerializer()),
            401: openapi.Response('Неавторизован', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING)
            }))
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        logger.debug(f"Retrieved data for user {request.user.username}")
        return Response(serializer.data, status=status.HTTP_200_OK)