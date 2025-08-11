from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class User(AbstractUser):
    # 内部管理用の社員コード
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # 表示/業務用の社員コード
    employee_id = models.CharField("社員ID", max_length=20, unique=True)
    email = models.EmailField("メールアドレス", unique=True)
    manager = models.ForeignKey(
        "self",
        verbose_name="上司ユーザー",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="subordinates",
    )

    created_at = models.DateTimeField("作成日時", default=timezone.now, editable=False)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    REQUIRED_FIELDS = ["email", "employee_id"]  # createsuperuserで必要な項目。

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def display_name(self) -> str:
        return self.username

    def __str__(self):
        return f"{self.display_name} ({self.employee_id})"
