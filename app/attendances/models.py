from django.db import models
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

User = settings.AUTH_USER_MODEL

# 承認ステータス（マスタ）
class ApprovalStatus(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField("ステータス名", max_length=50, unique=True)

    class Meta:
        db_table = "approval_statuses"
        verbose_name = "承認ステータス"
        verbose_name_plural = "承認ステータス"

    def __str__(self) -> str:
        return f"{self.id}:{self.name}"


# 勤怠履歴（打刻明細）
class WorkLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        verbose_name="ユーザー",
        related_name="work_logs",
        on_delete=models.PROTECT,
    )
    work_date = models.DateField("勤怠日")
    start_time = models.DateTimeField("開始時刻")
    end_time = models.DateTimeField("終了時刻", null=True, blank=True)

    status = models.ForeignKey(
        ApprovalStatus,
        verbose_name="承認ステータス",
        related_name="work_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    confirmed_by = models.ForeignKey(
        User,
        verbose_name="承認者",
        related_name="approved_work_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    confirmed_at = models.DateTimeField("承認日時", null=True, blank=True)

    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        db_table = "work_logs"
        verbose_name = "打刻明細"
        verbose_name_plural = "打刻明細"
        indexes = [
            models.Index(fields=["user", "work_date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} {self.work_date} {self.start_time:%H:%M}-{self.end_time:%H:%M if self.end_time else '--:--'}"

    def clean(self):
        if self.end_time and self.end_time < self.start_time:
            raise ValidationError({"end_time": "終了時刻は開始時刻以降である必要があります。"})

    @property
    def minutes(self) -> int:
        if not self.end_time:
            return 0
        delta = self.end_time - self.start_time
        return max(0, int(delta.total_seconds() // 60))

    @property
    def timedelta(self) -> timedelta:
        return timedelta(minutes=self.minutes)


# 打刻ステータス履歴
class WorkLogStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_log = models.ForeignKey(
        WorkLog,
        verbose_name="対象打刻",
        related_name="status_histories",
        on_delete=models.CASCADE,
    )
    from_status = models.ForeignKey(
        ApprovalStatus,
        verbose_name="変更前ステータス",
        related_name="from_histories",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    to_status = models.ForeignKey(
        ApprovalStatus,
        verbose_name="変更後ステータス",
        related_name="to_histories",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    changed_by = models.ForeignKey(
        User,
        verbose_name="操作ユーザー",
        related_name="worklog_status_changes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    changed_at = models.DateTimeField("変更日時", auto_now_add=True)
    reason = models.TextField("否認理由/メモ", blank=True, default="")

    class Meta:
        db_table = "work_log_status_history"
        verbose_name = "打刻ステータス履歴"
        verbose_name_plural = "打刻ステータス履歴"
        indexes = [
            models.Index(fields=["work_log", "changed_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.work_log_id} {self.from_status} -> {self.to_status} @ {self.changed_at}"


# 打刻編集履歴
class WorkLogChangeHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_log = models.ForeignKey(
        WorkLog,
        verbose_name="対象打刻",
        related_name="change_histories",
        on_delete=models.CASCADE,
    )
    changed_by = models.ForeignKey(
        User,
        verbose_name="編集者",
        related_name="worklog_edit_changes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    changed_at = models.DateTimeField("編集日時", auto_now_add=True)

    before_start_time = models.DateTimeField("変更前:開始", null=True, blank=True)
    before_end_time = models.DateTimeField("変更前:終了", null=True, blank=True)
    after_start_time = models.DateTimeField("変更後:開始", null=True, blank=True)
    after_end_time = models.DateTimeField("変更後:終了", null=True, blank=True)

    class Meta:
        db_table = "work_log_change_history"
        verbose_name = "打刻編集履歴"
        verbose_name_plural = "打刻編集履歴"
        indexes = [
            models.Index(fields=["work_log", "changed_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.work_log_id} edited @ {self.changed_at}"