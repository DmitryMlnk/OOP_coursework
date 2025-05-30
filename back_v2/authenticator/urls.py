from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

urlpatterns = [
    path('register/', views.Register.as_view(), name='register'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('me/', views.GetCurrentUser.as_view(), name='get_current_user'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]