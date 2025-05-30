from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Room
from .serializers import RoomSerializer, RoomCreateSerializer, RoomJoinSerializer

class RoomList(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Получить список активных комнат",
        operation_description="Возвращает список всех активных игровых комнат. Комнаты, время жизни которых истекло, автоматически деактивируются.",
        responses={200: RoomSerializer(many=True)}
    )
    def get(self, request):
        now = timezone.now()
        active_rooms = Room.objects.filter(is_active=True)

        # Проверка и деактивация истекших комнат
        expired_rooms = active_rooms.filter(end_time__lt=now)
        if expired_rooms.exists():
            expired_rooms.update(is_active=False)

        # Повторный запрос активных после деактивации
        rooms = Room.objects.filter(is_active=True)
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RoomCreate(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Создать новую комнату",
        operation_description="Создаёт новую игровую комнату. Создатель автоматически добавляется в комнату. Требуется аутентификация.",
        request_body=RoomCreateSerializer,
        responses={
            201: RoomSerializer(),
            400: openapi.Response('Ошибка валидации', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING)
            }))
        }
    )
    def post(self, request):
        serializer = RoomCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            room = serializer.save()
            return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class RoomJoin(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Присоединиться к комнате",
        operation_description="Присоединяет пользователя к комнате по её ID. Возвращает battle_id для WebSocket. Требуется аутентификация.",
        request_body=RoomJoinSerializer,
        responses={
            200: openapi.Response('Успешное присоединение', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'battle_id': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            400: openapi.Response('Ошибка', openapi.Schema(type=openapi.TYPE_OBJECT)),
            404: openapi.Response('Комната не найдена', openapi.Schema(type=openapi.TYPE_OBJECT))
        }
    )
    def post(self, request):
        serializer = RoomJoinSerializer(data=request.data)
        if serializer.is_valid():
            try:
                room = Room.objects.get(id=serializer.validated_data['room_id'], is_active=True)
                room.players.add(request.user)
                return Response({'battle_id': str(room.battle_id)}, status=status.HTTP_200_OK)
            except Room.DoesNotExist:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class RoomLeave(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Покинуть комнату",
        operation_description="Удаляет пользователя из всех активных комнат.",
        responses={200: openapi.Response('Успешно покинута комната')}
    )
    def post(self, request):
        request.user.joined_rooms.remove(*request.user.joined_rooms.filter(is_active=True))
        return Response({'message': 'Left room'}, status=status.HTTP_200_OK)