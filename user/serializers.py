from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import serializers

from feed.serializers import get_full_url, PostListSerializer


class UserInfoSerializer(serializers.ModelSerializer):
    num_followers = serializers.IntegerField()
    num_followings = serializers.IntegerField()
    followers_url = serializers.SerializerMethodField()
    followings_url = serializers.SerializerMethodField()
    is_followed_by_user = serializers.SerializerMethodField()
    follow_toggle = serializers.SerializerMethodField()
    posts = PostListSerializer(many=True, read_only=True)

    @staticmethod
    def get_followers_url(instance) -> str:
        return get_full_url(
            reverse("user:user-followers", kwargs={"pk": instance.id})
        )

    @staticmethod
    def get_followings_url(instance) -> str:
        return get_full_url(
            reverse("user:user-followings", kwargs={"pk": instance.id})
        )

    def get_is_followed_by_user(self, instance) -> bool:
        return instance.id in self.context.get("followings_ids")

    @staticmethod
    def get_follow_toggle(instance):
        return get_full_url(
            reverse("user:user-follow-toggle", kwargs={"pk": instance.id})
        )

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "num_followers",
            "num_followings",
            "followers_url",
            "followings_url",
            "is_followed_by_user",
            "follow_toggle",
            "posts",
        )


class UserInfoListSerializer(serializers.ModelSerializer):
    profile_url = serializers.SerializerMethodField()

    @staticmethod
    def get_profile_url(instance):
        return get_full_url(instance.get_absolute_url())

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "first_name", "last_name", "profile_url")
