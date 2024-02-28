import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from feed.models import PostImage
from tests.test_post_api import sample_post
from tests.test_user_info_api import sample_user

UPLOAD_POST_IMAGE_URL = reverse("feed:post-image-upload", args=[1])
DELETE_POST_IMAGE_URL = reverse("feed:post-image-delete", args=[1])


class UnauthenticatedPostImageApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_post_image_upload_auth_required(self):
        user = sample_user(email="sample@user.com")
        post = sample_post(user)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                UPLOAD_POST_IMAGE_URL,
                {"image": ntf, "post": post},
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_image_delete_auth_required(self):
        res = self.client.delete(DELETE_POST_IMAGE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPostImageApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def tearDown(self):
        PostImage.objects.all().delete()

    def test_post_image_upload_is_forbidden(self):
        user = sample_user(email="sample@user.com")
        post = sample_post(user)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                UPLOAD_POST_IMAGE_URL,
                {"image": ntf, "post": post},
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(post.images.count(), 0)


class AuthorPostImageApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def tearDown(self):
        PostImage.objects.all().delete()

    def test_post_image_upload(self):
        post = sample_post(self.user)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                UPLOAD_POST_IMAGE_URL, {"image": ntf}, format="multipart"
            )

        image = PostImage.objects.get(id=1)

        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        self.assertEqual(post.images.count(), 1)
        self.assertTrue(os.path.exists(image.image.path))
