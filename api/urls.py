from django.urls import path
from . import views
from .views import MyTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    #authcontroller url paths

    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/',views.User_register, name="user-register"),

    #Todocontroller url paths

    path('',views.apiOverview,name = "api-overview"),
    path('getall/',views.GetAllItems,name = "get-all"),
    path('get/<str:pk>/',views.GetItem,name="get-item"),
    path('create/',views.CreateItem,name="create-item"),
    path('put/<str:pk>/',views.UpdateItem,name="update-item"),
    path('delete/<str:pk>/',views.DeleteItem,name="delete-item"),
]