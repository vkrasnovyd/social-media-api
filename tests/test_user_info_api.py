from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Prefetch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from feed.models import Post, Like
from user.models import User, Follow
from user.serializers import UserInfoListSerializer, UserInfoSerializer

USER_LIST_URL = reverse("user:user-list")
USER_DETAIL_URL = reverse("user:user-detail", args=[2])
USER_FOLLOWERS_URL = reverse("user:user-followers", args=[1])
USER_FOLLOWINGS_URL = reverse("user:user-followings", args=[1])
USER_FOLLOW_TOGGLE_URL = reverse("user:user-follow-toggle", args=[2])


def sample_user(**params) -> User:
    index = get_user_model().objects.count()
    defaults = {"email": f"followed{index}@user.com", "password": "samplepass"}
    defaults.update(params)

    return get_user_model().objects.create(**defaults)


def follow(follower: User, following: User) -> None:
    Follow.objects.create(follower=follower, following=following)


def get_annotated_user_detail(user: User) -> User:
    posts = Prefetch(
        "posts",
        queryset=Post.objects.filter(is_published=True).annotate(
            num_likes=Count("likes", distinct=True),
            num_comments=Count("comments", distinct=True),
            has_like_from_user=Exists(
                Like.objects.filter(user=user, post=OuterRef("pk"))
            ),
        ),
    )
    users = get_user_model().objects.all().prefetch_related(posts)

    users = users.annotate(
        is_followed_by_user=Exists(
            Follow.objects.filter(follower=user, following=OuterRef("pk"))
        ),
        num_followers=Count("followers", distinct=True),
    ).annotate(num_followings=Count("followings", distinct=True))

    return users


class UnauthenticatedUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_users_list_auth_required(self):
        res = self.client.get(USER_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_detail_auth_required(self):
        res = self.client.get(USER_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_followers_list_auth_required(self):
        res = self.client.get(USER_FOLLOWERS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_followings_list_auth_required(self):
        res = self.client.get(USER_FOLLOWINGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_follow_toggle_auth_required(self):
        res = self.client.get(USER_FOLLOW_TOGGLE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpass",
            first_name="John",
            last_name="Doe",
        )
        self.client.force_authenticate(self.user)
        self.payload = {"name": "another_tag"}

    def test_get_users_list(self):
        sample_user(email="sample@user.com")
        res = self.client.get(USER_LIST_URL)

        users = get_user_model().objects.all()
        serializer = UserInfoListSerializer(users, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["results"], serializer.data)

    def test_retrieve_user_detail(self):
        following = sample_user()
        follow(follower=self.user, following=following)
        res = self.client.get(USER_DETAIL_URL)

        users = get_annotated_user_detail(self.user)
        serializer = UserInfoSerializer(users.get(id=following.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_followers_list(self):
        not_follower = sample_user(email="not_follower@user.com")
        follower1 = sample_user()
        follower2 = sample_user()

        for follower in (follower1, follower2):
            follow(follower=follower, following=self.user)

        res = self.client.get(USER_FOLLOWERS_URL)

        serisliser1 = UserInfoListSerializer(not_follower)
        serisliser2 = UserInfoListSerializer(follower1)
        serisliser3 = UserInfoListSerializer(follower2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serisliser1.data, res.data)
        self.assertIn(serisliser2.data, res.data)
        self.assertIn(serisliser3.data, res.data)

    def test_get_followings_list(self):
        not_following = sample_user(email="not_follower@user.com")
        following1 = sample_user()
        following2 = sample_user()

        for following in (following1, following2):
            follow(follower=self.user, following=following)

        res = self.client.get(USER_FOLLOWINGS_URL)

        serisliser1 = UserInfoListSerializer(not_following)
        serisliser2 = UserInfoListSerializer(following1)
        serisliser3 = UserInfoListSerializer(following2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serisliser1.data, res.data)
        self.assertIn(serisliser2.data, res.data)
        self.assertIn(serisliser3.data, res.data)

    def test_get_follow_toggle(self):
        following = sample_user(email="not_follower@user.com")

        # Test adding Follow connection with a toggle
        self.client.get(USER_FOLLOW_TOGGLE_URL)

        self.assertTrue(
            Follow.objects.filter(
                follower=self.user, following=following
            ).exists()
        )

        # Test removing Follow connection with a toggle
        self.client.get(USER_FOLLOW_TOGGLE_URL)

        self.assertFalse(
            Follow.objects.filter(
                follower=self.user, following=following
            ).exists()
        )
