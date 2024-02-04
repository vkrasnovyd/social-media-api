from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from feed.models import Hashtag, Post
from feed.serializers import (
    HashtagSerializer,
    PostSerializer,
    PostListSerializer,
    PostDetailSerializer,
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
    serializer_class = HashtagSerializer


class PostViewSet(CreateListRetrieveUpdateViewSet):
    queryset = Post.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer

        if self.action == "retrieve":
            return PostDetailSerializer

        return PostSerializer
