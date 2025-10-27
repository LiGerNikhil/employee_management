from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

from .models import Employee, Attendance
from .forms import EmployeeForm, EmployeeUpdateForm


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
            messages.error(request, 'Invalid email/username or password.')
            return render(request, 'employees/auth/login.html', self.get_context_data())

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
    """Admin dashboard view"""
    from django.utils import timezone

    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'total_employees': Employee.objects.count(),
        'today_checkins': Attendance.objects.filter(date=timezone.now().date()).count(),
        'recent_employees': Employee.objects.order_by('-created_at')[:5],
        'today_attendance': Attendance.objects.filter(date=timezone.now().date()).select_related('employee')[:10],
        'today': timezone.now().date(),
        'date_today': timezone.now().date(),
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
                week_data.append({'day': None, 'attendance': None, 'is_today': False})
            else:
                day_date = datetime.date(current_year, current_month, day)
                attendance = attendance_dict.get(day)
                is_today = day_date == today
                week_data.append({
                    'day': day,
                    'attendance': attendance,
                    'is_today': is_today,
                    'is_past': day_date < today,
                    'is_future': day_date > today
                })
        calendar_data.append(week_data)

    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
        'has_checked_in_today': Attendance.has_checked_in_today(employee),
        'today_attendance': Attendance.objects.filter(
            employee=employee,
            date=timezone.now().date()
        ).first(),
        'recent_attendance': Attendance.objects.filter(employee=employee).order_by('-date')[:5],
        'today': today,
        'current_time': timezone.now(),
        'calendar_data': calendar_data,
        'month_name': month_name_str,
        'current_month': current_month,
        'current_year': current_year,
        'total_month_attendance': month_attendance.count(),
        'day_names': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    })
    return render(request, 'employees/dashboard/employee_dashboard.html', context)


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
        # Get password directly from form's cleaned_data (form is already validated)
        password = form.cleaned_data.get('password')

        if not password:
            messages.error(self.request, 'Password is required to create employee account.')
            return self.form_invalid(form)

        # Check if password meets minimum requirements
        if len(password) < 8:
            messages.error(self.request, 'Password must be at least 8 characters long.')
            return self.form_invalid(form)

        # Create user account for the employee
        user = User.objects.create_user(
            username=form.cleaned_data['email'],
            email=form.cleaned_data['email'],
            first_name=form.cleaned_data['name'],
            password=password
        )

        # Link employee to user and save
        employee = form.save(commit=False)
        employee.user = user
        employee.save()

        messages.success(self.request, 'Employee created successfully!')
        return super().form_valid(form)


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

    def get_success_url(self):
        messages.success(self.request, 'Employee updated successfully!')
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


# Employee Detail View (for super-admins to view employee details)
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
@login_required
@user_passes_test(is_employee)
def employee_profile(request):
    """Employee profile view"""
    employee = request.user.employee_profile
    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
    })
    return render(request, 'employees/employee_profile.html', context)


# Check-in Views
@login_required
@user_passes_test(is_employee)
def check_in(request):
    """Employee check-in view"""
    employee = request.user.employee_profile

    # Check if already checked in today
    if Attendance.has_checked_in_today(employee):
        messages.warning(request, 'You have already checked in today!')
        return redirect('employees:employee_dashboard')

    if request.method == 'POST':
        # Create attendance record
        Attendance.objects.create(employee=employee)
        messages.success(request, 'Check-in successful!')
        return redirect('employees:employee_dashboard')

    context = TemplateLayout.init(self={}, context={})
    context.update({
        'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
        'employee': employee,
        'has_checked_in_today': Attendance.has_checked_in_today(employee),
        'date_today': timezone.now().date(),
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
        context.update({
            'layout_path': TemplateHelper.set_layout('layout_vertical.html', context),
            'today_count': Attendance.objects.filter(date=timezone.now().date()).count(),
            'unique_employees': Attendance.objects.filter(
                date=timezone.now().date()
            ).values('employee').distinct().count(),
            'total_employees': Employee.objects.count(),
            'today': timezone.now().date(),
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
