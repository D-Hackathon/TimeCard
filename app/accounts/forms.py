from django import forms
from django.contrib.auth import authenticate,get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import User

User = get_user_model()

def is_manager(user):
    return User.objects.filter(manager=user).exists()

class LoginForm(forms.Form):
    email = forms.EmailField(label="メールアドレス")
    password = forms.CharField(label="パスワード", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(request=self.request, email=email, password=password)
            if user is None:
                raise forms.ValidationError("メールアドレスまたはパスワードが正しくありません。")
            cleaned_data['user'] = user

        return cleaned_data

class AddUserForm(UserCreationForm):
    email_confirm = forms.EmailField(label="メールアドレス確認")
    manager_employee_id = forms.CharField(
        label="上司ID",
        required=False,
    )

    class Meta:
        model = User
        fields = ("username", "employee_id", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ラベル調整
        self.fields["password1"].label = "初期パスワード"
        self.fields["password2"].label = "初期パスワード 確認"

        # 表示順（テンプレの順番に固定）
        field_order = [
            "employee_id",
            "username",
            "email",
            "email_confirm",
            "manager_employee_id",
            "password1",
            "password2",
        ]
        self.order_fields(field_order)

        # プレースホルダ（任意）
        for name, ph in [
            ("employee_id", "入力してください"),
            ("username", "入力してください"),
            ("email", "入力してください"),
            ("email_confirm", "入力してください"),
            ("manager_employee_id", "入力してください"),
            ("password1", "入力してください"),
            ("password2", "入力してください"),
        ]:
            self.fields[name].widget.attrs.update({"placeholder": ph})


    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    # メールと上司IDの検証工程を新設
    def clean(self):
        cleaned = super().clean()

        email = cleaned.get("email")
        email_confirm = cleaned.get("email_confirm")
        if email and email_confirm and email != email_confirm:
            self.add_error("email_confirm", "メールアドレスが一致しません。")

        # 上司ID。手入力に対応したことにより新設。ややこしい。。。
        # 手入力された社員IDから User を取得。見つかったら一旦変数に格納。
        manager_code = cleaned.get("manager_employee_id")
        self._manager_id = None
        if manager_code:
            mgr = User.objects.filter(employee_id=manager_code).first()
            if not mgr:
                self.add_error("manager_employee_id", "指定した上司ID（社員ID）が見つかりません。")
            else:
                self._manager_id = mgr

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if getattr(self, "_manager_id", None):
            user.manager = self._manager_id

        if commit:
            user.save()
        return user
    
class EditUserForm(forms.ModelForm):
    email_confirm = forms.EmailField(
        label="メールアドレス確認", required=False,
        widget=forms.EmailInput()
    )
    password = forms.CharField(
        label="パスワード変更", required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="パスワード確認", required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    manager_employee_id = forms.CharField(
        label="上司ID（社員ID）", required=False,
        help_text=None,
        widget=forms.TextInput()
    )

    class Meta:
        model = User
        fields = (
            "employee_id",
            "username",
            "email",
            "email_confirm",
            "manager_employee_id",
            "password",
            "password_confirm",
        )
        labels = {"username": "氏名"}
        widgets = {
            "employee_id": forms.TextInput(),
            "username": forms.TextInput(),
            "email": forms.EmailInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.help_text = None
            
        self.fields["employee_id"].widget.attrs.update({
            "placeholder": "入力してください",
            "class": "form-control",
        })
        self.fields["username"].widget.attrs.update({
            "placeholder": "入力してください",
            "class": "form-control",
        })
        self.fields["email"].widget.attrs.update({
            "placeholder": "入力してください",
            "class": "form-control",
        })
        self.fields["email_confirm"].widget.attrs.update({
            "placeholder": "入力してください",
            "class": "form-control",
        })
        self.fields["manager_employee_id"].widget.attrs.update({
            "placeholder": "入力してください",
            "class": "form-control",
        })
        self.fields["password"].widget.attrs.update({
            "placeholder": "入力してください",
            "class": "form-control",
        })
        self.fields["password_confirm"].widget.attrs.update({
            "placeholder": "入力してください",
            "class": "form-control",
        })

        # 既存データを初期値に設定
        if self.instance and self.instance.pk and self.instance.manager:
            self.fields["manager_employee_id"].initial = self.instance.manager.employee_id
        if self.instance and self.instance.pk:
            self.fields["email_confirm"].initial = self.instance.email

        # 順序を固定
        self.order_fields([
            "employee_id",
            "username",
            "email",
            "email_confirm",
            "manager_employee_id",
            "password",
            "password_confirm",
        ])
        self._manager_obj = None

    def clean_email(self):
        email = self.cleaned_data.get("email")
        return email.strip().lower() if email else email

    def clean_email_confirm(self):
        email_confirm = self.cleaned_data.get("email_confirm")
        return email_confirm.strip().lower() if email_confirm else email_confirm

    def clean(self):
        cleaned = super().clean()

        email = cleaned.get("email")
        email_confirm = cleaned.get("email_confirm")
        current = getattr(self.instance, "email", None)
        if current:
            current = current.strip().lower()

        # emailが変更されたかどうか
        email_changed = (email is not None) and (email != current)

        if email_changed:
            if not email_confirm:
                self.add_error("email_confirm", "メールアドレス（確認）を入力してください。")
            elif email_confirm != email:
                self.add_error("email_confirm", "メールアドレスが一致しません。")
        else:
            if email_confirm and email_confirm != (email or current):
                self.add_error("email_confirm", "メールアドレスが一致しません。")

        # パスワード一致チェック
        pw, pw2 = cleaned.get("password"), cleaned.get("password_confirm")
        if pw or pw2:
            if not pw or not pw2:
                self.add_error("password_confirm", "パスワード（変更）と（確認）を両方入力してください。")
            elif pw != pw2:
                self.add_error("password_confirm", "パスワードが一致しません。")

        # 上司社員IDからUserを検索
        code = cleaned.get("manager_employee_id")
        self._manager_obj = None
        if code:
            mgr = User.objects.filter(employee_id=code, is_active=True).first()
            if not mgr:
                self.add_error("manager_employee_id", "指定した上司ID（社員ID）が見つかりません。")
            else:
                if self.instance and self.instance.pk and mgr.pk == self.instance.pk:
                    self.add_error("manager_employee_id", "自分自身を上司に設定することはできません。")
                else:
                    self._manager_obj = mgr

        return cleaned
