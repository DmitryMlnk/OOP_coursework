from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from authenticator.models import CustomUser
from rooms.models import Room, GameMap

class RoomTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123',
            nickname='TestNick',
            email='test@example.com'
        )
        self.map = GameMap.objects.create(
            name="TestMap",
            width=800,
            height=600,
            obstacles="########"
        )
        self.room = Room.objects.create(
            creator=self.user,
            map_name=self.map,
            mode="DM",
            max_players=2,
        )
        self.room.players.add(self.user)

        self.room_list_url = reverse('room_list')
        self.room_create_url = reverse('room_create')
        self.room_join_url = reverse('room_join')
        self.room_leave_url = reverse('room_leave')
        self.token_url = reverse('token_obtain_pair')

        # Получение токенов
        response = self.client.post(self.token_url, {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        self.access_token = response.data['access']
        self.auth_header = {'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'}

    def test_list_active_rooms(self):
        response = self.client.get(self.room_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertTrue(any(room['id'] == self.room.id for room in response.data))

    def test_deactivate_expired_rooms(self):
        self.room.end_time = timezone.now() - timedelta(minutes=1)
        self.room.save()
        response = self.client.get(self.room_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertFalse(self.room.is_active)

    def test_create_room_authenticated(self):
        data = {
            "map_name": self.map.name,
            "max_players": 4,
            "mode": "DM"
        }
        response = self.client.post(self.room_create_url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['creator']['username'], self.user.username)

    def test_create_room_unauthenticated(self):
        data = {
            "map_name": self.map.name,
            "max_players": 4,
            "mode": "DM"
        }
        response = self.client.post(self.room_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_join_existing_room(self):
        another_user = CustomUser.objects.create_user(
            username='anotheruser',
            password='anotherpass',
            nickname='AnotherNick',
            email='another@example.com'
        )
        login_response = self.client.post(self.token_url, {
            'username': 'anotheruser',
            'password': 'anotherpass'
        })
        access = login_response.data['access']
        auth = {'HTTP_AUTHORIZATION': f'Bearer {access}'}

        data = {'room_id': self.room.id}
        response = self.client.post(self.room_join_url, data, **auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('battle_id', response.data)

    def test_join_nonexistent_room(self):
        data = {'room_id': 9999}
        response = self.client.post(self.room_join_url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_join_room_invalid_payload(self):
        response = self.client.post(self.room_join_url, {}, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_leave_room(self):
        response = self.client.post(self.room_leave_url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Left room')
        self.assertEqual(self.user.joined_rooms.filter(is_active=True).count(), 0)
