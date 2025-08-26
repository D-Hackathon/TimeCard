from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False,label="パスワード（変更）")
    password_confirm = forms.CharField(widget=forms.PasswordInput, required=False, label="パスワード（確認）")

    class Meta:
        model = User
        fields = ['email']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password or password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("パスワードが一致しません。")
        return cleaned_data
    
