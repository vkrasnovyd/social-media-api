from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Prefetch
from django.http import HttpResponseRedirect
from rest_framework import viewsets, status, mixins, generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from feed.models import Like, Post
from user.models import Follow
from user.serializers import (
    UserInfoSerializer,
    UserInfoListSerializer,
    ManageUserProfileSerializer,
    ProfileImageSerializer,
    UserCreateSerializer,
    UserChangePasswordSerializer,
)


class UserInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint for retrieving basic users' info."""

    def get_queryset(self):
        queryset = get_user_model().objects.all()

        if self.action == "retrieve":
            posts = Prefetch(
                "posts",
                queryset=Post.objects.annotate(
                    num_likes=Count("likes", distinct=True),
                    num_comments=Count("comments", distinct=True),
                ).prefetch_related("images", "hashtags"),
            )
            queryset = queryset.prefetch_related(posts)

            queryset = queryset.annotate(
                num_followers=Count("followers", distinct=True)
            ).annotate(num_followings=Count("followings", distinct=True))

        if self.action == "list":
            search_string = self.request.query_params.get("search", None)
            if search_string:
                queryset = queryset.filter(
                    Q(username__icontains=search_string)
                    | Q(first_name__icontains=search_string)
                    | Q(last_name__icontains=search_string)
                ).distinct()

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return UserInfoListSerializer

        if self.action == "my_profile":
            return ManageUserProfileSerializer

        return UserInfoSerializer

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""

        context = super().get_serializer_context()

        post_ids_liked_by_user = Like.objects.filter(
            user=self.request.user
        ).values_list("post", flat=True)

        context.update({"post_ids_liked_by_user": post_ids_liked_by_user})

        if self.action == "retrieve":
            context["followings_ids"] = Follow.objects.filter(
                follower=self.request.user
            ).values_list("following_id", flat=True)
            context["user"] = self.request.user

        return context

    @action(
        methods=["GET"], detail=False, url_path=r"(?P<pk>[^/.]+)/followers"
    )
    def followers(self, request, pk=None):
        """Endpoint for getting a list of user's followers."""
        retrieved_user = self.get_object()

        follow_relations = Follow.objects.filter(following=retrieved_user)
        followers = get_user_model().objects.filter(
            followings__in=follow_relations
        )

        serializer = UserInfoListSerializer(followers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"], detail=False, url_path=r"(?P<pk>[^/.]+)/followings"
    )
    def followings(self, request, pk=None):
        """Endpoint for getting a list of user's followings."""
        retrieved_user = self.get_object()

        follow_relations = Follow.objects.filter(follower=retrieved_user)
        followings = get_user_model().objects.filter(
            followers__in=follow_relations
        )

        serializer = UserInfoListSerializer(followings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, url_path="follow_toggle")
    def follow_toggle(self, request, pk=None):
        """Endpoint for following and un-following specific user."""
        retrieved_user = self.get_object()
        active_user = request.user

        is_followed_by_user = Follow.objects.filter(
            follower=active_user, following=retrieved_user
        ).exists()

        if is_followed_by_user:
            follow_relation = Follow.objects.filter(
                follower=active_user, following=retrieved_user
            )
            follow_relation.delete()
        else:
            Follow.objects.create(
                follower=active_user, following=retrieved_user
            )

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


class ManageUserProfileViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Endpoint where logged-in user can manage their personal information."""

    queryset = get_user_model().objects.all()

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.action == "upload_image":
            return ProfileImageSerializer

        if self.action == "change_password":
            return UserChangePasswordSerializer

        return ManageUserProfileSerializer

    @action(methods=["POST"], detail=True, url_path="upload_profile_image")
    def upload_image(self, request, pk=None):
        """Endpoint where logged-in user can upload their new profile image."""

        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, url_path="delete_profile_image")
    def delete_image(self, request, pk=None):
        """Endpoint where logged-in user can delete their own profile image."""

        user = self.get_object()
        user.profile_image = None
        user.save()

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    @action(methods=["POST"], detail=False, url_path="change_password")
    def change_password(self, request):
        """Endpoint where logged-in user can change their password."""
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        if not user.check_password(serializer.data.get("old_password")):
            return Response(
                {"old_password": ["Wrong password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.data.get("new_password"))
        user.save()

        return Response("Success.", status=status.HTTP_200_OK)


class CreateUserView(generics.CreateAPIView):
    """Endpoint for registering new users."""

    queryset = get_user_model().objects.all()
    serializer_class = UserCreateSerializer


class CreateTokenView(ObtainAuthToken):
    """Login endpoint."""

    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class LogoutAPIView(APIView):
    """Endpoint for invalidating user token."""

    @staticmethod
    def get(request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)
