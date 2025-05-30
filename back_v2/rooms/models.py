import uuid
from django.db import models
from authenticator.models import CustomUser
from django.utils import timezone
from datetime import timedelta

class GameMode(models.TextChoices):
    DEATHMATCH = "DM", "Deathmatch"
    TEAM_BATTLE = "TB", "Team Battle"

class GameMap(models.Model):
    name = models.CharField(max_length=100, unique=True)
    width = models.IntegerField(default=800)  # Ширина карты (пиксели или клетки)
    height = models.IntegerField(default=600)  # Высота карты
    obstacles = models.TextField()  # Список препятствий

    def __str__(self):
        return self.name

class Room(models.Model):
    creator = models.ForeignKey(CustomUser, related_name='created_rooms', on_delete=models.CASCADE)
    mode = models.CharField(max_length=2, choices=GameMode, default=GameMode.DEATHMATCH)
    map_name = models.ForeignKey(GameMap, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    max_players = models.IntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    battle_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    players = models.ManyToManyField(CustomUser, related_name='joined_rooms', blank=True)

    def save(self, *args, **kwargs):
        if not self.end_time:
            self.end_time = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Room {self.id} ({self.mode}) created by {self.creator.username}"