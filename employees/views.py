from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Min, Max
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

import cv2
import numpy as np
import face_recognition
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image
import base64

from .models import Employee, Attendance
from django.contrib.auth.forms import PasswordChangeForm

from .forms import EmployeeForm, EmployeeUpdateForm, SuperAdminProfileForm
from .face_utils import (
    extract_face_encoding,
    extract_face_encoding_from_file,
    compare_faces,
    get_match_tolerance,
    get_strict_match_tolerance,
    find_best_face_match,
)
from django.db import transaction

from django.contrib.auth.hashers import make_password
from .models import PasswordResetRequest

from datetime import datetime, date, timedelta


def get_working_days(start_date: date, end_date: date) -> int:
    """Return count of working days between two dates inclusive, excluding Sundays and 1st/3rd/5th Saturdays."""

    if start_date > end_date:
        return 0

    total_days = 0
    current = start_date
    while current <= end_date:
        weekday = current.weekday()  # Monday=0 ... Sunday=6

        if weekday == 6:
            current += timedelta(days=1)
            continue

        if weekday == 5:
            saturday_count = 0
            for day in range(1, current.day + 1):
                if datetime(current.year, current.month, day).weekday() == 5:
                    saturday_count += 1

            if saturday_count in {1, 3, 5}:
                current += timedelta(days=1)
                continue

        total_days += 1
        current += timedelta(days=1)

    return total_days


def calculate_attendance_metrics(attendance_qs, start_date: date, end_date: date):
    """Calculate working day metrics for attendance records within provided date range."""

    working_days = get_working_days(start_date, end_date)

    present = attendance_qs.filter(check_out_time__isnull=False, half_day=False).count()
    half_days = attendance_qs.filter(check_out_time__isnull=False, half_day=True).count()

    absent = max(working_days - (present + half_days), 0)

    attendance_percentage = 0
    if working_days:
        attendance_percentage = ((present + (half_days * 0.5)) / working_days) * 100

    return {
        'total_working_days': working_days,
        'present_days': present,
        'half_day_days': half_days,
        'absent_days': absent,
        'attendance_percentage': round(attendance_percentage, 1),
    }


# Helper functions to check user roles
def is_superadmin(user):
    """Check if user is a superadmin (only true superusers, not staff)"""
    return user.is_superuser


def is_employee(user):
    """Check if user is an employee"""
    return hasattr(user, 'employee_profile')


# Authentication Views
class LoginView(TemplateView):
    """Custom login view that handles both admin and employee logins"""

    def get(self, request):
        if request.user.is_authenticated:
            return self.redirect_authenticated_user(request.user)
        return render(request, 'employees/auth/login.html', self.get_context_data())

    def post(self, request):
        username = request.POST.get('email-username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Please provide both email/username and password.')
            return render(request, 'employees/auth/login.html', self.get_context_data())

        # Try to authenticate with username first, then email
        user = None

        # First try direct username authentication
        user = authenticate(request, username=username, password=password)

        # If that fails, try email authentication
        if not user:
            try:
                # Find user by email
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return self.redirect_authenticated_user(user)
        else:
            context = self.get_context_data()
            context.update({
                'login_error': 'Invalid email/username or password.',
                'entered_username': username,
            })
            return render(request, 'employees/auth/login.html', context)

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            'layout_path': TemplateHelper.set_layout('layout_blank.html', context),
        })
        return context

    def redirect_authenticated_user(self, user):
        """Redirect user based on their role"""
        # Check if there's a 'next' parameter in the request
        next_url = self.request.POST.get('next') or self.request.GET.get('next')

        if next_url:
            # Redirect to the page they were trying to access
            return redirect(next_url)
        else:
            # Default redirects based on role
            if is_superadmin(user):
                return redirect('employees:admin_dashboard')
            elif is_employee(user):
                return redirect('employees:employee_dashboard')
            else:
                return redirect('/')


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('/')  # Redirect to home/login page


# Dashboard Views
@login_required
@user_passes_test(is_superadmin)
def admin_dashboard(request):
    """Admin dashboard view with comprehensive statistics"""
    from django.utils import timezone
    from django.db.models import Count, Q
    from datetime import timedelta
    from employees.models import Ticket, AttendanceLog
    
    today = timezone.now().date()
    now = timezone.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Employee Statistics
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(user__is_active=True).count()
    
    # Attendance Statistics
    today_checkins = Attendance.objects.filter(date=today).count()
    today_checkouts = Attendance.objects.filter(date=today, check_out_time__isnull=False).count()
    incomplete_today = today_checkins - today_checkouts
    
    # Weekly attendance trend
    week_attendance = []
    for i in range(7):
        date = today - timedelta(days=6-i)
        count = Attendance.objects.filter(date=date).count()
        week_attendance.append({
            'date': date.strftime('%a'),
            'count': count
        })
    
    # Ticket Statistics
    open_tickets = Ticket.objects.filter(status='open').count()
    urgent_tickets = Ticket.objects.filter(priority='urgent', status__in=['open', 'in_progress']).count()
    resolved_today = Ticket.objects.filter(resolved_at__date=today).count()
    
    # Password Reset Requests
    pending_password_requests = PasswordResetRequest.objects.filter(status='pending').count()
    recent_password_requests = PasswordResetRequest.objects.filter(
        status='pending'
    ).select_related('employee').order_by('-created_at')[:5]
    
    # Recent Activity Logs
    recent_failures = AttendanceLog.objects.filter(
        success=False
    ).select_related('employee').order_by('-timestamp')[:5]
    
    # Top performers (most check-ins this month)
    top_performers = Employee.objects.annotate(
        checkin_count=Count('attendance_records', filter=Q(attendance_records__date__gte=month_ago))
    ).order_by('-checkin_count')[:5]
    
    # Recent tickets
    recent_tickets = Ticket.objects.select_related('employee').order_by('-created_at')[:5]
    
    # Today's attendance
    today_attendance = Attendance.objects.filter(
        date=today
    ).select_related('employee').order_by('-check_in_time')[:10]
    
    # Recent employees
    recent_employees = Employee.objects.order_by('-created_at')[:5]
    
    # Monthly statistics
    month_checkins = Attendance.objects.filter(date__gte=month_ago).count()
    month_tickets = Ticket.objects.filter(created_at__gte=month_ago).count()
    
    # Attendance rate
    expected_checkins = total_employees * 30  # Assuming 30 days
    attendance_rate = (month_checkins / expected_checkins * 100) if expected_checkins > 0 else 0
    
    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'total_employees': total_employees,
        'active_employees': active_employees,
        'today_checkins': today_checkins,
        'today_checkouts': today_checkouts,
        'incomplete_today': incomplete_today,
        'open_tickets': open_tickets,
        'urgent_tickets': urgent_tickets,
        'resolved_today': resolved_today,
        'pending_password_requests': pending_password_requests,
        'recent_password_requests': recent_password_requests,
        'month_checkins': month_checkins,
        'month_tickets': month_tickets,
        'attendance_rate': round(attendance_rate, 1),
        'week_attendance': week_attendance,
        'recent_failures': recent_failures,
        'top_performers': top_performers,
        'recent_tickets': recent_tickets,
        'today_attendance': today_attendance,
        'recent_employees': recent_employees,
        'today': today,
        'now': now,
    })
    return render(request, 'employees/dashboard/admin_dashboard.html', context)


@login_required
@user_passes_test(is_employee)
def employee_dashboard(request):
    """Employee dashboard view"""
    employee = request.user.employee_profile
    from django.utils import timezone
    from calendar import monthcalendar, month_name
    import datetime

    # Get current month and year
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # Get all attendance for current month
    month_attendance = Attendance.objects.filter(
        employee=employee,
        date__year=current_year,
        date__month=current_month
    ).order_by('date')

    # Create calendar data
    cal = monthcalendar(current_year, current_month)
    month_name_str = month_name[current_month]

    # Create attendance dictionary for quick lookup
    attendance_dict = {}
    for attendance in month_attendance:
        attendance_dict[attendance.date.day] = attendance

    # Create calendar grid with attendance data
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({
                    'day': None, 
                    'attendance': None, 
                    'is_today': False,
                    'status': 'empty'
                })
            else:
                day_date = datetime.date(current_year, current_month, day)
                attendance = attendance_dict.get(day)
                is_today = day_date == today
                is_past = day_date < today
                is_future = day_date > today
                
                # Determine status
                if is_today:
                    if attendance:
                        if attendance.check_out_time:
                            status = 'today-complete'
                        else:
                            status = 'today-incomplete'
                    else:
                        status = 'today-absent'
                elif attendance:
                    if attendance.check_out_time:
                        # Check if it's a half day (less than 6 hours)
                        if attendance.duration_hours < 6:
                            status = 'halfday'
                        else:
                            status = 'present'
                    else:
                        status = 'incomplete'
                elif is_past:
                    status = 'absent'
                else:
                    status = 'future'
                
                week_data.append({
                    'day': day,
                    'attendance': attendance,
                    'is_today': is_today,
                    'is_past': is_past,
                    'is_future': is_future,
                    'status': status
                })
        calendar_data.append(week_data)

    # Additional statistics
    from datetime import timedelta
    from employees.models import Ticket
    
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Ticket statistics
    my_open_tickets = Ticket.objects.filter(employee=employee, status='open').count()
    my_total_tickets = Ticket.objects.filter(employee=employee).count()
    my_resolved_tickets = Ticket.objects.filter(employee=employee, status='resolved').count()
    
    # Attendance statistics
    complete_days = month_attendance.filter(check_out_time__isnull=False).count()
    incomplete_days = month_attendance.count() - complete_days
    
    # Calculate total hours worked this month
    total_hours = 0
    for att in month_attendance.filter(check_out_time__isnull=False):
        total_hours += att.duration_hours
    
    # Week attendance
    week_attendance = Attendance.objects.filter(
        employee=employee,
        date__gte=week_ago
    ).count()
    
    # Recent tickets
    recent_tickets = Ticket.objects.filter(employee=employee).order_by('-created_at')[:3]
    
    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
        'has_checked_in_today': Attendance.has_checked_in_today(employee),
        'today_attendance': Attendance.objects.filter(
            employee=employee,
            date=timezone.now().date()
        ).first(),
        'recent_attendance': Attendance.objects.filter(employee=employee).order_by('-date')[:10],
        'today': today,
        'current_time': timezone.now(),
        'calendar_data': calendar_data,
        'month_name': month_name_str,
        'current_month': current_month,
        'current_year': current_year,
        'total_month_attendance': month_attendance.count(),
        'complete_days': complete_days,
        'incomplete_days': incomplete_days,
        'total_hours': round(total_hours, 1),
        'week_attendance': week_attendance,
        'my_open_tickets': my_open_tickets,
        'my_total_tickets': my_total_tickets,
        'my_resolved_tickets': my_resolved_tickets,
        'recent_tickets': recent_tickets,
        'day_names': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'requires_face_registration': not employee.has_registered_face,
    })
    return render(request, 'employees/dashboard/employee_dashboard.html', context)


@login_required
@user_passes_test(is_employee)
def my_attendance_logs(request):
    """Employee attendance logs view - shows detailed attendance history"""
    employee = request.user.employee_profile
    from django.utils import timezone
    from django.core.paginator import Paginator
    
    # Get filter parameters
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    # Base queryset
    attendance_records = Attendance.objects.filter(employee=employee).order_by('-date')
    
    filter_kwargs = {}
    if month:
        filter_kwargs['date__month'] = int(month)
    if year:
        filter_kwargs['date__year'] = int(year)

    if filter_kwargs:
        attendance_records = attendance_records.filter(**filter_kwargs)

    # Pagination
    paginator = Paginator(attendance_records, 20)  # 20 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate statistics
    aggregated_metrics = {}
    if attendance_records.exists():
        date_bounds = attendance_records.aggregate(
            first_date=Min('date'),
            last_date=Max('date'),
        )

        start_date = date_bounds['first_date']
        end_date = date_bounds['last_date']

        if start_date and end_date:
            aggregated_metrics = calculate_attendance_metrics(attendance_records, start_date, end_date)
    else:
        aggregated_metrics = {
            'total_working_days': 0,
            'present_days': 0,
            'half_day_days': 0,
            'absent_days': 0,
            'attendance_percentage': 0,
        }

    total_days = attendance_records.count()
    complete_days = attendance_records.filter(check_out_time__isnull=False).count()
    incomplete_days = total_days - complete_days

    # Calculate total hours worked (only for complete days)
    total_hours = 0
    for record in attendance_records.filter(check_out_time__isnull=False):
        total_hours += record.duration_hours
    
    # Get available years for filter
    available_years = Attendance.objects.filter(
        employee=employee
    ).dates('date', 'year', order='DESC')
    
    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
        'page_obj': page_obj,
        'attendance_records': page_obj.object_list,
        'total_days': total_days,
        'complete_days': complete_days,
        'incomplete_days': incomplete_days,
        'total_hours': round(total_hours, 2),
        'total_working_days': aggregated_metrics.get('total_working_days', 0),
        'present_days': aggregated_metrics.get('present_days', 0),
        'absent_days': aggregated_metrics.get('absent_days', 0),
        'half_day_days': aggregated_metrics.get('half_day_days', 0),
        'attendance_percentage': aggregated_metrics.get('attendance_percentage', 0),
        'available_years': available_years,
        'selected_month': month,
        'selected_year': year,
        'current_date': timezone.now().date(),
    })
    return render(request, 'employees/my_attendance_logs.html', context)


# Employee CRUD Views
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_superadmin), name='dispatch')
class EmployeeListView(ListView):
    """List all employees"""
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        })
        return context

    def get_queryset(self):
        queryset = Employee.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(contact__icontains=search)
            )
        return queryset.order_by('name', 'full_name')


@login_required
@user_passes_test(is_superadmin)
def employee_live_search(request):
    """Return filtered employees for live search (AJAX only)."""
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

    query = request.GET.get('q', '').strip()
    employees = Employee.objects.all()

    if query:
        employees = employees.filter(
            Q(name__icontains=query) |
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(contact__icontains=query)
        )

    employees = employees.order_by('name', 'full_name')[:25]
    html = render_to_string(
        'employees/partials/_employee_rows.html',
        {'employees': employees, 'request': request}
    )

    return JsonResponse({
        'success': True,
        'html': html,
        'count': employees.count(),
    })


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_superadmin), name='dispatch')
class EmployeeCreateView(CreateView):
    """Create new employee"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee_list')

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
            'title': 'Create Employee',
        })
        return context

    def form_valid(self, form):
        password = form.cleaned_data.get('password')
        if not password or len(password) < 8:
            form.add_error('password', 'Password is required (minimum 8 characters).')
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['name'],
                    password=password,
                    is_staff=True,
                    is_active=True
                )

                employee = form.save(commit=False)
                employee.user = user
                employee.profile_picture = None
                employee.face_registered = False
                employee.face_encoding = None
                employee.face_registered_at = None
                employee.save()

                self.object = employee
                messages.success(
                    self.request,
                    'Employee created successfully. Ask the employee to log in and register their face using their camera before using attendance.'
                )
                return redirect(self.get_success_url())
        except Exception as e:
            form.add_error(None, f'Could not create employee: {e}')
            return self.form_invalid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_superadmin), name='dispatch')
class EmployeeUpdateView(UpdateView):
    """Update existing employee"""
    model = Employee
    form_class = EmployeeUpdateForm
    template_name = 'employees/employee_form.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
            'title': 'Update Employee',
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Employee updated successfully.')
        return response

    def get_success_url(self):
        return reverse_lazy('employees:employee_list')


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_superadmin), name='dispatch')
class EmployeeDeleteView(DeleteView):
    """Delete employee"""
    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    success_url = reverse_lazy('employees:employee_list')

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        })
        return context

    def delete(self, request, *args, **kwargs):
        employee = self.get_object()
        # Delete associated user account
        if employee.user:
            employee.user.delete()
        messages.success(request, 'Employee deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Employee Status Toggle View (for super-admins to activate/deactivate employees)
@login_required
@user_passes_test(is_superadmin)
def employee_toggle_status(request, pk):
    """Toggle employee active/inactive status (Super-admin only)"""
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        # Toggle the user's active status
        employee.user.is_active = not employee.user.is_active
        employee.user.save()

        status = "activated" if employee.user.is_active else "deactivated"
        messages.success(request, f'Employee {employee.full_name} has been {status} successfully!')

        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)

        # Redirect back to the page that made the request
        referer = request.META.get('HTTP_REFERER')
        if referer and 'employee_list' in referer:
            return redirect('employees:employee_list')
        else:
            return redirect('employees:employee_detail', pk=pk)

    # If not POST, redirect back
    messages.error(request, 'Invalid request method.')
    return redirect('employees:employee_list')
@login_required
@user_passes_test(is_superadmin)
def employee_detail(request, pk):
    """View employee details (Super-admin only)"""
    employee = get_object_or_404(Employee, pk=pk)
    from django.utils import timezone

    # Get attendance statistics
    total_attendance = Attendance.objects.filter(employee=employee).count()
    current_month_attendance = Attendance.objects.filter(
        employee=employee,
        date__year=timezone.now().year,
        date__month=timezone.now().month
    ).count()

    # Get recent attendance records
    recent_attendance = Attendance.objects.filter(employee=employee).order_by('-date')[:10]

    # Get attendance for current week
    week_start = timezone.now().date() - timezone.timedelta(days=7)
    week_attendance = Attendance.objects.filter(
        employee=employee,
        date__gte=week_start,
        date__lte=timezone.now().date()
    ).order_by('-date')

    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
        'total_attendance': total_attendance,
        'current_month_attendance': current_month_attendance,
        'recent_attendance': recent_attendance,
        'week_attendance': week_attendance,
        'today': timezone.now().date(),
    })
    return render(request, 'employees/employee_detail.html', context)

# Employee Profile View (for employees to view their own profile)
@login_required
@user_passes_test(is_employee)
def employee_profile(request):
    """Employee profile view"""
    # Redirect superadmins to their profile
    if request.user.is_superuser:
        return redirect('employees:superadmin_profile')

    employee = request.user.employee_profile
    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
    })
    return render(request, 'employees/employee_profile.html', context)


# SuperAdmin Profile Views
@login_required
@user_passes_test(is_superadmin)
def superadmin_profile(request):
    """SuperAdmin profile view"""
    user = request.user
    from django.utils import timezone

    # Get statistics for superadmin dashboard
    total_employees = Employee.objects.count()
    today_checkins = Attendance.objects.filter(date=timezone.now().date()).count()

    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'user': user,
        'total_employees': total_employees,
        'today_checkins': today_checkins,
    })
    return render(request, 'employees/superadmin_profile.html', context)


@login_required
@user_passes_test(is_superadmin)
def superadmin_profile_edit(request):
    """SuperAdmin profile edit view"""
    user = request.user

    if request.method == 'POST':
        form = SuperAdminProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('employees:superadmin_profile')
    else:
        form = SuperAdminProfileForm(instance=user)

    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'form': form,
        'user': user,
    })
    return render(request, 'employees/superadmin_profile_edit.html', context)


@login_required
@user_passes_test(is_superadmin)
def superadmin_change_password(request):
    """Allow superadmin to update their own password"""
    context = TemplateLayout.init(self={}, context={})

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been updated successfully.')
            return redirect('employees:superadmin_profile')
        else:
            messages.error(request, 'Please correct the errors below to update your password.')
    else:
        form = PasswordChangeForm(request.user)

    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'form': form,
    })
    return render(request, 'employees/superadmin_change_password.html', context)
def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
@user_passes_test(is_employee)
def check_in(request):
    """Employee check-in view"""
    from employees.models import AttendanceLog
    employee = request.user.employee_profile
    today = timezone.now().date()

    # Get today's attendance record if it exists
    today_attendance = Attendance.objects.filter(employee=employee, date=today).first()

    if not employee.has_registered_face:
        face_register_url = f"{reverse('employees:face_register')}?next={reverse('employees:check_in')}"
        messages.warning(
            request,
            'Please register your face before checking in. Use the camera to capture your profile so we can verify you during attendance.'
        )
        return redirect(face_register_url)

    if request.method == 'POST':
        # Validate geolocation first
        from employees.geolocation_utils import validate_coordinates, is_within_office_premises
        
        user_latitude = request.POST.get('latitude')
        user_longitude = request.POST.get('longitude')
        
        if not user_latitude or not user_longitude:
            AttendanceLog.objects.create(
                employee=employee,
                action='check_in_failed',
                success=False,
                failure_reason='location_not_provided',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes='Location coordinates were not provided'
            )
            messages.error(request, 'Location access is required for check-in. Please enable location services and try again.')
            return redirect('employees:check_in')
        
        # Validate coordinate format
        is_valid_coords, coord_message = validate_coordinates(user_latitude, user_longitude)
        if not is_valid_coords:
            AttendanceLog.objects.create(
                employee=employee,
                action='check_in_failed',
                success=False,
                failure_reason='invalid_coordinates',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes=f'Invalid coordinates: {coord_message}'
            )
            messages.error(request, f'Invalid location data: {coord_message}')
            return redirect('employees:check_in')
        
        # Check if within office premises
        is_within, distance, location_message = is_within_office_premises(
            float(user_latitude), 
            float(user_longitude)
        )
        
        if not is_within:
            AttendanceLog.objects.create(
                employee=employee,
                action='check_in_failed',
                success=False,
                failure_reason='outside_office_premises',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes=f'Location: {user_latitude}, {user_longitude}. {location_message}'
            )
            messages.error(request, location_message)
            return redirect('employees:check_in')
        
        # Require photo and face match
        check_in_photo = request.FILES.get('check_in_photo')
        if not check_in_photo:
            # Log failed attempt
            AttendanceLog.objects.create(
                employee=employee,
                action='check_in_failed',
                success=False,
                failure_reason='photo_required',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes='Photo was not provided'
            )
            messages.error(request, 'Please capture a photo to check in.')
            return redirect('employees:check_in')

        if not employee.has_registered_face:
            # Log failed attempt
            AttendanceLog.objects.create(
                employee=employee,
                action='check_in_failed',
                success=False,
                failure_reason='no_face_registered',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes='Employee face is not registered'
            )
            messages.error(request, 'Face is not registered for your account. Contact admin to register your face.')
            return redirect('employees:employee_dashboard')

        try:
            stored_encoding = employee.get_face_encoding()
            checkin_encoding = extract_face_encoding_from_file(check_in_photo)

            if checkin_encoding is None:
                AttendanceLog.objects.create(
                    employee=employee,
                    action='check_in_failed',
                    success=False,
                    failure_reason='no_face_detected',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    notes='No face or multiple faces detected in photo'
                )
                messages.error(request, 'No face detected or multiple faces detected. Please try again with a clear face in frame.')
                return redirect('employees:check_in')

            if stored_encoding is None:
                AttendanceLog.objects.create(
                    employee=employee,
                    action='check_in_failed',
                    success=False,
                    failure_reason='no_face_registered',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    notes='Stored face encoding missing for employee'
                )
                messages.error(request, 'Your face data is missing. Please re-register your face before checking in.')
                return redirect('employees:face_register')

            tol = get_strict_match_tolerance()
            result = compare_faces(stored_encoding, checkin_encoding, tolerance=tol)

            if not result['match']:
                AttendanceLog.objects.create(
                    employee=employee,
                    action='check_in_failed',
                    success=False,
                    failure_reason='face_not_matched',
                    confidence=result['confidence'],
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    notes=f'Face verification failed with {result["confidence"]:.1f}% confidence (strict tolerance)'
                )
                messages.error(request, 'Face does not match the registered face. Check-in denied.')
                return redirect('employees:check_in')

            match_info = find_best_face_match(
                checkin_encoding,
                Employee.objects.filter(face_registered=True),
                tolerance=get_match_tolerance(),
            )

            if not match_info or match_info['employee'].pk != employee.pk:
                matched_employee = match_info['employee'].full_name if match_info else None
                AttendanceLog.objects.create(
                    employee=employee,
                    action='check_in_failed',
                    success=False,
                    failure_reason='face_not_matched',
                    confidence=match_info['confidence'] if match_info else None,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    notes='Face appears to match another employee' if match_info else 'No unique match identified'
                )
                if matched_employee:
                    messages.error(request, f'Face verification failed. This face matches another employee ({matched_employee}). Check-in denied.')
                else:
                    messages.error(request, 'Face verification failed. We could not uniquely match your face to your profile. Check-in denied.')
                return redirect('employees:check_in')

            # Passed verification, create attendance
            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={
                    'check_in_time': timezone.now(),
                }
            )
            # If already exists and has check_in_time, keep it but allow updating photo and location
            attendance.check_in_photo.save(check_in_photo.name, check_in_photo, save=False)
            attendance.check_in_latitude = user_latitude
            attendance.check_in_longitude = user_longitude
            attendance.save()

            # Log successful check-in
            AttendanceLog.objects.create(
                employee=employee,
                action='check_in_success',
                success=True,
                confidence=result['confidence'],
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                attendance=attendance,
                notes=f'Check-in successful with {result["confidence"]:.1f}% confidence'
            )

            messages.success(request, f'✓ Check-in successful! Face verified with {result["confidence"]:.1f}% confidence.')
            return redirect('employees:employee_dashboard')

        except Exception as e:
            # Log exception
            AttendanceLog.objects.create(
                employee=employee,
                action='check_in_failed',
                success=False,
                failure_reason='other',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes=f'Exception during face verification: {str(e)}'
            )
            messages.error(request, f'Error during face verification: {str(e)}')
            return redirect('employees:check_in')

    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
        'has_checked_in_today': bool(today_attendance),
        'today_attendance': today_attendance,
        'date_today': today,
        'current_time': timezone.now(),
    })
    return render(request, 'employees/check_in.html', context)


# Attendance Views (for admin)
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_superadmin), name='dispatch')
class AttendanceListView(ListView):
    """List all attendance records"""
    model = Attendance
    template_name = 'employees/attendance_list.html'
    context_object_name = 'attendance_records'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        today = timezone.now().date()
        queryset = self.get_queryset()

        metrics = {}
        if queryset.exists():
            date_bounds = queryset.aggregate(
                first_date=Min('date'),
                last_date=Max('date'),
            )

            start_date = date_bounds['first_date']
            end_date = date_bounds['last_date']

            if start_date and end_date:
                metrics = calculate_attendance_metrics(queryset, start_date, end_date)
        else:
            metrics = {
                'total_working_days': 0,
                'present_days': 0,
                'half_day_days': 0,
                'absent_days': 0,
                'attendance_percentage': 0,
            }

        context.update({
            'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
            'today_count': Attendance.objects.filter(date=today).count(),
            'unique_employees': Attendance.objects.filter(
                date=today
            ).values('employee').distinct().count(),
            'total_employees': Employee.objects.count(),
            'today': today,
            'total_working_days': metrics.get('total_working_days', 0),
            'present_days': metrics.get('present_days', 0),
            'half_day_days': metrics.get('half_day_days', 0),
            'absent_days': metrics.get('absent_days', 0),
            'attendance_percentage': metrics.get('attendance_percentage', 0),
        })
        return context

    def get_queryset(self):
        queryset = Attendance.objects.select_related('employee')
        date_filter = self.request.GET.get('date')
        employee_filter = self.request.GET.get('employee')

        if date_filter:
            queryset = queryset.filter(date=date_filter)
        if employee_filter:
            queryset = queryset.filter(employee_id=employee_filter)

        return queryset.order_by('-check_in_time')


@login_required
@user_passes_test(is_superadmin)
def admin_attendance_logs(request):
    """Admin view for all attendance activity logs including failed attempts"""
    from django.core.paginator import Paginator
    from employees.models import AttendanceLog
    
    # Get filter parameters
    employee_id = request.GET.get('employee')
    action = request.GET.get('action')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Base queryset
    logs = AttendanceLog.objects.select_related('employee', 'attendance').order_by('-timestamp')
    
    # Apply filters
    if employee_id:
        logs = logs.filter(employee_id=employee_id)
    
    if action:
        logs = logs.filter(action=action)
    
    if status == 'success':
        logs = logs.filter(success=True)
    elif status == 'failed':
        logs = logs.filter(success=False)
    
    if date_from:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        logs = logs.filter(timestamp__date__gte=date_from_obj)
    
    if date_to:
        from datetime import datetime
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        logs = logs.filter(timestamp__date__lte=date_to_obj)
    
    # Calculate statistics
    total_logs = logs.count()
    successful_logs = logs.filter(success=True).count()
    failed_logs = logs.filter(success=False).count()
    
    # Count by action type
    check_in_attempts = logs.filter(action__contains='check_in').count()
    check_out_attempts = logs.filter(action__contains='check_out').count()
    
    # Recent failed attempts (for security monitoring)
    recent_failures = AttendanceLog.objects.filter(
        success=False
    ).select_related('employee').order_by('-timestamp')[:10]
    
    # Pagination
    paginator = Paginator(logs, 50)  # 50 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all employees for filter dropdown
    employees = Employee.objects.all().order_by('name')
    
    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'total_logs': total_logs,
        'successful_logs': successful_logs,
        'failed_logs': failed_logs,
        'check_in_attempts': check_in_attempts,
        'check_out_attempts': check_out_attempts,
        'recent_failures': recent_failures,
        'employees': employees,
        'selected_employee': employee_id,
        'selected_action': action,
        'selected_status': status,
        'selected_date_from': date_from,
        'selected_date_to': date_to,
        'action_choices': AttendanceLog.ACTION_CHOICES,
        'current_date': timezone.now().date(),
    })
    return render(request, 'employees/admin_attendance_logs.html', context)


@require_http_methods(["GET", "POST"])
@login_required
@user_passes_test(is_employee)
def face_registration(request):
    """Allow an employee to register (or re-register) their face using the webcam."""
    employee = request.user.employee_profile

    if request.method == 'GET':
        context = TemplateLayout.init(self={}, context={})
        context.update({
            'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
            'employee': employee,
            'has_registered_face': employee.has_registered_face,
        })
        return render(request, 'employees/face_register.html', context)

    # POST: process uploaded image (base64 or file)
    image_payload = request.POST.get('image') or request.POST.get('image_base64')
    image_file = request.FILES.get('image_file') or request.FILES.get('upload_image')

    if not image_payload and not image_file:
        return JsonResponse({'success': False, 'error': 'No image provided. Please capture or upload a clear photo.'}, status=400)

    try:
        if image_file:
            image_bytes = image_file.read()
        else:
            payload = image_payload
            if 'base64,' in payload:
                payload = payload.split('base64,', 1)[1]
            try:
                image_bytes = base64.b64decode(payload)
            except (base64.binascii.Error, ValueError) as exc:
                return JsonResponse({'success': False, 'error': 'Unable to read the captured image. Please try again.'}, status=400)

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return JsonResponse({'success': False, 'error': 'Image format is not supported. Try retaking or uploading a JPG/PNG photo.'}, status=400)

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_img)

        if not face_locations:
            return JsonResponse({'success': False, 'error': 'No face detected. Please try again.'}, status=400)
        if len(face_locations) > 1:
            return JsonResponse({'success': False, 'error': 'Multiple faces detected. Capture only your face.'}, status=400)

        face_encoding = face_recognition.face_encodings(rgb_img, face_locations)[0]

        # Prevent registering duplicate faces for different employees
        tolerance = get_match_tolerance()
        is_unique, conflict_emp, conflict_distance = is_encoding_unique(
            face_encoding,
            exclude_employee_id=employee.pk,
            tolerance=tolerance,
        )

        if not is_unique and conflict_emp:
            return JsonResponse({
                'success': False,
                'error': (
                    'This face appears to match another employee on record '
                    'and cannot be registered again. If you believe this is an error, '
                    'contact your administrator.'
                ),
                'conflict_employee': conflict_emp.full_name,
                'distance': conflict_distance,
            }, status=400)

        # Persist encoding and profile photo
        employee.set_face_encoding(face_encoding)
        success, buffer = cv2.imencode('.jpg', img)
        if not success:
            return JsonResponse({'success': False, 'error': 'Unable to process image. Please try again.'}, status=400)

        file_name = f'profile_{employee.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        employee.profile_picture.save(file_name, ContentFile(buffer.tobytes()), save=False)
        employee.save()

        return JsonResponse({
            'success': True,
            'message': 'Face registered successfully! You can now use face-enabled check-in/out.',
            'profile_picture': employee.profile_picture.url if employee.profile_picture else ''
        })
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)


def mark_attendance(request):
    """
    View for marking attendance using face recognition
    """
    if request.method == 'POST' and 'image' in request.POST:
        try:
            # Get the base64 image data
            image_data = request.POST['image'].split('base64,')[1]
            image_data = base64.b64decode(image_data)
            
            # Convert to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert BGR to RGB
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(rgb_img)
            
            if not face_locations:
                return JsonResponse({'success': False, 'error': 'No face detected'})
                
            if len(face_locations) > 1:
                return JsonResponse({'success': False, 'error': 'Multiple faces detected'})
            
            # Get the face encoding
            unknown_encoding = face_recognition.face_encodings(rgb_img, face_locations)[0]
            
            # Get all employees with face encodings
            employees = Employee.objects.filter(face_registered=True).exclude(face_encoding__isnull=True)
            
            # Compare with known faces
            for employee in employees:
                known_encoding = employee.get_face_encoding()
                if known_encoding is not None:
                    result = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.6)
                    if result[0]:
                        # Face recognized, mark attendance
                        attendance, created = Attendance.objects.get_or_create(
                            employee=employee,
                            date=timezone.now().date(),
                            defaults={
                                'check_in_time': timezone.now(),
                                'check_in_photo': save_attendance_image(img, f"checkin_{employee.id}")
                            }
                        )
                        
                        if not created:
                            # If already checked in, update check out
                            if not attendance.check_out_time:
                                attendance.check_out_time = timezone.now()
                                attendance.check_out_photo = save_attendance_image(img, f"checkout_{employee.id}")
                                attendance.save()
                                return JsonResponse({
                                    'success': True,
                                    'message': f'Check out recorded for {employee.name}',
                                    'employee_name': employee.name,
                                    'action': 'check_out',
                                    'time': timezone.now().strftime('%H:%M:%S')
                                })
                            else:
                                return JsonResponse({
                                    'success': False,
                                    'error': f'Attendance already marked for today',
                                    'employee_name': employee.name
                                })
                        
                        return JsonResponse({
                            'success': True,
                            'message': f'Check in recorded for {employee.name}',
                            'employee_name': employee.name,
                            'action': 'check_in',
                            'time': timezone.now().strftime('%H:%M:%S')
                        })
            
            return JsonResponse({'success': False, 'error': 'Face not recognized'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def save_attendance_image(image, prefix):
    """Helper function to save attendance images"""
    from django.core.files.base import ContentFile
    from io import BytesIO
    
    # Convert numpy array to PIL Image
    image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    # Save to BytesIO
    img_io = BytesIO()
    image.save(img_io, format='JPEG')
    
    # Create ContentFile from BytesIO
    return ContentFile(img_io.getvalue(), name=f"{prefix}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg")


# API Views for AJAX requests
@login_required
@user_passes_test(is_employee)
def check_in_status(request):
    """AJAX endpoint to check if employee has already checked in today"""
    employee = request.user.employee_profile
    has_checked_in = Attendance.has_checked_in_today(employee)

    return JsonResponse({
        'has_checked_in': has_checked_in,
        'message': 'Already checked in today' if has_checked_in else 'Not checked in today'
    })


@login_required
@user_passes_test(is_employee)
def check_out(request):
    """Employee check-out view with face verification - handles POST requests only"""
    from employees.models import AttendanceLog
    employee = request.user.employee_profile
    today = timezone.now().date()

    # Get today's attendance record
    attendance = Attendance.objects.filter(employee=employee, date=today).first()

    # Validation 1: Must be checked in first
    if not attendance:
        # Log failed attempt
        AttendanceLog.objects.create(
            employee=employee,
            action='check_out_failed',
            success=False,
            failure_reason='not_checked_in',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            notes='Employee has not checked in today'
        )
        messages.error(request, 'You have not checked in today. Please check in first before checking out.')
        return redirect('employees:check_in')

    # Validation 2: Cannot check out twice
    if attendance.check_out_time:
        # Log failed attempt
        AttendanceLog.objects.create(
            employee=employee,
            action='check_out_failed',
            success=False,
            failure_reason='already_checked_out',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            attendance=attendance,
            notes='Employee has already checked out today'
        )
        messages.info(request, 'You have already checked out today.')
        return redirect('employees:check_in')

    # Only handle POST requests (from the embedded form in check_in.html)
    if request.method == 'POST':
        # Validate geolocation first
        from employees.geolocation_utils import validate_coordinates, is_within_office_premises
        
        user_latitude = request.POST.get('latitude')
        user_longitude = request.POST.get('longitude')
        
        if not user_latitude or not user_longitude:
            AttendanceLog.objects.create(
                employee=employee,
                action='check_out_failed',
                success=False,
                failure_reason='location_not_provided',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                attendance=attendance,
                notes='Location coordinates were not provided'
            )
            messages.error(request, 'Location access is required for check-out. Please enable location services and try again.')
            return redirect('employees:check_in')
        
        # Validate coordinate format
        is_valid_coords, coord_message = validate_coordinates(user_latitude, user_longitude)
        if not is_valid_coords:
            AttendanceLog.objects.create(
                employee=employee,
                action='check_out_failed',
                success=False,
                failure_reason='invalid_coordinates',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                attendance=attendance,
                notes=f'Invalid coordinates: {coord_message}'
            )
            messages.error(request, f'Invalid location data: {coord_message}')
            return redirect('employees:check_in')
        
        # Check if within office premises
        is_within, distance, location_message = is_within_office_premises(
            float(user_latitude), 
            float(user_longitude)
        )
        
        if not is_within:
            AttendanceLog.objects.create(
                employee=employee,
                action='check_out_failed',
                success=False,
                failure_reason='outside_office_premises',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                attendance=attendance,
                notes=f'Location: {user_latitude}, {user_longitude}. {location_message}'
            )
            messages.error(request, location_message)
            return redirect('employees:check_in')
        
        # Validation 3: Photo is required
        check_out_photo = request.FILES.get('check_out_photo')
        if not check_out_photo:
            # Log failed attempt
            AttendanceLog.objects.create(
                employee=employee,
                action='check_out_failed',
                success=False,
                failure_reason='photo_required',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                attendance=attendance,
                notes='Photo was not provided'
            )
            messages.error(request, 'Please capture a photo to check out.')
            return redirect('employees:check_in')

        # Validation 4: Face must be registered
        if not employee.has_registered_face:
            # Log failed attempt
            AttendanceLog.objects.create(
                employee=employee,
                action='check_out_failed',
                success=False,
                failure_reason='no_face_registered',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                attendance=attendance,
                notes='Employee face is not registered'
            )
            messages.error(request, 'Face is not registered for your account. Contact admin to register your face.')
            return redirect('employees:check_in')

        try:
            stored_encoding = employee.get_face_encoding()
            checkout_encoding = extract_face_encoding_from_file(check_out_photo)

            if checkout_encoding is None:
                AttendanceLog.objects.create(
                    employee=employee,
                    action='check_out_failed',
                    success=False,
                    failure_reason='no_face_detected',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    attendance=attendance,
                    notes='No face or multiple faces detected in photo'
                )
                messages.error(request, 'No face detected or multiple faces detected in the photo. Please try again with a clear face in frame.')
                return redirect('employees:check_in')

            if stored_encoding is None:
                AttendanceLog.objects.create(
                    employee=employee,
                    action='check_out_failed',
                    success=False,
                    failure_reason='no_face_registered',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    attendance=attendance,
                    notes='Stored face encoding missing for employee'
                )
                messages.error(request, 'Your face data is missing. Please re-register your face before checking out.')
                return redirect('employees:face_register')

            strict_tol = get_strict_match_tolerance()
            result = compare_faces(stored_encoding, checkout_encoding, tolerance=strict_tol)

            if not result['match']:
                AttendanceLog.objects.create(
                    employee=employee,
                    action='check_out_failed',
                    success=False,
                    failure_reason='face_not_matched',
                    confidence=result['confidence'],
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    attendance=attendance,
                    notes=f'Face verification failed with {result["confidence"]:.1f}% confidence (strict tolerance)'
                )
                messages.error(request, 'Face verification failed. The captured face does not match your registered face. Check-out denied.')
                return redirect('employees:check_in')

            match_info = find_best_face_match(
                checkout_encoding,
                Employee.objects.filter(face_registered=True),
                tolerance=get_match_tolerance(),
            )

            if not match_info or match_info['employee'].pk != employee.pk:
                matched_employee = match_info['employee'].full_name if match_info else None
                AttendanceLog.objects.create(
                    employee=employee,
                    action='check_out_failed',
                    success=False,
                    failure_reason='face_not_matched',
                    confidence=match_info['confidence'] if match_info else None,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    attendance=attendance,
                    notes='Face appears to match another employee' if match_info else 'No unique match identified'
                )
                if matched_employee:
                    messages.error(request, f'Face verification failed. This face matches another employee ({matched_employee}). Check-out denied.')
                else:
                    messages.error(request, 'Face verification failed. We could not uniquely match your face to your profile. Check-out denied.')
                return redirect('employees:check_in')

            # All validations passed - save check-out
            check_out_time = timezone.now()
            attendance.check_out_photo.save(check_out_photo.name, check_out_photo, save=False)
            attendance.check_out_time = check_out_time
            attendance.check_out_latitude = user_latitude
            attendance.check_out_longitude = user_longitude
            # Determine half-day status (worked hours below threshold)
            HALF_DAY_THRESHOLD_SECONDS = int(4.5 * 60 * 60)
            time_worked = check_out_time - attendance.check_in_time
            attendance.half_day = time_worked.total_seconds() < HALF_DAY_THRESHOLD_SECONDS
            attendance.save()
            
            # Log successful check-out
            AttendanceLog.objects.create(
                employee=employee,
                action='check_out_success',
                success=True,
                confidence=result['confidence'],
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                attendance=attendance,
                notes=f'Check-out successful with {result["confidence"]:.1f}% confidence'
            )
            
            messages.success(request, f'✓ Check-out successful! Face verified with {result["confidence"]:.1f}% confidence. Have a great day!')
            return redirect('employees:employee_dashboard')
            
        except Exception as e:
            # Log exception
            AttendanceLog.objects.create(
                employee=employee,
                action='check_out_failed',
                success=False,
                failure_reason='other',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                attendance=attendance,
                notes=f'Exception during face verification: {str(e)}'
            )
            messages.error(request, f'Error during face verification: {str(e)}. Please try again or contact support.')
            return redirect('employees:check_in')
    
    # GET request - redirect to check-in page
    return redirect('employees:check_in')


# Ticket System Views

@login_required
@user_passes_test(is_employee)
def employee_tickets(request):
    """Employee view for their tickets"""
    from employees.models import Ticket
    from django.core.paginator import Paginator
    
    employee = request.user.employee_profile
    
    # Get filter parameters
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    
    # Base queryset
    tickets = Ticket.objects.filter(employee=employee).order_by('-created_at')
    
    # Apply filters
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    
    # Statistics
    total_tickets = Ticket.objects.filter(employee=employee).count()
    open_tickets = Ticket.objects.filter(employee=employee, status='open').count()
    in_progress_tickets = Ticket.objects.filter(employee=employee, status='in_progress').count()
    resolved_tickets = Ticket.objects.filter(employee=employee, status='resolved').count()
    
    # Pagination
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
        'page_obj': page_obj,
        'tickets': page_obj.object_list,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'resolved_tickets': resolved_tickets,
        'selected_status': status,
        'selected_priority': priority,
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
    })
    return render(request, 'employees/tickets/employee_tickets.html', context)


@login_required
@user_passes_test(is_employee)
def create_ticket(request):
    """Create new ticket"""
    from employees.models import Ticket
    
    employee = request.user.employee_profile
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        category = request.POST.get('category')
        priority = request.POST.get('priority', 'medium')
        attachment = request.FILES.get('attachment')
        
        if not subject or not description:
            messages.error(request, 'Subject and description are required.')
            return redirect('employees:create_ticket')
        
        ticket = Ticket.objects.create(
            employee=employee,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            attachment=attachment
        )
        
        messages.success(request, f'Ticket {ticket.ticket_number} created successfully! We will respond soon.')
        return redirect('employees:ticket_detail', pk=ticket.pk)
    
    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
        'category_choices': Ticket.CATEGORY_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
    })
    return render(request, 'employees/tickets/create_ticket.html', context)


@login_required
@user_passes_test(is_employee)
def ticket_detail(request, pk):
    """View ticket details with comments"""
    from employees.models import Ticket, TicketComment
    
    employee = request.user.employee_profile
    ticket = get_object_or_404(Ticket, pk=pk, employee=employee)
    comments = ticket.comments.filter(is_internal=False).order_by('created_at')
    
    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
        'ticket': ticket,
        'comments': comments,
    })
    return render(request, 'employees/tickets/ticket_detail.html', context)


@login_required
@user_passes_test(is_employee)
def add_ticket_comment(request, pk):
    """Add comment to ticket"""
    from employees.models import Ticket, TicketComment
    
    employee = request.user.employee_profile
    ticket = get_object_or_404(Ticket, pk=pk, employee=employee)
    
    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        
        if comment_text:
            TicketComment.objects.create(
                ticket=ticket,
                user=request.user,
                comment=comment_text,
                is_internal=False
            )
            messages.success(request, 'Comment added successfully.')
        else:
            messages.error(request, 'Comment cannot be empty.')
    
    return redirect('employees:ticket_detail', pk=pk)


@login_required
@user_passes_test(is_superadmin)
def admin_tickets(request):
    """Admin view for all tickets"""
    from employees.models import Ticket
    from django.core.paginator import Paginator
    
    # Get filter parameters
    employee_id = request.GET.get('employee')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    category = request.GET.get('category')
    
    # Base queryset
    tickets = Ticket.objects.select_related('employee', 'resolved_by').order_by('-created_at')
    
    # Apply filters
    if employee_id:
        tickets = tickets.filter(employee_id=employee_id)
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    if category:
        tickets = tickets.filter(category=category)
    
    # Statistics
    total_tickets = Ticket.objects.count()
    open_tickets = Ticket.objects.filter(status='open').count()
    in_progress_tickets = Ticket.objects.filter(status='in_progress').count()
    resolved_tickets = Ticket.objects.filter(status='resolved').count()
    urgent_tickets = Ticket.objects.filter(priority='urgent', status__in=['open', 'in_progress']).count()
    
    # Pagination
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all employees for filter
    employees = Employee.objects.all().order_by('name')
    
    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'page_obj': page_obj,
        'tickets': page_obj.object_list,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'resolved_tickets': resolved_tickets,
        'urgent_tickets': urgent_tickets,
        'employees': employees,
        'selected_employee': employee_id,
        'selected_status': status,
        'selected_priority': priority,
        'selected_category': category,
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'category_choices': Ticket.CATEGORY_CHOICES,
    })
    return render(request, 'employees/tickets/admin_tickets.html', context)


@login_required
@user_passes_test(is_superadmin)
def admin_update_ticket(request, pk):
    """Admin update ticket status and add notes"""
    from employees.models import Ticket, TicketComment
    
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_status':
            old_status = ticket.status
            new_status = request.POST.get('status')
            new_priority = request.POST.get('priority')
            admin_notes = request.POST.get('admin_notes')
            
            ticket.status = new_status
            ticket.priority = new_priority
            
            if admin_notes:
                ticket.admin_notes = admin_notes
            
            if new_status == 'resolved':
                ticket.resolved_by = request.user
                ticket.resolved_at = timezone.now()
            
            ticket.save()
            
            # Add automatic comment about status change (visible to employee)
            if old_status != new_status:
                status_comment = f"Status changed from '{dict(Ticket.STATUS_CHOICES)[old_status]}' to '{dict(Ticket.STATUS_CHOICES)[new_status]}'"
                if new_priority:
                    status_comment += f" | Priority updated to '{dict(Ticket.PRIORITY_CHOICES)[new_priority]}'"
                
                TicketComment.objects.create(
                    ticket=ticket,
                    user=request.user,
                    comment=status_comment,
                    is_internal=False  # Visible to employee
                )
            
            messages.success(request, f'Ticket {ticket.ticket_number} updated successfully. Employee will see the status change.')
        
        elif action == 'add_comment':
            comment_text = request.POST.get('comment')
            is_internal = request.POST.get('is_internal') == 'on'
            
            if comment_text:
                TicketComment.objects.create(
                    ticket=ticket,
                    user=request.user,
                    comment=comment_text,
                    is_internal=is_internal
                )
                if is_internal:
                    messages.success(request, 'Internal note added (not visible to employee).')
                else:
                    messages.success(request, 'Comment added successfully. Employee will see this comment.')
    
    return redirect('employees:admin_tickets')


# ===========================
# ATTENDANCE CALENDAR VIEWS
# ===========================

@login_required
@user_passes_test(is_employee)
def employee_attendance_calendar(request):
    """Interactive attendance calendar for employees"""
    from datetime import datetime, timedelta
    from calendar import monthrange
    import calendar
    
    employee = request.user.employee_profile
    
    # Get year and month from query params, default to current
    current_date = timezone.now()
    year = int(request.GET.get('year', current_date.year))
    month = int(request.GET.get('month', current_date.month))
    
    # Ensure valid month/year
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    
    # Get first and last day of the month
    first_day = datetime(year, month, 1).date()
    last_day = datetime(year, month, monthrange(year, month)[1]).date()
    
    # Get all attendance records for this month
    attendance_records = Attendance.objects.filter(
        employee=employee,
        date__gte=first_day,
        date__lte=last_day
    ).select_related('employee')
    
    # Create a dictionary for quick lookup
    attendance_dict = {record.date: record for record in attendance_records}
    
    # Helper function to check if a date is a holiday
    def is_holiday(date_obj):
        """Check if date is a holiday (Sunday or 1st, 3rd, 5th Saturday)"""
        # Sunday is weekday 6
        if date_obj.weekday() == 6:
            return True
        
        # Saturday is weekday 5
        if date_obj.weekday() == 5:
            # Count which Saturday of the month this is
            saturday_count = 0
            for d in range(1, date_obj.day + 1):
                if datetime(date_obj.year, date_obj.month, d).weekday() == 5:
                    saturday_count += 1
            
            # 1st, 3rd, 5th Saturday are holidays
            if saturday_count in [1, 3, 5]:
                return True
        
        return False
    
    # Generate calendar data
    cal = calendar.monthcalendar(year, month)
    calendar_data = []
    
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                date_obj = datetime(year, month, day).date()
                attendance = attendance_dict.get(date_obj)
                is_holiday_day = is_holiday(date_obj)
                
                # Determine status
                status = 'none'
                status_class = ''
                status_icon = ''
                
                if attendance:
                    if attendance.check_out_time:
                        if attendance.is_half_day:
                            status = 'halfday'
                            status_class = 'bg-info'
                            status_icon = 'bx-time-five'
                        else:
                            status = 'present'
                            status_class = 'bg-success'
                            status_icon = 'bx-check-circle'
                    else:
                        status = 'checked-in'
                        status_class = 'bg-warning'
                        status_icon = 'bx-time'
                elif is_holiday_day:  # Holiday
                    status = 'holiday'
                    status_class = 'bg-secondary'
                    status_icon = 'bx-calendar'
                elif date_obj < current_date.date():  # Past working day without attendance
                    status = 'absent'
                    status_class = 'bg-danger'
                    status_icon = 'bx-x-circle'
                
                week_data.append({
                    'day': day,
                    'date': date_obj,
                    'attendance': attendance,
                    'status': status,
                    'status_class': status_class,
                    'status_icon': status_icon,
                    'is_half_day': attendance.is_half_day if attendance else False,
                    'is_today': date_obj == current_date.date(),
                    'is_future': date_obj > current_date.date(),
                    'is_holiday': is_holiday_day
                })
        calendar_data.append(week_data)
    
    # Calculate statistics for the month (excluding holidays)
    total_working_days = sum(1 for week in calendar_data for day in week 
                            if day and not day['is_holiday'] and day['date'] <= current_date.date())
    present_days = sum(1 for record in attendance_records if record.check_out_time and not record.is_half_day)
    half_day_days = sum(1 for record in attendance_records if record.check_out_time and record.is_half_day)
    absent_days = max(total_working_days - (present_days + half_day_days), 0)
    attendance_ratio = 0
    if total_working_days > 0:
        attendance_ratio = (present_days + (half_day_days * 0.5)) / total_working_days * 100

    # Get month navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    # Get all months for year selector
    months_list = [
        {'number': i, 'name': calendar.month_name[i], 'abbr': calendar.month_abbr[i]}
        for i in range(1, 13)
    ]
    
    # Get year range (current year ± 2 years)
    year_range = range(current_date.year - 2, current_date.year + 3)
    
    # Get layout path
    context = TemplateLayout.init(request, {
        'employee': employee,
        'calendar_data': calendar_data,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'current_date': current_date,
        'total_working_days': total_working_days,
        'present_days': present_days,
        'half_day_days': half_day_days,
        'absent_days': absent_days,
        'attendance_percentage': round(attendance_ratio, 1),
        'months_list': months_list,
        'year_range': year_range,
    })
    
    return render(request, 'employees/attendance/calendar.html', context)


@login_required
@user_passes_test(is_superadmin)
def admin_attendance_calendar(request):
    """Admin view for attendance calendar with detailed insights"""
    from datetime import datetime, timedelta
    from calendar import monthrange
    import calendar
    from django.db.models import Count, Q
    
    # Get year, month, and employee filter from query params
    current_date = timezone.now()
    year = int(request.GET.get('year', current_date.year))
    month = int(request.GET.get('month', current_date.month))
    employee_id = request.GET.get('employee')
    
    # Ensure valid month/year
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    
    # Get first and last day of the month
    first_day = datetime(year, month, 1).date()
    last_day = datetime(year, month, monthrange(year, month)[1]).date()
    
    # Get all employees
    all_employees = Employee.objects.all().order_by('name')
    
    # Filter by employee if specified
    if employee_id:
        selected_employee = get_object_or_404(Employee, id=employee_id)
        employees = [selected_employee]
    else:
        selected_employee = None
        employees = all_employees
    
    # Get all attendance records for this month
    attendance_records = Attendance.objects.filter(
        date__gte=first_day,
        date__lte=last_day
    ).select_related('employee')
    
    if employee_id:
        attendance_records = attendance_records.filter(employee_id=employee_id)
    
    # Create attendance lookup by date and employee
    attendance_by_date = {}
    for record in attendance_records:
        if record.date not in attendance_by_date:
            attendance_by_date[record.date] = []
        attendance_by_date[record.date].append(record)
    
    # Helper function to check if a date is a holiday
    def is_holiday(date_obj):
        """Check if date is a holiday (Sunday or 1st, 3rd, 5th Saturday)"""
        # Sunday is weekday 6
        if date_obj.weekday() == 6:
            return True
        
        # Saturday is weekday 5
        if date_obj.weekday() == 5:
            # Count which Saturday of the month this is
            saturday_count = 0
            for d in range(1, date_obj.day + 1):
                if datetime(date_obj.year, date_obj.month, d).weekday() == 5:
                    saturday_count += 1
            
            # 1st, 3rd, 5th Saturday are holidays
            if saturday_count in [1, 3, 5]:
                return True
        
        return False
    
    # Generate calendar data
    cal = calendar.monthcalendar(year, month)
    calendar_data = []
    
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                date_obj = datetime(year, month, day).date()
                day_attendance = attendance_by_date.get(date_obj, [])
                is_holiday_day = is_holiday(date_obj)
                
                # Count statuses
                checked_in_count = len([a for a in day_attendance if not a.check_out_time])
                half_day_count = len([a for a in day_attendance if a.check_out_time and a.is_half_day])
                checked_out_count = len([a for a in day_attendance if a.check_out_time and not a.is_half_day])
                total_present = len(day_attendance)
                
                # Calculate absent (only for past working days, not holidays)
                is_past_working_day = date_obj < current_date.date() and not is_holiday_day
                total_employees = len(employees) if not employee_id else 1
                absent_count = total_employees - total_present if is_past_working_day else 0
                
                week_data.append({
                    'day': day,
                    'date': date_obj,
                    'attendance_records': day_attendance,
                    'checked_in_count': checked_in_count,
                    'checked_out_count': checked_out_count,
                    'half_day_count': half_day_count,
                    'total_present': total_present,
                    'absent_count': absent_count,
                    'is_today': date_obj == current_date.date(),
                    'is_future': date_obj > current_date.date(),
                    'is_holiday': is_holiday_day
                })
        calendar_data.append(week_data)
    
    # Calculate monthly statistics (excluding holidays)
    total_working_days = sum(1 for week in calendar_data for day in week 
                            if day and not day['is_holiday'] and day['date'] <= current_date.date())

    if employee_id:
        employee_records = attendance_records.filter(employee_id=employee_id)
        total_present = employee_records.filter(check_out_time__isnull=False, half_day=False).count()
        total_half_days = employee_records.filter(check_out_time__isnull=False, half_day=True).count()
        total_absent = total_working_days - employee_records.count()
    else:
        total_present = attendance_records.filter(check_out_time__isnull=False, half_day=False).count()
        total_half_days = attendance_records.filter(check_out_time__isnull=False, half_day=True).count()
        total_expected = total_working_days * len(employees)
        total_absent = total_expected - attendance_records.count()
    
    # Get month navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    # Get all months for selector
    months_list = [
        {'number': i, 'name': calendar.month_name[i], 'abbr': calendar.month_abbr[i]}
        for i in range(1, 13)
    ]
    
    # Get year range
    year_range = range(current_date.year - 2, current_date.year + 3)
    
    # Get layout path
    context = TemplateLayout.init(request, {
        'calendar_data': calendar_data,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'current_date': current_date,
        'all_employees': all_employees,
        'selected_employee': selected_employee,
        'total_working_days': total_working_days,
        'total_present': total_present,
        'total_half_days': total_half_days,
        'total_absent': total_absent,
        'months_list': months_list,
        'year_range': year_range,
    })
    
    return render(request, 'employees/attendance/admin_calendar.html', context)

# Employee Password Reset Request (Public - No Login Required)
def password_reset_request(request):
    """Employee submits password reset request"""
    if request.method == 'POST':
        email_or_username = request.POST.get('email_or_username')
        reason = request.POST.get('reason', '')
        
        try:
            # Try to find employee by email or username
            employee = None
            if '@' in email_or_username:
                employee = Employee.objects.get(email=email_or_username)
            else:
                user = User.objects.get(username=email_or_username)
                employee = Employee.objects.get(user=user)
            
            # Create password reset request
            reset_request = PasswordResetRequest.objects.create(
                employee=employee,
                email=employee.email,
                reason=reason,
                status='pending'
            )
            
            messages.success(request, f'Password reset request submitted successfully! Request ID: #{reset_request.id}')
            return redirect('employees:login')
            
        except (Employee.DoesNotExist, User.DoesNotExist):
            messages.error(request, 'No employee found with this email or username.')
        except Exception as e:
            messages.error(request, f'Error submitting request: {str(e)}')
    
    return render(request, 'employees/password_reset_request.html')


# Admin Views for Password Management
@login_required
@user_passes_test(lambda u: u.is_superuser)
def password_reset_requests_list(request):
    """Admin view to see all password reset requests"""
    status_filter = request.GET.get('status', 'all')
    
    requests_query = PasswordResetRequest.objects.select_related('employee', 'processed_by').all()
    
    if status_filter != 'all':
        requests_query = requests_query.filter(status=status_filter)
    
    pending_count = PasswordResetRequest.objects.filter(status='pending').count()
    approved_count = PasswordResetRequest.objects.filter(status='approved').count()
    rejected_count = PasswordResetRequest.objects.filter(status='rejected').count()
    
    context = TemplateLayout.init(request, {
        'reset_requests': requests_query,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })
    
    return render(request, 'employees/admin/password_reset_requests.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def process_password_reset_request(request, request_id):
    """Admin processes a password reset request"""
    reset_request = get_object_or_404(PasswordResetRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        new_password = request.POST.get('new_password')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'approve' and new_password:
            # Update employee password
            employee = reset_request.employee
            employee.user.password = make_password(new_password)
            employee.user.save()
            
            # Update request
            reset_request.status = 'approved'
            reset_request.new_password = new_password  # Store temporarily for notification
            reset_request.processed_by = request.user
            reset_request.processed_at = timezone.now()
            reset_request.admin_notes = admin_notes
            reset_request.save()
            
            messages.success(request, f'Password reset approved for {employee.name}. New password: {new_password}')
            
        elif action == 'reject':
            reset_request.status = 'rejected'
            reset_request.processed_by = request.user
            reset_request.processed_at = timezone.now()
            reset_request.admin_notes = admin_notes
            reset_request.save()
            
            messages.warning(request, f'Password reset request rejected for {reset_request.employee.name}')
        
        return redirect('employees:password_reset_requests')
    
    context = TemplateLayout.init(request, {
        'reset_request': reset_request,
    })
    
    return render(request, 'employees/admin/process_password_reset.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def employee_change_password(request, employee_id):
    """Admin directly changes employee password"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        admin_notes = request.POST.get('admin_notes', '')
        
        if new_password and new_password == confirm_password:
            # Update password
            employee.user.password = make_password(new_password)
            employee.user.save()
            
            # Create a record of this change
            PasswordResetRequest.objects.create(
                employee=employee,
                email=employee.email,
                reason=f'Password changed by admin: {admin_notes}',
                status='approved',
                new_password=new_password,
                processed_by=request.user,
                processed_at=timezone.now(),
                admin_notes=admin_notes
            )
            
            messages.success(request, f'Password updated successfully for {employee.name}')
            return redirect('employees:employee_detail', pk=employee.id)
        else:
            messages.error(request, 'Passwords do not match!')
    
    context = TemplateLayout.init(request, {
        'employee': employee,
    })
    
    return render(request, 'employees/admin/change_employee_password.html', context)