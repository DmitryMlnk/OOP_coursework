from django.db import transaction
from rest_framework import serializers
from .models import Room
from authenticator.serializers import UserSerializer
from rooms.models import GameMap

class RoomSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    map_name = serializers.SlugRelatedField(slug_field='name', queryset=GameMap.objects.all())
    current_players = UserSerializer(many=True, read_only=True)
    current_player_count = serializers.IntegerField(source='players.count', read_only=True)

    class Meta:
        model = Room
        fields = (
            'id', 'battle_id', 'creator', 'map_name', 'mode', 'max_players',
            'current_player_count', 'current_players', 'is_active', 'created_at', 'end_time'
        )
        read_only_fields = ('id', 'battle_id', 'creator', 'current_players', 'is_active', 'created_at', 'end_time')

class RoomCreateSerializer(serializers.ModelSerializer):
    map_name = serializers.SlugRelatedField(slug_field='name', queryset=GameMap.objects.all())

    class Meta:
        model = Room
        fields = ('map_name', 'max_players', 'mode')

    def create(self, validated_data):
        user = self.context['request'].user
        with transaction.atomic():
            room = Room.objects.create(
                creator=user,
                map_name=validated_data['map_name'],
                max_players=validated_data['max_players'],
                mode=validated_data['mode']
            )
            room.players.add(user)
        return room

class RoomJoinSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()