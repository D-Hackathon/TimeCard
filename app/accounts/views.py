from django.views.generic import FormView, CreateView, View, DeleteView, UpdateView, ListView
from django.contrib.auth import login, logout,update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect,render
from django.contrib import messages
from django.db import models,transaction

from .forms import LoginForm, AddUserForm, EditUserForm, EmployeeIdSearchForm
from .models import User

def is_manager(user):
    return User.objects.filter(manager=user).exists()

class LoginView(FormView):
    template_name = "accounts/login_test.html"
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
    template_name = "admin/admin_employee_test.html"
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
    
class userEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = r"admin/admin_edit_employee_test.html"
    success_url = reverse_lazy("accounts:user_edit")

    def test_func(self):
        u = self.request.userC
        return u.is_superuser or is_manager(u)

    def handle_no_permission(self):
        messages.error(self.request, "ユーザー編集の権限がありません。")
        return redirect("accounts:login")

    def get_queryset(self):
        return User.objects.filter(is_active=True)

    # 社員IDで検索して、編集フォームを表示する。
    def get(self, request, *args, **kwargs):
        search_form = EmployeeIdSearchForm(request.GET or None)
        target = None
        edit_form = None

        if search_form.is_bound and search_form.is_valid(): # 社員検索フォームが送信され、かつ有効な場合
            emp_id = search_form.cleaned_data["employee_id"] 
            qs = self.get_queryset()
            target = qs.filter(employee_id=emp_id).first()

            if not target:
                messages.error(f"社員ID「{emp_id}」は存在しません。")
            else:
                edit_form = EditUserForm(instance=target) # 編集フォームの表を準備する

        return render(request, self.template_name, {
            "search_form": search_form,
            "target": target,
            "edit_form": edit_form,
        })

    # 編集フォームが送信された場合の処理
    def post(self, request):
        action = request.POST.get("action", "update")
        target_pk = request.POST.get("target")
        if not target_pk:
            messages.error(request, "対象ユーザーが指定されていません。")
            return redirect(request.path)

        target = self.get_queryset().filter(pk=target_pk).first()
        if not target:
            messages.error(request, "対象ユーザーが見つかりません。")
            return redirect(request.path)

        # 削除の場合
        if action == "delete":
            if target.pk == request.user.pk:
                #削除後の挙動などを構築するのが面倒なので、自分は削除禁止。
                messages.error(request, "自分自身は削除できません。")
                return redirect(request.path)

            try:
                # トランザクションで実装。他にも使う場所あるはず
                with transaction.atomic():
                    target.is_active = False
                    target.save(update_fields=["is_active"])
                messages.success(request, f"ユーザー「{target.username}」を削除しました。")
                return redirect(self.success_url)
            except Exception as e:
                messages.error(request, f"削除に失敗しました：{e}")
                return redirect(request.path)

        # 更新の場合
        edit_form = EditUserForm(request.POST, instance=target)
        search_form = EmployeeIdSearchForm(initial={"employee_id": target.employee_id})

        if edit_form.is_valid():
            password_changed = bool(edit_form.cleaned_data.get("password")) #パスワードが変更されたかをチェックする。
            edit_form.save()
            if password_changed and target.pk == request.user.pk:
                # 自分のパスワードを変更した場合、セッション認証を更新する。
                update_session_auth_hash(request, target)
            messages.success(request, "ユーザーを更新しました。")
            return redirect(self.success_url)

        return render(request, self.template_name, {
            "search_form": search_form,
            "target": target,
            "edit_form": edit_form,
        })