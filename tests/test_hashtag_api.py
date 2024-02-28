from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from feed.models import Hashtag
from feed.serializers import HashtagListSerializer, HashtagDetailSerializer

HASHTAG_LIST_URL = reverse("feed:hashtag-list")
HASHTAG_DETAIL_URL = reverse("feed:hashtag-detail", args=[1])


def sample_hashtag(**params) -> Hashtag:
    defaults = {"name": "sample_hashtag"}
    defaults.update(params)

    return Hashtag.objects.create(**defaults)


class UnauthenticatedHashtagApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_hashtags_list_auth_required(self):
        res = self.client.get(HASHTAG_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_hashtag_detail_auth_required(self):
        res = self.client.get(HASHTAG_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedHashtagApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)
        self.payload = {"name": "another_tag"}

    def test_get_hashtags_list(self):
        sample_hashtag()
        sample_hashtag(name=self.payload.get("name"))

        res = self.client.get(HASHTAG_LIST_URL)

        hashtags = Hashtag.objects.order_by("name")
        serializer = HashtagListSerializer(hashtags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["results"], serializer.data)

    def test_retrieve_hashtag_detail(self):
        hashtag = sample_hashtag()

        res = self.client.get(HASHTAG_DETAIL_URL)

        serializer = HashtagDetailSerializer(hashtag)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_hashtag_forbidden(self):
        res = self.client.post(HASHTAG_LIST_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_hashtag_forbidden(self):
        sample_hashtag()

        res = self.client.put(HASHTAG_DETAIL_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_hashtag_forbidden(self):
        sample_hashtag()

        res = self.client.delete(HASHTAG_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminHashtagApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.payload = {"name": "another_tag"}

    def test_create_hashtag_not_allowed(self):
        res = self.client.post(HASHTAG_LIST_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_hashtag_not_allowed(self):
        sample_hashtag()

        res = self.client.put(HASHTAG_DETAIL_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_hashtag_forbidden(self):
        sample_hashtag()

        res = self.client.delete(HASHTAG_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
