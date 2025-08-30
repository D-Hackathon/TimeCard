from django.urls import path
from .views import ProfileUpdateView,MyPageView,DailyRequestView

app_name = "attendance"

urlpatterns = [
    path("profile/", ProfileUpdateView.as_view(), name="profile"),
    path("mypage/", MyPageView.as_view(), name="mypage"),
    path("daily_request/", DailyRequestView.as_view(), name="daily_request"),
]