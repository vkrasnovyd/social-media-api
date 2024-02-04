from rest_framework import serializers

from feed.models import Hashtag, Post, PostImage


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
    num_likes = serializers.SerializerMethodField()
    num_comments = serializers.SerializerMethodField()
    images = PostImageListSerializer(many=True, read_only=True)

    @staticmethod
    def get_num_likes(instance):
        return instance.likes.count()

    @staticmethod
    def get_num_comments(instance):
        return instance.comments.count()

    class Meta:
        model = Post
        fields = (
            "id",
            "text",
            "hashtags",
            "num_likes",
            "num_comments",
            "images",
        )
