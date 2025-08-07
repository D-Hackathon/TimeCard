from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid



class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255, verbose_name='会社名')
    address = models.CharField(max_length=255)
    contact_person_name = models.CharField(max_length=255)
    contact_person_email = models.EmailField()
    contact_phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, company=None, **extra_fields):
        if not email:
            raise ValueError('メールアドレスは必須です')
        if not company and not extra_fields.get("is_superuser", False):
            raise ValueError('会社IDは必須です')

        email = self.normalize_email(email)
        user = self.model(email=email, company=company, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('スーパーユーザーは is_staff=True にする必要があります。')
        if not extra_fields.get('is_superuser'):
            raise ValueError('スーパーユーザーは is_superuser=True にする必要があります。')

        return self.create_user(email, password, company=None, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_code = models.CharField(max_length=20, verbose_name='社員ID')
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        null=True, blank=True  # superuser 用
    )
    name = models.CharField(max_length=255, verbose_name='氏名')
    email = models.EmailField(verbose_name='メールアドレス')
    is_admin = models.BooleanField(default=False, verbose_name='管理者権限')
    is_active = models.BooleanField(default=True, verbose_name='在職フラグ')
    manager_code = models.CharField(max_length=20, null=True, blank=True, verbose_name='上司の社員ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    # 認証に usernameを使わないようにするためにNoneに変更
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        unique_together = [
            ('email', 'company'),            # 同一会社内でメールアドレスはユニーク
            ('employee_code', 'company')     # 同一会社内で社員IDもユニーク
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"