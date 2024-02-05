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
    queryset = Hashtag.objects.all()
    serializer_class = HashtagListDetailSerializer


class PostViewSet(CreateListRetrieveUpdateViewSet):
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Post.objects.all()

        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("author").prefetch_related(
                "hashtags", "likes", "comments", "images"
            )

        if self.action == "list":

            hashtag = self.request.query_params.get("hashtag", None)

            if hashtag:
                queryset = queryset.filter(hashtags__name__iexact=hashtag)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer

        if self.action == "retrieve":
            return PostDetailSerializer

        if self.action == "upload_image":
            return PostImageSerializer

        return PostSerializer

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        context.update({"user": self.request.user})
        return context

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading pictures to specific post"""
        post = self.get_object()
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(post=post)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        url_path="like",
    )
    def like(self, request, pk=None):
        """Endpoint for adding and removing likes to specific post"""
        post = self.get_object()
        user = request.user

        has_like_from_user = Like.objects.filter(user=user, post=post).exists()

        if has_like_from_user:
            like = Like.objects.get(user=user, post=post)
            like.delete()
        else:
            Like.objects.create(user=user, post=post)

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


class ImageDeleteView(generics.DestroyAPIView):
    """Endpoint for removing an image from post"""

    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer
