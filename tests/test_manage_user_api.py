import json
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.serializers import ManageUserProfileSerializer

USER_MANAGE_URL = reverse("user:manage-detail")
USER_CHANGE_PASSWORD_URL = reverse("user:manage-change-password")
USER_UPLOAD_PROFILE_IMAGE_URL = reverse("user:manage-upload-image")
USER_DELETE_PROFILE_IMAGE_URL = reverse("user:manage-delete-image")


class UnauthenticatedManageUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_user_manage(self):
        res = self.client.get(USER_MANAGE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_change_password(self):
        res = self.client.get(USER_CHANGE_PASSWORD_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_upload_profile_image(self):
        res = self.client.get(USER_UPLOAD_PROFILE_IMAGE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_delete_profile_image(self):
        res = self.client.get(USER_DELETE_PROFILE_IMAGE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedManageUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_get_user_manage(self):
        res = self.client.get(USER_MANAGE_URL)

        serializer = ManageUserProfileSerializer(self.user)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_put_user_manage(self):
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Sample bio",
        }
        json_data = json.dumps(payload)

        res = self.client.put(
            USER_MANAGE_URL, json_data, content_type="application/json"
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for key, value in payload.items():
            self.assertEqual(res.json().get(key), value)

    def test_put_user_change_password(self):
        payload = {"old_password": "testpass", "new_password": "newpass"}
        json_data = json.dumps(payload)

        res = self.client.post(
            USER_CHANGE_PASSWORD_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password(payload["new_password"]))

    def test_put_user_change_password_with_wrong_old_password_is_not_allowed(
        self,
    ):
        payload = {"old_password": "wrongpass", "new_password": "newpass"}
        json_data = json.dumps(payload)

        res = self.client.post(
            USER_CHANGE_PASSWORD_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_upload_profile_image(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                USER_UPLOAD_PROFILE_IMAGE_URL,
                {"image": ntf},
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(self.user.profile_image)
