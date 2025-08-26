from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Min, Max, Count, Q
from django.contrib.auth import update_session_auth_hash
from django.utils.dateparse import parse_date
from django.http import Http404

from accounts.forms import EmployeeIdSearchForm, EditUserForm
from accounts.models import User
from .forms import EmployeeIDSearchForm
from attendances.models import WorkLog, ApprovalStatus, WorkLogStatusHistory
from django.utils import timezone
from datetime import timedelta

def is_manager(user):
    return User.objects.filter(manager=user).exists()

class UserEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = r"admin/admin_edit_employee_test.html"
    success_url = reverse_lazy("managers:user_edit")

    def test_func(self):
        u = self.request.user
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

        if search_form.is_bound and search_form.is_valid():  # 社員検索フォームが送信され、かつ有効な場合
            emp_id = search_form.cleaned_data["employee_id"]
            qs = self.get_queryset()
            target = qs.filter(employee_id=emp_id).first()

            if not target:
                messages.error(request, f"社員ID「{emp_id}」は存在しません。")
            else:
                edit_form = EditUserForm(instance=target)  # 編集フォームの表を準備する

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
                messages.error(request, "自分自身は削除できません。")
                return redirect(request.path)

            try:
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
            password_changed = bool(edit_form.cleaned_data.get("password"))
            edit_form.save()
            if password_changed and target.pk == request.user.pk:
                update_session_auth_hash(request, target)
            messages.success(request, "ユーザーを更新しました。")
            return redirect(self.success_url)

        return render(request, self.template_name, {
            "search_form": search_form,
            "target": target,
            "edit_form": edit_form,
        })

class TeamWorkLogAdminView(LoginRequiredMixin,UserPassesTestMixin, View):
    template_name = r"admin/admin_setting_test.html"

    def test_func(self):
        u = self.request.user
        return u.is_superuser or is_manager(u)

    def handle_no_permission(self):
        messages.error(self.request, "閲覧権限がありません。")
        return redirect("accounts:login")

    def allowed_users(self):
        """管理者=全員／マネージャー=自分の部下のみ"""
        u = self.request.user
        if u.is_superuser:
            return User.objects.filter(is_active=True)
        return User.objects.filter(is_active=True, manager=u)

    def get(self, request):
        form = EmployeeIdSearchForm(request.GET or None)
        target_user, logs = None, []
        year = month = None
        total_minutes = 0
        days = []

        if form.is_bound and form.is_valid():
            emp_id = form.cleaned_data["employee_id"]
            qs = self.allowed_users()
            target_user = qs.filter(employee_id=emp_id).first()
            if not target_user:
                messages.error(request, f"社員ID「{emp_id}」は存在しないか、閲覧権限がありません。")
                return redirect(request.path)

            # 対象社員の最新の勤怠月
            latest_log = WorkLog.objects.filter(user=target_user).order_by("-work_date").first()
            if latest_log:
                year, month = latest_log.work_date.year, latest_log.work_date.month

                logs = (
                    WorkLog.objects
                    .filter(user=target_user, work_date__year=year, work_date__month=month)
                    .select_related("status")
                    .order_by("work_date", "start_time")
                )
                total_minutes = sum(w.minutes for w in logs)

                # ▼ ここを DB 集約に変更（1日1行、最古開始/最新終了、申請前除外も対応可）
                daily_qs = (
                    WorkLog.objects
                    .filter(user=target_user, work_date__year=year, work_date__month=month)
                    .values("work_date")
                    .annotate(
                        start=Min("start_time"),
                        end=Max("end_time"),
                        pending_count=Count("id", filter=Q(status__name="申請中")),
                        with_status_count=Count("id", filter=Q(status__isnull=False)),
                    )
                    .order_by("work_date")
                )

                days = []
                for row in daily_qs:
                    # ステータス表示ルール：
                    # 1) 申請中が1件でもあれば「申請中あり」
                    # 2) 申請中が無く、何かしらのステータスが付いていれば「対応済み」
                    # 3) どれもなければ「—」（未申請）
                    if row["pending_count"] > 0:
                        status_label = "申請中あり"
                    elif row["with_status_count"] > 0:
                        status_label = "対応済み"
                    else:
                        status_label = "—"  # 未申請のみ
                    days.append({
                        "date": row["work_date"],
                        "start": row["start"],
                        "end": row["end"],
                        "status_label": status_label,
                    })
            else:
                messages.info(request, "勤怠明細がまだありません。")

        return render(request, self.template_name, {
            "form": form,
            "target_user": target_user,
            "days": days,
            "total_minutes": total_minutes,
            "year": year, "month": month,
        })
    
class TeamWorkLogDayDetailView(LoginRequiredMixin,UserPassesTestMixin, View):
    template_name = r"admin/admin_daily_request_test.html"
    
    def test_func(self):
        u = self.request.user
        return u.is_superuser or is_manager(u)

    def handle_no_permission(self):
        messages.error(self.request, "閲覧権限がありません。")
        return redirect("accounts:login")

    def allowed_users(self):
        u = self.request.user
        if u.is_superuser:
            return User.objects.filter(is_active=True)
        return User.objects.filter(is_active=True, manager=u)
    
    def get(self, request, employee_id, ymd):
        target_user = self.allowed_users().filter(employee_id=employee_id).first()
        if not target_user:
            messages.error(request, f"社員ID「{employee_id}」は存在しないか、閲覧権限がありません。")
            return redirect("managers:admin_worklogs")
        
        day = parse_date(ymd)
        if not day:
            raise Http404("不正な日付です。yyyy-mm-dd形式で指定してください。")
        
        logs = (WorkLog.objects
                .filter(user=target_user, work_date=day)
                .select_related("status")
                .order_by("start_time"))
        
        total_minutes = sum(log.minutes for log in logs)

        return render(request, self.template_name, {
            "target_user": target_user,
            "day": day,
            "logs": logs,
            "total_minutes": total_minutes,
        })
    
    def post(self, request, employee_id: str, ymd: str):
        target_user = self.allowed_users().filter(employee_id=employee_id).first()
        if not target_user:
            messages.error(request, f"社員ID「{employee_id}」は存在しないか、閲覧権限がありません。")
            return redirect("managers:admin_worklogs")

        day = parse_date(ymd)
        if not day:
            raise Http404("日付形式が不正です。")

        # 必要なマスタをチェックする（本番環境用）
        pending  = ApprovalStatus.objects.filter(name="申請中").first()
        approved = ApprovalStatus.objects.filter(name="承認済み").first()
        rejected = ApprovalStatus.objects.filter(name="否認").first()
        if not all([pending, approved, rejected]):
            messages.error(request, "承認マスタ（申請中/承認済み/否認）を登録してください。")
            return redirect("managers:admin_worklogs_day", employee_id=employee_id, ymd=ymd)

        # POST のキーから decision_* を拾って一括処理
        to_approve_ids = []
        to_reject_ids = []
        for key, val in request.POST.items():
            if not key.startswith("decision_"):
                continue
            try:
                wl_id = key.split("_", 1)[1]
            except IndexError:
                continue
            decision = (val or "").strip()
            if decision == "approve":
                to_approve_ids.append(wl_id)
            elif decision == "reject":
                to_reject_ids.append(wl_id)

        if not to_approve_ids and not to_reject_ids:
            messages.info(request, "実行対象が選択されていません。")
            return redirect("managers:admin_worklogs_day", employee_id=employee_id, ymd=ymd)

        qs_base = WorkLog.objects.filter(
            user=target_user,
            work_date=day,
            status_id=pending.id,
        )

        approved_count = rejected_count = skipped_count = 0

        # 承認
        if to_approve_ids:
            for wl in qs_base.filter(pk__in=to_approve_ids).select_related("status"):
                wl.status = approved
                wl.confirmed_by = request.user
                wl.confirmed_at = timezone.now()
                wl.save(update_fields=["status", "confirmed_by", "confirmed_at", "updated_at"])
                WorkLogStatusHistory.objects.create(
                    work_log=wl, from_status=pending, to_status=approved, changed_by=request.user
                )
                approved_count += 1
            # 既に申請中でない等により外れたIDはスキップ扱い
            skipped_count += max(0, len(to_approve_ids) - approved_count)

        # 差し戻し
        if to_reject_ids:
            for wl in qs_base.filter(pk__in=to_reject_ids).select_related("status"):
                wl.status = rejected
                wl.confirmed_by = request.user
                wl.confirmed_at = timezone.now()
                wl.save(update_fields=["status", "confirmed_by", "confirmed_at", "updated_at"])
                WorkLogStatusHistory.objects.create(
                    work_log=wl, from_status=pending, to_status=rejected, changed_by=request.user
                )
                rejected_count += 1
            skipped_count += max(0, len(to_reject_ids) - rejected_count)

        # サマリ表示
        parts = []
        if approved_count:
            parts.append(f"承認 {approved_count} 件")
        if rejected_count:
            parts.append(f"差し戻し {rejected_count} 件")
        messages.success(request, " / ".join(parts) if parts else "処理対象がありませんでした。")

        return redirect("managers:admin_worklogs_day", employee_id=employee_id, ymd=ymd)


