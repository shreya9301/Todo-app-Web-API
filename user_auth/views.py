from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,permission_classes
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import UserSerializer
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


''' ---------------AUTHCONTROLLER API VIEWS -----------------'''

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['firstname'] = user.first_name
        token['lastname'] = user.last_name
        token['email'] = user.email
        token['isActive'] = user.is_active
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer



@api_view(['POST'])
@permission_classes((permissions.AllowAny, ))
def User_register(request):

	''' For user registration '''

	serializer = UserSerializer(data=request.data)
	if serializer.is_valid():
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
