from django.contrib import admin
from .models import Employee, Attendance, AttendanceLog, Ticket, TicketComment


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


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('employee', 'action', 'success', 'timestamp', 'ip_address', 'confidence')
    list_filter = ('action', 'success', 'failure_reason', 'timestamp')
    search_fields = ('employee__name', 'employee__email', 'ip_address', 'notes')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('Log Information', {
            'fields': ('employee', 'action', 'success', 'timestamp')
        }),
        ('Details', {
            'fields': ('failure_reason', 'confidence', 'attendance')
        }),
        ('Technical Information', {
            'fields': ('ip_address', 'user_agent', 'notes'),
            'classes': ('collapse',)
        }),
    )


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'comment', 'is_internal', 'created_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'employee', 'subject', 'category', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('ticket_number', 'subject', 'employee__name', 'employee__email', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('ticket_number', 'created_at', 'updated_at', 'resolved_at')
    inlines = [TicketCommentInline]
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_number', 'employee', 'subject', 'description', 'attachment')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'status')
        }),
        ('Resolution', {
            'fields': ('resolved_by', 'resolved_at', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'comment_preview', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('ticket__ticket_number', 'user__username', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'
