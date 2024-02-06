from django.contrib.auth import get_user_model
from rest_framework import serializers

from feed.serializers import get_full_url, PostListSerializer


class UserInfoSerializer(serializers.ModelSerializer):
    posts = PostListSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "first_name", "last_name", "posts")


class UserInfoListSerializer(serializers.ModelSerializer):
    profile_url = serializers.SerializerMethodField()

    @staticmethod
    def get_profile_url(instance):
        return get_full_url(instance.get_absolute_url())

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "first_name", "last_name", "profile_url")
