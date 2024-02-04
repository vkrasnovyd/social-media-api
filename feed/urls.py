from django.urls import include, path
from rest_framework import routers

from feed.views import HashtagViewSet, PostViewSet


router = routers.DefaultRouter()
router.register("hashtags", HashtagViewSet, basename="hashtag")
router.register("posts", PostViewSet, basename="post")

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "feed"
