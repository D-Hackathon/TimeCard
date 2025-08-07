from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Company

# User 管理画面カスタマイズ
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        'employee_code', 'email', 'name', 'company',
        'is_admin', 'is_staff', 'is_active'
    )
    list_filter = ('company', 'is_admin', 'is_staff', 'is_active')
    search_fields = ('employee_code', 'email', 'name')
    ordering = ('email',)

    # ユーザー作成時のフィールドセット（admin画面の「追加」時）
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'employee_code', 'email', 'name', 'company', 'manager_code',
                'password1', 'password2',
                'is_admin', 'is_staff', 'is_superuser', 'is_active',
            ),
        }),
    )

    # ユーザー編集画面のフィールドセット
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('個人情報', {'fields': ('employee_code', 'name', 'company', 'manager_code')}),
        ('アクセス権', {
            'fields': (
                'is_admin', 'is_superuser', 'is_staff', 'is_active',
                'groups', 'user_permissions'
            )
        }),
        ('日付', {'fields': ('last_login',)}),
    )


# Company 管理画面カスタマイズ
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'company_name', 'contact_person_name',
        'contact_person_email', 'contact_phone_number', 'created_at'
    )
    readonly_fields = ('id', 'created_at', 'updated_at')  
    search_fields = ('company_name', 'contact_person_name', 'contact_person_email')
    ordering = ('created_at',)
