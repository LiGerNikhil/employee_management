from django.contrib import admin
from .models import Employee, Attendance


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'full_name', 'email', 'contact', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'full_name', 'email', 'contact')
    ordering = ('name', 'full_name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'full_name', 'email', 'contact')
        }),
        ('Financial Information', {
            'fields': ('aadhar_card_number', 'account_number', 'ifsc_code', 'pan_card')
        }),
        ('Profile', {
            'fields': ('profile_picture',)
        }),
        ('Account', {
            'fields': ('user',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'check_in_time', 'get_date')
    list_filter = ('check_in_time',)
    search_fields = ('employee__name', 'employee__full_name', 'employee__email')
    ordering = ('-check_in_time',)
    readonly_fields = ('check_in_time',)

    fieldsets = (
        ('Attendance Information', {
            'fields': ('employee', 'check_in_time', 'check_in_photo')
        }),
    )

    def get_date(self, obj):
        return obj.date
    get_date.short_description = 'Date'
    get_date.admin_order_field = 'date'
