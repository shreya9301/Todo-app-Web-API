from rest_framework import permissions

#custom permission class to give access only to admins users

class IsAdminUserOrReadOnly(permissions.BasePermission):

     def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True


