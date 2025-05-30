from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    nickname = models.CharField(max_length=50, unique=True)
    score = models.IntegerField(default=0)

    def __str__(self):
        return self.nickname