from django.urls import include, path
from rest_framework import routers

from user.views import (
    UserInfoViewSet,
    ManageUserProfileViewSet,
)

router = routers.DefaultRouter()
router.register("users", UserInfoViewSet, basename="user")
router.register("manage", ManageUserProfileViewSet, basename="manage")

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "user"
