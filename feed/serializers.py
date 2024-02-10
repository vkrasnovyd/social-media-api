from django.urls import reverse
from rest_framework import serializers
from feed.models import Hashtag, Post, PostImage, Comment
from social_media_api import settings


def get_full_url(url: str) -> str:
    return f"{settings.BASE_URL}{url}"


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ("id", "name")


class HashtagListDetailSerializer(serializers.ModelSerializer):
    posts_list = serializers.SerializerMethodField()

    @staticmethod
    def get_posts_list(instance: Hashtag) -> str:
        posts_list = get_full_url(reverse("feed:post-list"))
        return f"{posts_list}?hashtag={instance.name}"

    class Meta:
        model = Hashtag
        fields = ("id", "name", "posts_list")


class PostSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True, read_only=False, required=False)

    class Meta:
        model = Post
        fields = ("id", "text", "hashtags")

    def create(self, validated_data):
        hashtags_data = validated_data.pop("hashtags")
        post = Post.objects.create(**validated_data)

        for hashtag in hashtags_data:
            new_hashtag = Hashtag.objects.get_or_create(
                name=dict(hashtag).get("name")
            )
            post.hashtags.add(new_hashtag[0])
        post.save()

        return post


class PostImageListSerializer(serializers.ModelSerializer):
    delete_image_url = serializers.SerializerMethodField()

    @staticmethod
    def get_delete_image_url(instance):
        return get_full_url(
            reverse("feed:post-image-delete", kwargs={"pk": instance.id})
        )

    class Meta:
        model = PostImage
        fields = ("id", "image", "delete_image_url")


class PostListSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(many=False)
    author_url = serializers.SerializerMethodField()
    hashtags = serializers.StringRelatedField(many=True)
    num_likes = serializers.IntegerField()
    num_comments = serializers.IntegerField()
    images = PostImageListSerializer(many=True, read_only=True)
    detail_url = serializers.SerializerMethodField(read_only=True)
    has_like_from_user = serializers.SerializerMethodField()
    like_toggle = serializers.SerializerMethodField()

    @staticmethod
    def get_author_url(instance):
        return get_full_url(instance.author.get_absolute_url())

    @staticmethod
    def get_detail_url(instance):
        return get_full_url(instance.get_absolute_url())

    def get_has_like_from_user(self, instance):
        return instance.id in self.context["post_ids_liked_by_user"]

    @staticmethod
    def get_like_toggle(instance):
        return get_full_url(
            reverse("feed:post-like-toggle", kwargs={"pk": instance.id})
        )

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "author_url",
            "text",
            "hashtags",
            "num_likes",
            "num_comments",
            "images",
            "detail_url",
            "has_like_from_user",
            "like_toggle",
        )


class PostponedPostListSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True, read_only=True)
    images = PostImageListSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ("id", "published_at", "text", "hashtags", "images")


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    author_url = serializers.SerializerMethodField()

    @staticmethod
    def get_author_url(instance):
        return get_full_url(instance.author.get_absolute_url())

    class Meta:
        model = Comment
        fields = ("id", "author", "author_url", "text")


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "text")


class PostDetailSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(many=False)
    author_url = serializers.SerializerMethodField()
    hashtags = serializers.StringRelatedField(many=True)
    num_likes = serializers.IntegerField()
    images = PostImageListSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    has_like_from_user = serializers.SerializerMethodField()
    like_toggle = serializers.SerializerMethodField()
    users_who_liked_url = serializers.SerializerMethodField()

    @staticmethod
    def get_author_url(instance):
        return get_full_url(instance.author.get_absolute_url())

    def get_has_like_from_user(self, instance):
        return instance.id in self.context["post_ids_liked_by_user"]

    @staticmethod
    def get_like_toggle(instance):
        return get_full_url(
            reverse("feed:post-like-toggle", kwargs={"pk": instance.id})
        )

    @staticmethod
    def get_users_who_liked_url(instance):
        return get_full_url(
            reverse("feed:post-users-who-liked", kwargs={"pk": instance.id})
        )

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "author_url",
            "text",
            "hashtags",
            "num_likes",
            "comments",
            "images",
            "has_like_from_user",
            "like_toggle",
            "users_who_liked_url",
        )


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ("id", "image")
