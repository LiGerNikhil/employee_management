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
    path('employees/create/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/update/', views.EmployeeUpdateView.as_view(), name='employee_update'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),

    # Employee Profile URL (Employee only)
    path('profile/', views.employee_profile, name='employee_profile'),

    # Check-in URLs (Employee only)
    path('check-in/', views.check_in, name='check_in'),
    path('api/check-in-status/', views.check_in_status, name='check_in_status'),

    # Attendance URLs (Admin only)
    path('attendance/', views.AttendanceListView.as_view(), name='attendance_list'),
]
