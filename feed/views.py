from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from feed.models import Hashtag, Post
from feed.serializers import (
    PostSerializer,
    PostListSerializer,
    PostDetailSerializer,
    HashtagListDetailSerializer,
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

        return PostSerializer
