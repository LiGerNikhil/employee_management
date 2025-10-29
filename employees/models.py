from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import json


class Employee(models.Model):
    """Employee model representing an employee in the system"""

    # Basic Information
    name = models.CharField(max_length=100, help_text="Employee's first name")
    full_name = models.CharField(max_length=200, help_text="Employee's full name")

    # Contact Information
    contact = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')],
        help_text="Employee's contact number"
    )
    email = models.EmailField(unique=True, help_text="Employee's email address")

    # Financial Information
    aadhar_card_number = models.CharField(
        max_length=12,
        validators=[RegexValidator(r'^\d{12}$', 'Aadhar number must be exactly 12 digits.')],
        help_text="Employee's Aadhar card number"
    )
    account_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\d{9,18}$', 'Account number must be 9-18 digits.')],
        help_text="Employee's bank account number"
    )
    ifsc_code = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^[A-Z]{4}0[A-Z0-9]{6}$', 'Enter a valid IFSC code.')],
        help_text="Bank IFSC code"
    )
    pan_card = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', 'Enter a valid PAN card number.')],
        help_text="Employee's PAN card number"
    )

    # Address Information
    current_address = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Current residential address"
    )
    permanent_address = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Permanent residential address"
    )
    
    # Relative Information
    relative_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Name of the relative"
    )
    relative_contact = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')],
        help_text="Contact number of the relative"
    )
    relation_with_employee = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Relationship with the employee (e.g., Father, Mother, Spouse)"
    )
    
    # Profile Picture
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text="Employee's profile picture"
    )
    
    # Face Recognition Data
    face_encoding = models.TextField(
        blank=True,
        null=True,
        help_text="JSON-encoded face encoding data for recognition"
    )
    face_registered = models.BooleanField(
        default=False,
        help_text="Whether face recognition data has been registered"
    )
    face_registered_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When face was registered for recognition"
    )

    # User Account (linked to Django's User model)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        help_text="Associated Django user account"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'full_name']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

    def __str__(self):
        return f"{self.name} {self.full_name}"

    def save(self, *args, **kwargs):
        # Auto-generate username if not set (only for new users)
        if self.user and not self.user.username:
            self.user.username = self.email
        super().save(*args, **kwargs)
    
    def get_face_encoding(self):
        """Get face encoding as numpy array"""
        if not self.face_encoding:
            return None
        try:
            import numpy as np
            encoding_data = json.loads(self.face_encoding)
            return np.array(encoding_data)
        except (json.JSONDecodeError, ValueError, ImportError):
            return None
    
    def set_face_encoding(self, encoding_array):
        """Set face encoding from numpy array"""
        if encoding_array is not None:
            self.face_encoding = json.dumps(encoding_array.tolist())
            self.face_registered = True
            from django.utils import timezone
            if not self.face_registered_at:
                self.face_registered_at = timezone.now()
        else:
            self.face_encoding = None
            self.face_registered = False
            self.face_registered_at = None


class Attendance(models.Model):
    """Attendance model for tracking employee check-ins"""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Employee who checked in"
    )
    check_in_time = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when employee checked in"
    )
    date = models.DateField(
        help_text="Date of the check-in"
    )
    check_in_photo = models.ImageField(
        upload_to='checkin_photos/',
        blank=True,
        null=True,
        help_text="Photo taken during check-in for verification"
    )
    check_out_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when employee checked out"
    )
    check_out_photo = models.ImageField(
        upload_to='checkout_photos/',
        blank=True,
        null=True,
        help_text="Photo taken during check-out for verification"
    )
    check_in_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        help_text="Latitude of check-in location"
    )
    check_in_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        help_text="Longitude of check-in location"
    )
    check_out_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        help_text="Latitude of check-out location"
    )
    check_out_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        help_text="Longitude of check-out location"
    )

    class Meta:
        ordering = ['-check_in_time']
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        # Ensure only one check-in per employee per day
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee.name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def duration(self):
        """Calculate duration between check-in and check-out"""
        if not self.check_out_time:
            return "-"
        
        delta = self.check_out_time - self.check_in_time
        total_seconds = int(delta.total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    @property
    def duration_hours(self):
        """Calculate duration in decimal hours"""
        if not self.check_out_time:
            return 0
        
        delta = self.check_out_time - self.check_in_time
        hours = delta.total_seconds() / 3600
        return round(hours, 2)

    @classmethod
    def has_checked_in_today(cls, employee):
        """Check if employee has already checked in today"""
        from django.utils import timezone
        today = timezone.now().date()
        return cls.objects.filter(
            employee=employee,
            date=today
        ).exists()


class AttendanceLog(models.Model):
    """Log all attendance activities including successful and failed attempts"""
    
    ACTION_CHOICES = [
        ('check_in_success', 'Check-In Success'),
        ('check_in_failed', 'Check-In Failed'),
        ('check_out_success', 'Check-Out Success'),
        ('check_out_failed', 'Check-Out Failed'),
    ]
    
    FAILURE_REASONS = [
        ('no_face_detected', 'No Face Detected'),
        ('multiple_faces', 'Multiple Faces Detected'),
        ('face_not_matched', 'Face Not Matched'),
        ('already_checked_in', 'Already Checked In'),
        ('not_checked_in', 'Not Checked In Yet'),
        ('already_checked_out', 'Already Checked Out'),
        ('no_face_registered', 'Face Not Registered'),
        ('photo_required', 'Photo Required'),
        ('other', 'Other Error'),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendance_logs',
        help_text="Employee who attempted the action"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type of action attempted"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the action was attempted"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether the action was successful"
    )
    failure_reason = models.CharField(
        max_length=30,
        choices=FAILURE_REASONS,
        blank=True,
        null=True,
        help_text="Reason for failure if unsuccessful"
    )
    confidence = models.FloatField(
        blank=True,
        null=True,
        help_text="Face recognition confidence percentage"
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP address of the request"
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="Browser user agent"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes or error messages"
    )
    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='logs',
        help_text="Related attendance record if successful"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Attendance Log'
        verbose_name_plural = 'Attendance Logs'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['employee', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.employee.name} - {self.get_action_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def status_badge(self):
        """Return Bootstrap badge class based on status"""
        if self.success:
            return 'success'
        else:
            return 'danger'
    
    @property
    def action_icon(self):
        """Return icon based on action type"""
        icons = {
            'check_in_success': 'bx-log-in',
            'check_in_failed': 'bx-log-in',
            'check_out_success': 'bx-log-out',
            'check_out_failed': 'bx-log-out',
        }
        return icons.get(self.action, 'bx-time')


class Ticket(models.Model):
    """Support ticket system for employees to raise issues"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('reopened', 'Reopened'),
    ]
    
    CATEGORY_CHOICES = [
        ('attendance', 'Attendance Issue'),
        ('leave', 'Leave Request'),
        ('payroll', 'Payroll Issue'),
        ('technical', 'Technical Support'),
        ('hr', 'HR Related'),
        ('facility', 'Facility/Infrastructure'),
        ('other', 'Other'),
    ]
    
    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Auto-generated ticket number"
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='tickets',
        help_text="Employee who raised the ticket"
    )
    subject = models.CharField(
        max_length=200,
        help_text="Brief subject of the issue"
    )
    description = models.TextField(
        help_text="Detailed description of the issue"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        help_text="Category of the ticket"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='open',
        help_text="Current status"
    )
    attachment = models.FileField(
        upload_to='ticket_attachments/',
        blank=True,
        null=True,
        help_text="Optional file attachment"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the ticket was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update time"
    )
    resolved_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the ticket was resolved"
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='resolved_tickets',
        help_text="Admin who resolved the ticket"
    )
    admin_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes by admin"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['employee', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.ticket_number} - {self.subject} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate ticket number: TKT-YYYYMMDD-XXXX
            from django.utils import timezone
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            
            # Get count of tickets created today
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            count = Ticket.objects.filter(created_at__gte=today_start).count() + 1
            
            self.ticket_number = f"TKT-{date_str}-{count:04d}"
        
        # Auto-set resolved_at when status changes to resolved
        if self.status == 'resolved' and not self.resolved_at:
            from django.utils import timezone
            self.resolved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def status_color(self):
        """Return color class based on status"""
        colors = {
            'open': 'primary',
            'in_progress': 'warning',
            'resolved': 'success',
            'closed': 'secondary',
            'reopened': 'danger',
        }
        return colors.get(self.status, 'secondary')
    
    @property
    def priority_color(self):
        """Return color class based on priority"""
        colors = {
            'low': 'info',
            'medium': 'primary',
            'high': 'warning',
            'urgent': 'danger',
        }
        return colors.get(self.priority, 'secondary')
    
    @property
    def category_icon(self):
        """Return icon based on category"""
        icons = {
            'attendance': 'bx-time-five',
            'leave': 'bx-calendar-x',
            'payroll': 'bx-money',
            'technical': 'bx-wrench',
            'hr': 'bx-user-voice',
            'facility': 'bx-building',
            'other': 'bx-help-circle',
        }
        return icons.get(self.category, 'bx-help-circle')
    
    @property
    def is_overdue(self):
        """Check if ticket is overdue (open for more than 3 days)"""
        if self.status in ['resolved', 'closed']:
            return False
        from django.utils import timezone
        from datetime import timedelta
        return (timezone.now() - self.created_at) > timedelta(days=3)


class TicketComment(models.Model):
    """Comments/replies on tickets"""
    
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="Related ticket"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User who posted the comment"
    )
    comment = models.TextField(
        help_text="Comment text"
    )
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal note (visible only to admins)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the comment was posted"
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Ticket Comment'
        verbose_name_plural = 'Ticket Comments'
    
    def __str__(self):
        return f"Comment on {self.ticket.ticket_number} by {self.user.username}"
    
    @property
    def is_admin(self):
        """Check if comment is from admin"""
        return self.user.is_superuser


class PasswordResetRequest(models.Model):
    """Model to track employee password reset requests"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='password_reset_requests',
        help_text="Employee requesting password reset"
    )
    email = models.EmailField(help_text="Email address used for request")
    reason = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Reason for password reset request"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Status of the request"
    )
    new_password = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="New password set by admin (temporary)"
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_password_requests',
        help_text="Admin who processed the request"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was processed"
    )
    admin_notes = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Admin notes about the request"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Password Reset Request'
        verbose_name_plural = 'Password Reset Requests'
    
    def __str__(self):
        return f"Password reset request for {self.employee.name} - {self.status}"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'
