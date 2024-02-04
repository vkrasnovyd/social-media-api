from rest_framework import serializers

from feed.models import Hashtag, Post, PostImage, Comment
from social_media_api import settings


def get_full_url(url: str) -> str:
    return f"{settings.BASE_URL}{url}"


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ("id", "name")


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "text", "hashtags")


class PostImageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ("id", "image")


class PostListSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(many=False)
    num_likes = serializers.SerializerMethodField()
    num_comments = serializers.SerializerMethodField()
    images = PostImageListSerializer(many=True, read_only=True)
    detail_url = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_num_likes(instance):
        return instance.likes.count()

    @staticmethod
    def get_num_comments(instance):
        return instance.comments.count()

    @staticmethod
    def get_detail_url(instance):
        return get_full_url(instance.get_absolute_url())

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "text",
            "hashtags",
            "num_likes",
            "num_comments",
            "images",
            "detail_url",
        )


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "author", "text")


class PostDetailSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(many=False)
    num_likes = serializers.SerializerMethodField()
    images = PostImageListSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    @staticmethod
    def get_num_likes(instance):
        return instance.likes.count()

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "text",
            "hashtags",
            "num_likes",
            "comments",
            "images",
        )
