from django.urls import include, path
from rest_framework import routers

from user.views import UserInfoViewSet


router = routers.DefaultRouter()
router.register("", UserInfoViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "user"
