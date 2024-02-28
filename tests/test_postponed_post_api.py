from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient

from feed.models import Post
from feed.serializers import (
    PostponedPostListSerializer,
    PostponedPostDetailSerializer,
)
from tests.test_user_info_api import sample_user
from user.models import User

POSTPONED_POST_LIST_URL = reverse("feed:postponed-post-list")
POSTPONED_POST_DETAIL_URL = reverse("feed:postponed-post-detail", args=[1])
POSTPONED_POST_PUBLISH_NOW_URL = reverse(
    "feed:postponed-post-publish-now", args=[1]
)


def sample_postponed_post(user: User, **params) -> Post:
    published_at = now() + timedelta(minutes=15)

    defaults = {
        "author": user,
        "text": "Sample text.",
        "is_published": False,
        "published_at": published_at,
    }
    defaults.update(params)

    return Post.objects.create(**defaults)


class UnauthenticatedPostponedPostApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_postponed_posts_auth_required(self):
        res = self.client.get(POSTPONED_POST_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_postponed_post_detail_auth_required(self):
        res = self.client.get(POSTPONED_POST_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_postponed_post_publish_now_auth_required(self):
        res = self.client.get(POSTPONED_POST_PUBLISH_NOW_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorPostponedPostApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)
        self.payload = {
            "text": "Test text.",
            "published_at": "2024-02-27 12:01:00",
        }

    def test_get_postponed_post_list(self):
        user1 = self.user
        user2 = sample_user(email="another@user.com")

        post1 = sample_postponed_post(user1)
        post2 = sample_postponed_post(user2)

        posts = Post.objects.filter(is_published=False)

        serializer1 = PostponedPostListSerializer(posts.get(id=post1.id))
        serializer2 = PostponedPostListSerializer(posts.get(id=post2.id))

        res = self.client.get(POSTPONED_POST_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.json()["results"])
        self.assertNotIn(serializer2.data, res.json()["results"])

    def test_retrieve_postponed_post_detail(self):
        post = sample_postponed_post(self.user)

        res = self.client.get(POSTPONED_POST_DETAIL_URL)
        serializer = PostponedPostDetailSerializer(post)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    @freeze_time("2024-02-27 12:00:01")
    def test_postponed_post_publish_now(self):
        post = sample_postponed_post(self.user)

        res = self.client.get(POSTPONED_POST_PUBLISH_NOW_URL)
        published_at = now()
        post = Post.objects.get(id=post.id)

        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        self.assertTrue(post.is_published)
        self.assertEqual(post.published_at, published_at)
