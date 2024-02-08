from django.http import HttpResponseRedirect
from rest_framework import mixins, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from feed.models import Hashtag, Post, PostImage, Like
from feed.serializers import (
    PostSerializer,
    PostListSerializer,
    PostDetailSerializer,
    HashtagListDetailSerializer,
    PostImageSerializer,
    CommentCreateSerializer,
)


class CreateListRetrieveUpdateViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    """
    A viewset that provides default `create()`, `list()`, `retrieve()`,
    `update()` and `partial_update()` actions.
    """

    pass


class HashtagViewSet(CreateListRetrieveUpdateViewSet):
    """Endpoint for creating, updating and retrieving hashtags."""

    queryset = Hashtag.objects.all()
    serializer_class = HashtagListDetailSerializer


class PostViewSet(CreateListRetrieveUpdateViewSet):
    """Endpoint for creating, updating and retrieving posts."""

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Post.objects.all()

        if self.action == "retrieve":
            queryset = queryset.select_related("author").prefetch_related(
                "hashtags", "likes", "comments__author", "images"
            )

        if self.action == "list":
            queryset = queryset.select_related("author").prefetch_related(
                "hashtags", "likes", "comments", "images"
            )

            hashtag = self.request.query_params.get("hashtag", None)

            if hashtag:
                queryset = queryset.filter(hashtags__name__iexact=hashtag)

        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "liked_posts", "followed_authors_posts"]:
            return PostListSerializer

        if self.action == "retrieve":
            return PostDetailSerializer

        if self.action == "upload_image":
            return PostImageSerializer

        if self.action == "add_comment":
            return CommentCreateSerializer

        return PostSerializer

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        post_ids_liked_by_user = Like.objects.filter(
            user=self.request.user
        ).values_list("post", flat=True)

        context.update({"post_ids_liked_by_user": post_ids_liked_by_user})
        return context

    @action(methods=["POST"], detail=True, url_path="upload_image")
    def upload_image(self, request, pk=None):
        """Endpoint for uploading pictures to specific post."""
        post = self.get_object()
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(post=post)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, url_path="like_toggle")
    def like_toggle(self, request, pk=None):
        """Endpoint for adding and removing likes to specific post."""
        post = self.get_object()
        user = request.user

        has_like_from_user = Like.objects.filter(user=user, post=post).exists()

        if has_like_from_user:
            like = Like.objects.get(user=user, post=post)
            like.delete()
        else:
            Like.objects.create(user=user, post=post)

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    @action(methods=["POST"], detail=True, url_path="add_comment")
    def add_comment(self, request, pk=None):
        """Endpoint for creating adding comments to specific post"""
        author = request.user
        post = self.get_object()
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(author=author, post=post)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=["GET"], detail=False, url_path="liked_posts")
    def liked_posts(self, request):
        """Endpoint for getting the list of posts liked by the logged-in user."""
        user = request.user

        posts = (
            Post.objects.filter(likes__user=user)
            .select_related("author")
            .prefetch_related("hashtags", "likes", "comments", "images")
        )
        serializer = self.get_serializer(posts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["GET"], detail=False, url_path="followed_authors_posts")
    def followed_authors_posts(self, request):
        """
        Endpoint for getting the list of posts from the authors
        liked by the logged-in user.
        """
        posts = (
            Post.objects.filter(author__followers__follower=self.request.user)
            .select_related("author")
            .prefetch_related("hashtags", "likes", "comments", "images")
        )
        serializer = self.get_serializer(posts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ImageDeleteView(generics.DestroyAPIView):
    """Endpoint for removing an image from post"""

    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer
