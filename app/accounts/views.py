from django.views.generic import FormView, CreateView, View, DeleteView, UpdateView, ListView
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.db import models

from .forms import LoginForm, AddUserForm, EditUserForm
from .models import User

def is_manager(user):
    return User.objects.filter(manager=user).exists()

class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = LoginForm
    #　ログイン後の画面は２種類あるので、分岐させる。
    success_url = reverse_lazy("accounts:user_list") # 後ほど変更
    admin_url = reverse_lazy("accounts:add_user") #後ほど変更

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        user = form.cleaned_data['user']
        action = self.request.POST.get("action", "user")
        login(self.request, user)

        if action == "admin":
            if self._test_func(user):
                return redirect(self.admin_url)
            messages.error(self.request, "管理者機能へのアクセス権限がありません。")
            return redirect(self.success_url)
        # 通常のユーザー画面へリダイレクト
        return redirect(self.success_url)
    
    def _test_func(self, user):
        # 管理者または上司設定がされているユーザーに限定する
        # UserPassesTextMixinを使うと、通常のログインに支障が出るため、使わない。
        return user.is_superuser or User.objects.filter(manager=user).exists()
    
    def dispatch(self, request, *args, **kwargs):
        # 既にログイン済みならリダイレクト
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)
    
class LogoutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("accounts:login")
    

class AdduserView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = "accounts/add_user.html"
    form_class = AddUserForm
    success_url = reverse_lazy("accounts:add_user")

    def test_func(self):
        u = self.request.user
        # 利用者を管理者または上司設定がされているユーザーに限定する
        return u.is_superuser or User.objects.filter(manager=u).exists()

    def form_valid(self, form):
        messages.success(self.request, "ユーザーを作成しました。")
        return super().form_valid(form)

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users" #templateから呼び出す際に使用する名称
    paginate_by = 20

    def test_func(self):
        u = self.request.user
        return u.is_superuser
    def get_queryset(self):
        qs = User.objects.all().order_by("username")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                models.Q(username__icontains=q)
                | models.Q(employee_id__icontains=q)
                | models.Q(email__icontains=q)
            )
        return qs

    def handle_no_permission(self):
        messages.error(self.request, "ユーザー一覧の権限がありません。")
        return redirect("accounts:login")
    

class EditUserView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    template_name = "accounts/edit_user.html"
    form_class = EditUserForm
    success_url = reverse_lazy("accounts:add_user")

    def test_func(self):
        u = self.request.user
        return u.is_superuser or is_manager(u)

    def get_queryset(self):
        u = self.request.user
        if u.is_superuser or is_manager(u):
            return User.objects.all()       
        return User.objects.none()

    def form_valid(self, form):
        messages.success(self.request, "ユーザーを更新しました。")
        return super().form_valid(form)

    def handle_no_permission(self):
        messages.error(self.request, "ユーザー編集の権限がありません。")
        return redirect("accounts:login")
    
class DeleteUserView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = "accounts/user_delete.html"
    success_url = reverse_lazy("accounts:add_user")

    def test_func(self):
        u = self.request.user
        return u.is_superuser or is_manager(u)

    def get_queryset(self):
        u = self.request.user
        if u.is_superuser or is_manager(u):
            return User.objects.all()
        return User.objects.none()

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        #自分は削除禁止。ややこしいので。
        if obj == request.user:
            messages.error(request, "自分自身は削除できません。")
            return redirect(self.success_url)

        messages.success(request, f"ユーザー「{obj.username}」を削除しました。")
        return super().delete(request, *args, **kwargs)

    def handle_no_permission(self):
        messages.error(self.request, "ユーザー削除の権限がありません。")
        return redirect("accounts:login")