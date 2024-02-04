from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from feed.models import Hashtag
from feed.serializers import HashtagSerializer


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
