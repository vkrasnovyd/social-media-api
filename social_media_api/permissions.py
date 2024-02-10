from rest_framework.permissions import SAFE_METHODS, BasePermission

from feed.models import Post


class IsPostAuthorOrIsAuthenticatedReadOnly(BasePermission):
    """
    The request is authenticated as the object author,
    or is a read-only request for authenticated users.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        obj_type = obj.__class__

        if obj_type == Post:
            return obj.author == request.user

        return obj.post.author == request.user


class IsPostAuthorUser(BasePermission):
    def has_object_permission(self, request, view, obj):
        obj_type = obj.__class__

        if obj_type == Post:
            return obj.author == request.user

        return obj.post.author == request.user