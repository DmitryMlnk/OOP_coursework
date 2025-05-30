from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.logout_url = reverse('logout')
        self.me_url = reverse('get_current_user')
        self.user_data = {
            "username": "testuser",
            "nickname": "TestUser123",
            "email": "testuser@example.com",
            "password": "TestPassword123"
        }

    def test_register_user(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_register_user_invalid_email(self):
        data = self.user_data.copy()
        data["email"] = "invalid-email"
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["error"])

    def test_register_user_invalid_nickname(self):
        data = self.user_data.copy()
        data["nickname"] = "Invalid Nick!"
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nickname", response.data["error"])

    def test_login_user(self):
        self.client.post(self.register_url, self.user_data)
        response = self.client.post(self.login_url, {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.access_token = response.data["access"]
        self.refresh_token = response.data["refresh"]

    def test_get_current_user(self):
        self.test_login_user()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user_data["username"])

    def test_logout_user(self):
        self.test_login_user()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post(self.logout_url, {"refresh": self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Logged out")

    def test_logout_with_invalid_refresh_token(self):
        self.test_login_user()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post(self.logout_url, {"refresh": "badtoken"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_with_invalid_access_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken')
        response = self.client.post(self.logout_url, {"refresh": "doesnt_matter"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
