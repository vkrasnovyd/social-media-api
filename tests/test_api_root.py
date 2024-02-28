from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

API_ROOT_URL = reverse("root")


class UnauthenticatedApiRootTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_api_root_auth_required(self):
        res = self.client.get(API_ROOT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedShowThemeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_api_root(self):
        res = self.client.get(API_ROOT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
