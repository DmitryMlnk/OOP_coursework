from django.db import models
from authenticator.models import CustomUser
from rooms.models import Room


class Tank(models.Model):
    room = models.ForeignKey(Room, related_name='tanks', on_delete=models.CASCADE)
    player = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    x = models.FloatField(default=0)  # Позиция X на карте
    y = models.FloatField(default=0)  # Позиция Y на карте
    direction = models.CharField(max_length=10, default='up')  # Направление: up, down, left, right
    is_alive = models.BooleanField(default=True)

    def __str__(self):
        return f"Tank of {self.player.nickname} in room {self.room.id}"

class Bullet(models.Model):
    room = models.ForeignKey(Room, related_name='bullets', on_delete=models.CASCADE)
    shooter = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    x = models.FloatField()  # Позиция X
    y = models.FloatField()  # Позиция Y
    direction = models.CharField(max_length=10)  # Направление: up, down, left, right
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bullet in room {self.room.id} by {self.shooter.nickname}"