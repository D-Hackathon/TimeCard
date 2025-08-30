# Create your views here.
from django.contrib import messages
from django.contrib.auth import get_user_model,update_session_auth_hash
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.views import View
from django.views.generic import TemplateView

from .forms import ProfileForm

User = get_user_model()

def is_manager(user):
    return User.objects.filter(manager=user).exists()

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "attendance/profile.html"
    success_url = reverse_lazy("attendance:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        password = form.cleaned_data.get("password")
        if password:
            user = self.object
            user.set_password(password)
            user.save()
            update_session_auth_hash(self.request, user)
        messages.success(self.request, "プロフィールを更新しました。")
        return response
    
class MyPageView(LoginRequiredMixin, TemplateView):
    template_name = "attendance/mypage_dummy.html"

class DailyRequestView(LoginRequiredMixin, TemplateView):
    template_name = "attendance/daily_request_dummy.html"