import re
from django.shortcuts import render
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,permission_classes
)
from rest_framework.permissions import AllowAny, IsAuthenticated
#from .permissions import IsAdminUserOrReadOnly
from rest_framework.response import Response
from .serializers import UserSerializer,TaskSerializer
from .models import Task
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



''' ---------------TODOCONTROLLER API VIEWS-- -----------------'''

@api_view(['GET'])
@permission_classes((permissions.AllowAny, ))
def apiOverview(request):
    api_urls = {
        'GetAllItems' : '/getall/',
        'GetItem' : '/get/<str:pk>/',
        'CreateItem' : '/create/',
        'UpdateItem' : '/put/<str:pk>/',
        'DeleteItem' : '/delete/<str:pk>/',
    }

    return Response(api_urls)


'''Get all todo items'''

@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def GetAllItems(request):
    tasks = Task.objects.all()
    serializer = TaskSerializer(tasks, many=True)

    return Response(serializer.data)



'''view for the detailed view of a specific item with the help of pk'''

@api_view(['GET'])
def GetItem(request,pk):
    tasks = Task.objects.get(id = pk)
    serializer = TaskSerializer(tasks,many = False)
    return Response(serializer.data)


'''Create a todo item'''

@api_view(['POST'])
def CreateItem(request):
    serializer = TaskSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


'''Update a specific item with the help of pk'''

@api_view(['POST'])
def UpdateItem(request,pk):
    task = Task.objects.get(id=pk)
    serializer = TaskSerializer(instance=task,data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


'''Delete a specific task with the help of pk'''

@api_view(['DELETE'])
def DeleteItem(request,pk):
    task = Task.objects.get(id=pk)
    task.delete()

    return Response('Task deleted successfully!')

