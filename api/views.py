from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,permission_classes
)
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from .permissions import IsAdminUserOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import TaskSerializer
from .models import Task
from rest_framework import generics
from django.contrib.auth.models import User


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
@permission_classes((permissions.IsAuthenticated,))
def GetAllItems(request):
    tasks = Task.objects.all()
    serializer = TaskSerializer(tasks, many=True)

    return Response(serializer.data)


'''view for the detailed view of a specific item with the help of pk'''

@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,IsAdminUser,))
def GetItem(request,pk):
    tasks = Task.objects.get(id = pk)
    serializer = TaskSerializer(tasks,many = False)
    return Response(serializer.data)


'''Create a todo item'''

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,IsAdminUser,))
def CreateItem(request):
    serializer = TaskSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


'''Update a specific item with the help of pk'''

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,IsAdminUser,))
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
@permission_classes((permissions.IsAuthenticated,IsAdminUser,))
def DeleteItem(request,pk):
    task = Task.objects.get(id=pk)
    task.delete()

    return Response('Task deleted successfully!')

