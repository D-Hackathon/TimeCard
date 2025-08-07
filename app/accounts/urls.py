from django.urls import path
from .views import AddUserView, LoginView

app_name = 'accounts' 

urlpatterns = [
    path('add/', AddUserView.as_view(), name='add_user'),
    path('login/', LoginView.as_view(), name='login'),
]