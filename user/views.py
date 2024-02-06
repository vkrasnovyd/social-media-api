from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import viewsets

from user.serializers import (
    UserInfoSerializer,
    UserInfoListSerializer,
)


class UserInfoViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        queryset = get_user_model().objects.all()

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

        return UserInfoSerializer
