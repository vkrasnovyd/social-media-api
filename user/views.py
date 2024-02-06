from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from feed.models import Like
from user.models import Follow
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

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super().get_serializer_context()

        post_ids_liked_by_user = Like.objects.filter(
            user=self.request.user
        ).values_list("post", flat=True)

        context.update({"post_ids_liked_by_user": post_ids_liked_by_user})

        if self.action == "retrieve":
            num_followers = self.get_followers(self.get_object()).count()
            num_followings = self.get_followings(self.get_object()).count()

            context.update({"num_followers": num_followers})
            context.update({"num_followings": num_followings})

        return context

    @staticmethod
    def get_followers(retrieved_user):
        """Method for getting QuerySet of user's followers."""
        follow_relations = Follow.objects.filter(following=retrieved_user)
        return get_user_model().objects.filter(followings__in=follow_relations)

    @staticmethod
    def get_followings(retrieved_user):
        """Method for getting QuerySet of user's followers."""
        follow_relations = Follow.objects.filter(follower=retrieved_user)
        return get_user_model().objects.filter(followers__in=follow_relations)

    @action(
        methods=["GET"], detail=False, url_path=r"(?P<pk>[^/.]+)/followers"
    )
    def followers(self, request, pk=None):
        """Endpoint for getting a list of user's followers."""
        followers = self.get_followers(self.get_object())
        serializer = UserInfoListSerializer(followers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"], detail=False, url_path=r"(?P<pk>[^/.]+)/followings"
    )
    def followings(self, request, pk=None):
        """Endpoint for getting a list of user's followings."""
        followings = self.get_followings(self.get_object())
        serializer = UserInfoListSerializer(followings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
