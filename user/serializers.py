from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import serializers

from feed.serializers import get_full_url, PostListSerializer


class UserInfoSerializer(serializers.ModelSerializer):
    num_followers = serializers.SerializerMethodField()
    num_followings = serializers.SerializerMethodField()
    followers_url = serializers.SerializerMethodField()
    followings_url = serializers.SerializerMethodField()
    posts = PostListSerializer(many=True, read_only=True)

    def get_num_followers(self, instance):
        return self.context["num_followers"]

    def get_num_followings(self, instance):
        return self.context["num_followings"]

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
