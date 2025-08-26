from django.contrib import admin
from django.utils.timezone import localtime
from .models import ApprovalStatus, WorkLog, WorkLogStatusHistory, WorkLogChangeHistory

@admin.register(ApprovalStatus)
class ApprovalStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("id",)

@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = (
        "user", "work_date", "start_hm", "end_hm", "status",
        "confirmed_by", "confirmed_at",
    )
    list_filter = ("status", "work_date")
    date_hierarchy = "work_date"
    search_fields = ("user__username", "user__employee_id", "user__email")
    autocomplete_fields = ("user", "confirmed_by")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-work_date", "start_time")

    def start_hm(self, obj):
        return localtime(obj.start_time).strftime("%H:%M")
    start_hm.short_description = "開始"

    def end_hm(self, obj):
        return localtime(obj.end_time).strftime("%H:%M") if obj.end_time else "—"
    end_hm.short_description = "終了"

@admin.register(WorkLogStatusHistory)
class WorkLogStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("work_log", "from_status", "to_status", "changed_by", "changed_at")
    list_filter = ("from_status", "to_status", "changed_at")
    autocomplete_fields = ("work_log", "changed_by")
    readonly_fields = ("changed_at",)

@admin.register(WorkLogChangeHistory)
class WorkLogChangeHistoryAdmin(admin.ModelAdmin):
    list_display = ("work_log", "changed_by", "changed_at",
                    "before_start_time", "before_end_time",
                    "after_start_time", "after_end_time")
    list_filter = ("changed_at",)
    autocomplete_fields = ("work_log", "changed_by")
    readonly_fields = ("changed_at",)
