import json

from django.contrib.auth import get_user_model
from django.db.models import Count, OuterRef, Exists, QuerySet
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from feed.models import Post, Like
from feed.serializers import PostListSerializer, PostDetailSerializer
from tests.test_hashtag_api import sample_hashtag
from tests.test_user_info_api import sample_user
from user.models import User, Follow
from user.serializers import UserInfoListSerializer

POST_CREATE_URL = reverse("feed:post-list")
LIKED_POSTS_URL = reverse("feed:post-liked-posts")
FOLLOWED_AUTHORS_POSTS_URL = reverse("feed:post-followed-authors-posts")

POST_DETAIL_URL = reverse("feed:post-detail", args=[1])
POST_LIKE_TOGGLE_URL = reverse("feed:post-like-toggle", args=[1])
POST_ADD_COMMENT_URL = reverse("feed:post-add-comment", args=[1])
USERS_WHO_LIKED_POST_URL = reverse("feed:post-users-who-liked", args=[1])


def get_annotated_post_detail(user: User) -> QuerySet[Post]:
    posts = Post.objects.annotate(
        num_likes=Count("likes", distinct=True),
        has_like_from_user=Exists(
            Like.objects.filter(user=user, post=OuterRef("pk"))
        ),
    )
    return posts


def get_annotated_posts_list(user: User) -> QuerySet[Post]:
    posts = get_annotated_post_detail(user)
    posts = posts.annotate(
        num_comments=Count("comments", distinct=True),
    )
    return posts


def sample_post(user: User, **params) -> Post:
    defaults = {
        "author": user,
        "text": "Sample text.",
    }
    defaults.update(params)

    return Post.objects.create(**defaults)


class UnauthenticatedPostApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_liked_posts_auth_required(self):
        res = self.client.get(LIKED_POSTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_followed_authors_posts_auth_required(self):
        res = self.client.get(FOLLOWED_AUTHORS_POSTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_post_detail_auth_required(self):
        res = self.client.get(POST_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_like_auth_required(self):
        res = self.client.get(POST_LIKE_TOGGLE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_post_comment_auth_required(self):
        res = self.client.get(POST_ADD_COMMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_users_who_liked_post_auth_required(self):
        res = self.client.get(USERS_WHO_LIKED_POST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPostApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)
        self.payload = {"text": "Test text."}

    def test_get_liked_posts(self):
        user = sample_user()
        post_without_like = sample_post(user)
        post_with_like1 = sample_post(user)
        post_with_like2 = sample_post(user)
        Like.objects.create(post=post_with_like1, user=self.user)
        Like.objects.create(post=post_with_like2, user=self.user)

        res = self.client.get(LIKED_POSTS_URL)

        posts = get_annotated_posts_list(self.user)

        serializer1 = PostListSerializer(posts.get(id=post_without_like.id))
        serializer2 = PostListSerializer(posts.get(id=post_with_like1.id))
        serializer3 = PostListSerializer(posts.get(id=post_with_like2.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serializer1.data, res.json())
        self.assertIn(serializer2.data, res.json())
        self.assertIn(serializer3.data, res.json())

    def test_get_followed_authors_posts(self):
        not_followed_user = sample_user(email="not_followed@user.com")
        followed_user = sample_user(email="followed@user.com")
        Follow.objects.create(follower=self.user, following=followed_user)

        post_of_not_followed_user = sample_post(not_followed_user)
        post_of_followed_user1 = sample_post(followed_user)
        post_of_followed_user2 = sample_post(followed_user)

        posts = get_annotated_posts_list(self.user)

        serializer1 = PostListSerializer(
            posts.get(id=post_of_not_followed_user.id)
        )
        serializer2 = PostListSerializer(
            posts.get(id=post_of_followed_user1.id)
        )
        serializer3 = PostListSerializer(
            posts.get(id=post_of_followed_user2.id)
        )

        res = self.client.get(FOLLOWED_AUTHORS_POSTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serializer1.data, res.json())
        self.assertIn(serializer2.data, res.json())
        self.assertIn(serializer3.data, res.json())

    def test_retrieve_post_detail(self):
        post = sample_post(self.user)
        posts = get_annotated_post_detail(self.user)

        res = self.client.get(POST_DETAIL_URL)
        serializer = PostDetailSerializer(posts.get(id=post.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_users_who_liked_post(self):
        post = sample_post(self.user)
        user_without_like = sample_user(email="sample@user.com")
        user_who_liked1 = sample_user(email="first@user.com")
        user_who_liked2 = sample_user(email="second@user.com")

        Like.objects.create(user=user_who_liked1, post=post)
        Like.objects.create(user=user_who_liked2, post=post)

        serializer1 = UserInfoListSerializer(user_without_like)
        serializer2 = UserInfoListSerializer(user_who_liked1)
        serializer3 = UserInfoListSerializer(user_who_liked2)

        res = self.client.get(USERS_WHO_LIKED_POST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serializer1.data, res.json())
        self.assertIn(serializer2.data, res.json())
        self.assertIn(serializer3.data, res.json())

    def test_post_like_toggle(self):
        post = sample_post(self.user)
        posts = get_annotated_posts_list(self.user)

        # Test adding like with a toggle
        self.client.get(POST_LIKE_TOGGLE_URL)
        post = posts.get(id=post.id)

        self.assertTrue(
            Like.objects.filter(post=post, user=self.user).exists()
        )

        # Test removing like with a toggle
        self.client.get(POST_LIKE_TOGGLE_URL)
        post = posts.get(id=post.id)

        self.assertFalse(
            Like.objects.filter(post=post, user=self.user).exists()
        )

    def test_add_post_comment(self):
        sample_post(self.user)
        json_data = json.dumps(self.payload)

        res = self.client.post(
            POST_ADD_COMMENT_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["text"], self.payload["text"])

    def test_create_post(self):
        json_data = json.dumps(self.payload)

        res = self.client.post(
            POST_CREATE_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["text"], self.payload["text"])

    def test_create_post_with_hashtag(self):
        payload = self.payload
        hashtag1 = {"name": "first_hashtag"}
        hashtag2 = {"name": "second_hashtag"}
        payload["hashtags"] = [hashtag1, hashtag2]
        json_data = json.dumps(payload)

        res = self.client.post(
            POST_CREATE_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["text"], self.payload["text"])

        res_hashtags = [
            dict(hashtag)["name"] for hashtag in res.data["hashtags"]
        ]
        self.assertIn(hashtag1["name"], res_hashtags)
        self.assertIn(hashtag2["name"], res_hashtags)

    def test_put_post_by_not_author_is_forbidden(self):
        author = sample_user()
        sample_post(author)
        json_data = json.dumps(self.payload)

        res = self.client.put(
            POST_DETAIL_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_post_by_not_author_is_forbidden(self):
        author = sample_user()
        sample_post(author)

        res = self.client.delete(POST_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AuthorPostApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)
        self.payload = {"text": "Test text."}

    def test_put_post(self):
        sample_post(self.user)
        json_data = json.dumps(self.payload)

        res = self.client.put(
            POST_DETAIL_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["text"], self.payload["text"])

    def test_put_post_with_hashtag(self):
        payload = self.payload
        hashtag1 = {"name": "first_hashtag"}
        hashtag2 = {"name": "second_hashtag"}
        hashtag3 = {"name": "third_hashtag"}
        payload["hashtags"] = [hashtag2, hashtag3]
        json_data = json.dumps(payload)

        post = sample_post(self.user)
        for hashtag in [hashtag1, hashtag2]:
            new_hashtag = sample_hashtag(name=hashtag["name"])
            post.hashtags.add(new_hashtag)
            post.save()

        res = self.client.put(
            POST_DETAIL_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["text"], self.payload["text"])

        res_hashtags = [
            dict(hashtag)["name"] for hashtag in res.data["hashtags"]
        ]
        self.assertNotIn(hashtag1["name"], res_hashtags)
        self.assertIn(hashtag2["name"], res_hashtags)
        self.assertIn(hashtag3["name"], res_hashtags)

    def test_delete_post(self):
        sample_post(self.user)

        res = self.client.delete(POST_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
