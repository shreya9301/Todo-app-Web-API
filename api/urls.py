from django.urls import path
from . import views
urlpatterns = [
    #Todocontroller url paths
    path('',views.apiOverview,name = "api-overview"),
    path('getall/',views.GetAllItems,name = "get-all"),
    path('get/<str:pk>/',views.GetItem,name="get-item"),
    path('create/',views.CreateItem,name="create-item"),
    path('put/<str:pk>/',views.UpdateItem,name="update-item"),
    path('delete/<str:pk>/',views.DeleteItem,name="delete-item"),
]