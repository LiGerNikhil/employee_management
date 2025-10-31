from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'employees'

urlpatterns = [
    # Root URL - redirect to login for unauthenticated users
    path('', RedirectView.as_view(url='login/', permanent=False), name='home'),

    # Authentication URLs
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),

    # Employee CRUD URLs (Admin only)
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/live-search/', views.employee_live_search, name='employee_live_search'),
    path('employees/create/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/toggle-status/', views.employee_toggle_status, name='employee_toggle_status'),
    path('employees/<int:pk>/update/', views.EmployeeUpdateView.as_view(), name='employee_update'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),

    # Employee Profile URL (Employee only)
    path('profile/', views.employee_profile, name='employee_profile'),

    # SuperAdmin Profile URLs (SuperAdmin only)
    path('admin-profile/', views.superadmin_profile, name='superadmin_profile'),
    path('admin-profile/edit/', views.superadmin_profile_edit, name='superadmin_profile_edit'),
    path('admin-profile/change-password/', views.superadmin_change_password, name='superadmin_change_password'),

    # Check-in URLs (Employee only)
    path('check-in/', views.check_in, name='check_in'),
    path('check-out/', views.check_out, name='check_out'),
    path('api/check-in-status/', views.check_in_status, name='check_in_status'),

    # Attendance URLs
    path('attendance/', views.AttendanceListView.as_view(), name='attendance_list'),  # Admin only
    path('my-attendance/', views.my_attendance_logs, name='my_attendance_logs'),  # Employee only
    path('attendance-logs/', views.admin_attendance_logs, name='admin_attendance_logs'),  # Admin only - All activity logs
    path('attendance/calendar/', views.employee_attendance_calendar, name='attendance_calendar'),  # Employee - Calendar view
    path('attendance/admin-calendar/', views.admin_attendance_calendar, name='admin_attendance_calendar'),  # Admin - Calendar view

    # Face Recognition URLs
    path('face/register/', views.face_registration, name='face_register'),
    path('face/attendance/', views.mark_attendance, name='face_attendance'),
    
    # Ticket System URLs
    path('tickets/', views.employee_tickets, name='employee_tickets'),  # Employee - My tickets
    path('tickets/create/', views.create_ticket, name='create_ticket'),  # Employee - Create ticket
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),  # Employee - View ticket
    path('tickets/<int:pk>/comment/', views.add_ticket_comment, name='add_ticket_comment'),  # Add comment
    path('tickets/manage/', views.admin_tickets, name='admin_tickets'),  # Admin - All tickets
    path('tickets/manage/<int:pk>/update/', views.admin_update_ticket, name='admin_update_ticket'),  # Admin - Update ticket

    # Password Reset URLs
    path('password-reset-request/', views.password_reset_request, name='password_reset_request'),

    # Admin Password Management URLs
    path('password-requests/', views.password_reset_requests_list, name='password_reset_requests'),
    path('password-requests/<int:request_id>/process/', views.process_password_reset_request, name='process_password_reset'),
    path('employee/<int:employee_id>/change-password/', views.employee_change_password, name='employee_change_password'),
]