from django.urls import include, path
from rest_framework import routers

from feed.views import HashtagViewSet, PostViewSet, ImageDeleteView

router = routers.DefaultRouter()
router.register("hashtags", HashtagViewSet, basename="hashtag")
router.register("posts", PostViewSet, basename="post")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "post_images/<int:pk>/delete/",
        ImageDeleteView.as_view(),
        name="post-image-delete",
    ),
]

app_name = "feed"
