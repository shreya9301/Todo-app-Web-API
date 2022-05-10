from rest_framework import permissions

#custom permission class to give access only to admins users

class IsAdminUserOrReadOnly(permissions.BasePermission):

     def has_permission(self, request, view):
        if request.user.is_staff or request.user.is_superuser:
             return True
        return False

     def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff or request.user.is_superuser:
            return True
        return False

