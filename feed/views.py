from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch, Exists, OuterRef
from django.http import HttpResponseRedirect
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status, generics, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from feed.models import Hashtag, Post, PostImage, Like
from feed.serializers import (
    PostSerializer,
    PostListSerializer,
    PostDetailSerializer,
    HashtagListSerializer,
    HashtagDetailSerializer,
    PostImageSerializer,
    CommentCreateSerializer,
    PostponedPostListSerializer,
    PostponedPostDetailSerializer,
)
from feed.tasks import publish_postponed_post
from social_media_api.permissions import (
    IsAdminOrIfAuthenticatedReadOnly,
    IsPostAuthorUser,
    IsPostAuthorOrIfAuthenticatedReadOnly,
)
from user.serializers import UserInfoListSerializer


class Pagination(PageNumberPagination):
    page_size = 25
    max_page_size = 100
    page_size_query_param = "page_size"


class HashtagViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    """Endpoint for creating, updating and retrieving hashtags."""

    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = Pagination

    def get_queryset(self):
        queryset = Hashtag.objects.all()

        if self.action == "retrieve":
            user = self.request.user

            posts = Prefetch(
                "posts",
                queryset=(
                    Post.objects.all()
                    .select_related("author")
                    .prefetch_related(
                        "hashtags", "likes", "comments", "images"
                    )
                    .annotate(
                        num_likes=Count("likes", distinct=True),
                        num_comments=Count("comments", distinct=True),
                        has_like_from_user=Exists(
                            Like.objects.filter(user=user, post=OuterRef("pk"))
                        ),
                    )
                ),
            )
            queryset = queryset.prefetch_related(posts)

        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return HashtagDetailSerializer

        return HashtagListSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH)
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(self, request, *args, **kwargs)


class PostViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    """Endpoint for creating, updating, retrieving and deleting posts."""

    permission_classes = (IsPostAuthorOrIfAuthenticatedReadOnly,)
    pagination_class = Pagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Post.objects.filter(is_published=True)

        if self.action == "retrieve":
            user = self.request.user

            queryset = queryset.annotate(
                num_likes=Count("likes", distinct=True),
                has_like_from_user=Exists(
                    Like.objects.filter(user=user, post=OuterRef("pk"))
                ),
            )
            queryset = queryset.select_related("author").prefetch_related(
                "hashtags", "comments__author", "images"
            )

        return queryset

    def get_serializer_class(self):
        if self.action in ["liked_posts", "followed_authors_posts"]:
            return PostListSerializer

        if self.action == "retrieve":
            return PostDetailSerializer

        if self.action == "add_comment":
            return CommentCreateSerializer

        if self.action == "users_who_liked":
            return UserInfoListSerializer

        return PostSerializer

    @action(detail=True, url_path="like_toggle")
    @action(
        detail=True,
        url_path="like_toggle",
        permission_classes=[IsAuthenticated],
    )
    def like_toggle(self, request, pk=None):
        """Endpoint for adding and removing likes to specific posts."""

        post = self.get_object()
        user = request.user

        has_like_from_user = Like.objects.filter(user=user, post=post).exists()

        if has_like_from_user:
            like = Like.objects.get(user=user, post=post)
            like.delete()
        else:
            Like.objects.create(user=user, post=post)

        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    @action(
        methods=["POST"],
        detail=True,
        url_path="add_comment",
        permission_classes=[IsAuthenticated],
    )
    def add_comment(self, request, pk=None):
        """Endpoint for creating adding comments to specific post."""

        author = request.user
        post = self.get_object()
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(author=author, post=post)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=["GET"],
        detail=False,
        url_path="liked_posts",
        permission_classes=[IsAuthenticated],
    )
    def liked_posts(self, request):
        """Endpoint for getting the list of posts liked by the logged-in user."""

        user = request.user

        posts = (
            Post.objects.filter(likes__user=user)
            .select_related("author")
            .prefetch_related("hashtags", "likes", "comments", "images")
            .annotate(
                num_likes=Count("likes", distinct=True),
                num_comments=Count("comments", distinct=True),
                has_like_from_user=Exists(
                    Like.objects.filter(user=user, post=OuterRef("pk"))
                ),
            )
        )
        serializer = self.get_serializer(posts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False,
        url_path="followed_authors_posts",
        permission_classes=[IsAuthenticated],
    )
    def followed_authors_posts(self, request):
        """
        Endpoint for getting the list of posts from the authors
        liked by the logged-in user.
        """

        user = self.request.user

        posts = (
            Post.objects.filter(author__followers__follower=self.request.user)
            .select_related("author")
            .prefetch_related("hashtags", "likes", "comments", "images")
            .annotate(
                num_likes=Count("likes", distinct=True),
                num_comments=Count("comments", distinct=True),
                has_like_from_user=Exists(
                    Like.objects.filter(user=user, post=OuterRef("pk"))
                ),
            )
        )
        serializer = self.get_serializer(posts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=True,
        url_path="users_who_liked",
        permission_classes=[IsAuthenticated],
    )
    def users_who_liked(self, request, pk=None):
        """
        Endpoint for getting the list of users who liked the specific post.
        """

        users_who_liked = get_user_model().objects.filter(likes__post_id=pk)

        serializer = self.get_serializer(users_who_liked, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH)
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        if request.user and request.user.is_authenticated:
            return super().retrieve(self, request, *args, **kwargs)

        return Response(status=status.HTTP_401_UNAUTHORIZED)


class ImageDeleteView(generics.DestroyAPIView):
    """Endpoint for removing an image from post."""

    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer
    permission_classes = (IsAuthenticated, IsPostAuthorUser)


class PostImageUploadView(generics.CreateAPIView):
    """Endpoint for removing an image from post."""

    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer
    permission_classes = (IsPostAuthorUser,)

    def perform_create(self, serializer):
        serializer.save(post=Post.objects.get(id=self.kwargs.get("pk")))

    def post(self, request, *args, **kwargs):
        post = Post.objects.get(id=self.kwargs.get("pk"))

        if request.user and request.user.is_authenticated:
            if post.author == request.user:
                self.create(request, *args, **kwargs)
                return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response(status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    parameters=[
        OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH)
    ]
)
class PostponedPostViewSet(viewsets.ModelViewSet):
    """Endpoint for creating, updating, retrieving and deleting postponed posts."""

    permission_classes = (IsAuthenticated, IsPostAuthorUser)
    pagination_class = Pagination

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        publish_postponed_post.apply_async((post.id,), eta=post.published_at)

    def perform_update(self, serializer):
        post = self.get_object()
        publish_postponed_post.apply_async((post.id,), eta=post.published_at)

    def get_queryset(self):
        queryset = Post.objects.filter(
            is_published=False, author=self.request.user
        ).order_by("published_at")

        if self.action == "list":
            queryset = queryset.prefetch_related("hashtags", "images")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PostponedPostListSerializer

        return PostponedPostDetailSerializer

    @action(
        detail=True,
        url_path="publish_now",
        permission_classes=[IsAuthenticated, IsPostAuthorUser],
    )
    def publish_now(self, request, pk=None):
        post = self.get_object()

        post.publish()

        return HttpResponseRedirect(reverse("feed:postponed-post-list"))
