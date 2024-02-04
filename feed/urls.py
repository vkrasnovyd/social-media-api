from django.urls import include, path
from rest_framework import routers

from feed.views import HashtagViewSet


router = routers.DefaultRouter()
router.register("hashtags", HashtagViewSet, basename="hashtag")

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "feed"
