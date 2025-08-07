from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm

User = get_user_model()

class LoginForm(forms.Form):
    company = forms.CharField(label='会社ID')
    email = forms.EmailField(label='メールアドレス')
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)

class AddUserForm(forms.ModelForm):
    email_confirm = forms.EmailField(label='メールアドレス（確認用）')
    password = forms.CharField(label='初期パスワード', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='初期パスワード（確認用）', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['employee_code', 'name', 'email', 'manager_code']

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        email_confirm = cleaned_data.get("email_confirm")
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        manager_code = cleaned_data.get("manager_code")

        # パスワード確認
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'パスワードが一致しません。')

        # メール確認
        if email and email_confirm and email != email_confirm:
            self.add_error('email_confirm', 'メールアドレスが一致しません。')

        # manager_code 存在チェック
        if manager_code:
            try:
                manager = User.objects.get(
                    employee_code=manager_code,
                    company=self.request_user.company,
                    is_active=True
                )
            except User.DoesNotExist:
                self.add_error('manager_code', '指定された上司の社員IDは存在しないか、退職済みです。')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.company = self.request_user.company
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
    