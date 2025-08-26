from django.urls import path
from .views import UserEditView, TeamWorkLogAdminView, TeamWorkLogDayDetailView

app_name = "managers"
urlpatterns = [
    path("users/edit/", UserEditView.as_view(), name="user_edit"),
    path("worklogs/", TeamWorkLogAdminView.as_view(), name="admin_worklogs"),
    path("worklogs/<str:employee_id>/<slug:ymd>/",TeamWorkLogDayDetailView.as_view(),name="admin_worklogs_day"),
]
