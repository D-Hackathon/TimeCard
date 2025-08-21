from django.urls import path
from .views import ProfileUpdateView

app_name = "attendance"

urlpatterns = [
    path("profile/", ProfileUpdateView.as_view(), name="profile"),
    path("mypage/", ProfileUpdateView.as_view(), name="mypage"), #profileのテスト用に設定。本番環境に繋ぎ直してください。
]