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

    def get_is_followed_by_user(self, instance) -> bool | None:
        if self.context.get("user") == instance:
            return None
        return instance.id in self.context.get("followings_ids")

    def get_follow_toggle(self, instance) -> str | None:
        if self.context.get("user") == instance:
            return None
        return get_full_url(
            reverse("user:user-follow-toggle", kwargs={"pk": instance.id})
        )

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "profile_image",
            "first_name",
            "last_name",
            "bio",
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
        fields = (
            "id",
            "username",
            "profile_image",
            "first_name",
            "last_name",
            "profile_url",
        )


class ManageUserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(read_only=True)
    profile_url = serializers.SerializerMethodField()
    liked_posts_url = serializers.SerializerMethodField()

    @staticmethod
    def get_profile_url(instance):
        return get_full_url(instance.get_absolute_url())

    @staticmethod
    def get_liked_posts_url(instance):
        return get_full_url(reverse("feed:post-liked-posts"))

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "first_name",
            "last_name",
            "username",
            "bio",
            "profile_image",
            "profile_url",
            "liked_posts_url",
        )


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "profile_image")


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "password")
        read_only_fields = ("id",)
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        """Create user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)


class UserChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(style={"input_type": "password"})
    new_password = serializers.CharField(style={"input_type": "password"})

    class Meta:
        model = get_user_model()
        fields = ("id", "old_password", "new_password")
        read_only_fields = ("id",)
