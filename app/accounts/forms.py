from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import User

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
    class Meta:
        model = User
        fields = ("username", "employee_id", "email", "manager")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 上司の候補は全社員から選べるよ
        self.fields["manager"].queryset = User.objects.all()
        self.fields["manager"].empty_label = "（上司を選択）"

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

class EmployeeSearchForm(forms.Form):
    employee_id = forms.CharField(label="社員ID", required=False)
    name = forms.CharField(label="名前", required=False)

    def clean(self):
        cleaned_data = super().clean()
        employee_id = cleaned_data.get("employee_id")
        name = cleaned_data.get("name")

        if not employee_id and not name:
            raise forms.ValidationError("社員IDまたは名前のいずれかを入力してください。")

        return cleaned_data

class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "employee_id", "email", "manager")

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()