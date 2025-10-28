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

    class Meta:
        ordering = ['-check_in_time']
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        # Ensure only one check-in per employee per day
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee.name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def has_checked_in_today(cls, employee):
        """Check if employee has already checked in today"""
        from django.utils import timezone
        today = timezone.now().date()
        return cls.objects.filter(
            employee=employee,
            date=today
        ).exists()
