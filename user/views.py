from django.contrib.auth import get_user_model
from rest_framework import viewsets

from user.serializers import (
    UserInfoSerializer,
    UserInfoListSerializer,
)


class UserInfoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = get_user_model().objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return UserInfoListSerializer

        return UserInfoSerializer
