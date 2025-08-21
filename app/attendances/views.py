# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model,update_session_auth_hash
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView

from .forms import ProfileForm



class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "attendance/profile_test.html"
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