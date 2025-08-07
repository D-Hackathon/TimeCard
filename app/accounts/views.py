from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login
from django.views.generic import FormView
from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .forms import AddUserForm
from .models import User
from django.contrib import messages

from .forms import LoginForm

class LoginView(FormView):
    template_name = "accounts/login.html"  # 後ほど適切に変更
    form_class = LoginForm
    success_url = reverse_lazy('accounts:add_user')  # 後ほど適切に変更

    def form_valid(self, form):
        email = form.cleaned_data['email']
        company = form.cleaned_data['company']
        password = form.cleaned_data['password']

        user = authenticate(self.request, email=email, company=company, password=password)
        if user is not None and user.is_active:
            login(self.request, user)
            return super().form_valid(form)
        else:
            messages.error(self.request, 'ログインに失敗しました。メールアドレス、会社名、またはパスワードが正しいか確認してください。')
            return self.form_invalid(form)



class IsAdminMixin(UserPassesTestMixin):
    def test_func(self):
        # 管理者ユーザーかどうかをチェックする
        return self.request.user.is_authenticated and self.request.user.is_admin
    
class AddUserView(LoginRequiredMixin, IsAdminMixin, CreateView):
    model = User
    form_class = AddUserForm
    template_name = 'accounts/add_user.html'
    success_url = reverse_lazy('accounts:add_user')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request_user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "ユーザーを登録しました。引き続き追加できます。")
        return redirect(self.success_url)