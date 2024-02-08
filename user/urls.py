from django.urls import include, path
from rest_framework import routers

from user.views import (
    UserInfoViewSet,
    ManageUserProfileViewSet,
    CreateUserView,
    CreateTokenView,
    LogoutAPIView,
)

router = routers.DefaultRouter()
router.register("users", UserInfoViewSet, basename="user")
router.register("manage", ManageUserProfileViewSet, basename="manage")

urlpatterns = [
    path("", include(router.urls)),
    path("register/", CreateUserView.as_view(), name="register"),
    path("login/", CreateTokenView.as_view(), name="token"),
    path("api/token/logout/", LogoutAPIView.as_view(), name="logout"),
]

app_name = "user"
