from django.urls import path
from .views import LoginView, LogoutView, AdduserView, UserListView, EditUserView, DeleteUserView, userEditView

app_name = "accounts"
urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("user/new/", AdduserView.as_view(), name="add_user"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("user/<uuid:pk>/edit/", EditUserView.as_view(), name="edit_user"),
    path("user/<uuid:pk>/delete/", DeleteUserView.as_view(), name="delete_user"),
    path("admin/users/edit/", userEditView.as_view(), name="user_edit"),
]