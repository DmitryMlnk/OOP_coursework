from django.urls import path
from . import views

urlpatterns = [
    path('', views.RoomList.as_view(), name='room_list'),
    path('create/', views.RoomCreate.as_view(), name='room_create'),
    path('join/', views.RoomJoin.as_view(), name='room_join'),
    path('leave/', views.RoomLeave.as_view(), name='room_leave'),
]