from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'nickname', 'email', 'score')
        extra_kwargs = {
            'id': {'help_text': 'Уникальный идентификатор пользователя'},
            'username': {'help_text': 'Уникальное имя пользователя для входа'},
            'nickname': {'help_text': 'Отображаемое имя игрока в игре'},
            'email': {'help_text': 'Электронная почта пользователя'},
            'score': {'help_text': 'Общий счёт игрока в игре'},
        }

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, help_text='Пароль для нового пользователя')

    class Meta:
        model = User
        fields = ('username', 'nickname', 'email', 'password')
        extra_kwargs = {
            'username': {'help_text': 'Уникальное имя пользователя для входа'},
            'nickname': {'help_text': 'Отображаемое имя игрока в игре'},
            'email': {'help_text': 'Электронная почта пользователя (не <optional>'},
        }

    def validate_nickname(self, value):
        if not value.strip():
            raise serializers.ValidationError("Nickname cannot be empty")
        if not value.isalnum():
            raise serializers.ValidationError("Nickname must contain only alphanumeric characters")
        return value

    def validate_email(self, value):
        if value and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
            raise serializers.ValidationError("Invalid email format")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            nickname=validated_data['nickname'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['user'] = UserSerializer(self.user).data
        return data