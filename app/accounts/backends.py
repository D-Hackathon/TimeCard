from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class EmailCompanyBackend(ModelBackend):
    """
    カスタム認証バックエンド：管理者画面ではcompanyを不要とした。我々管理者のみ管理画面を使うため。
    - 管理画面からのログイン：email + password
    - 通常ログイン画面：email + company + password
    """
    def authenticate(self, request, email=None, password=None, company=None, **kwargs):
        try:
            if request and request.path.startswith('/admin/'):
                # 管理画面ログイン：email のみで認証
                user = UserModel.objects.get(email=email)
            else:
                # 通常ログイン：email + company が必須
                if not company:
                    return None  # companyが指定されていない場合は拒否
                user = UserModel.objects.get(email=email, company=company)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None