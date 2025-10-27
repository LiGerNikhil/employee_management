from django import forms
from django.contrib.auth.models import User
from .models import Employee


class EmployeeForm(forms.ModelForm):
    """Form for creating new employees"""

    # Additional fields for user creation
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        min_length=8,
        help_text="Password for the employee's login account (minimum 8 characters)"
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        help_text="Confirm the password"
    )

    class Meta:
        model = Employee
        fields = [
            'name', 'full_name', 'email', 'contact',
            'aadhar_card_number', 'account_number', 'ifsc_code', 'pan_card',
            'profile_picture', 'password'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter contact number'
            }),
            'aadhar_card_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter 12-digit Aadhar number'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bank account number'
            }),
            'ifsc_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter IFSC code'
            }),
            'pan_card': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter PAN card number'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        help_texts = {
            'name': 'Employee\'s first name',
            'full_name': 'Employee\'s complete name',
            'email': 'Email address (will be used as username)',
            'contact': 'Contact phone number',
            'aadhar_card_number': '12-digit Aadhar card number',
            'account_number': 'Bank account number (9-18 digits)',
            'ifsc_code': '11-character IFSC code',
            'pan_card': '10-character PAN card number (e.g., ABCDE1234F)',
            'profile_picture': 'Upload profile picture (optional)',
        }

    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_password(self):
        """Validate password strength"""
        password = self.cleaned_data.get('password')

        if password:
            if len(password) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')

            # Check for at least one number and one letter
            if not any(char.isdigit() for char in password):
                raise forms.ValidationError('Password must contain at least one number.')

            if not any(char.isalpha() for char in password):
                raise forms.ValidationError('Password must contain at least one letter.')

        return password

    def clean_confirm_password(self):
        """Validate password confirmation"""
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')

        return confirm_password

    def clean_aadhar_card_number(self):
        """Validate Aadhar number format"""
        aadhar = self.cleaned_data.get('aadhar_card_number')
        if len(aadhar) != 12 or not aadhar.isdigit():
            raise forms.ValidationError('Aadhar number must be exactly 12 digits.')
        return aadhar

    def clean_pan_card(self):
        """Validate PAN card format"""
        pan = self.cleaned_data.get('pan_card').upper()
        if len(pan) != 10:
            raise forms.ValidationError('PAN card number must be exactly 10 characters.')

        # PAN format: 5 letters, 4 numbers, 1 letter
        if not (pan[:5].isalpha() and pan[5:9].isdigit() and pan[9].isalpha()):
            raise forms.ValidationError('Invalid PAN card format. Should be ABCDE1234F.')

        return pan

    def clean_ifsc_code(self):
        """Validate IFSC code format"""
        ifsc = self.cleaned_data.get('ifsc_code').upper()
        if len(ifsc) != 11:
            raise forms.ValidationError('IFSC code must be exactly 11 characters.')

        # IFSC format: 4 letters, 0, 6 alphanumeric
        if not (ifsc[:4].isalpha() and ifsc[4] == '0' and ifsc[5:].isalnum()):
            raise forms.ValidationError('Invalid IFSC code format.')

        return ifsc

    def save(self, commit=True):
        """Save the employee"""
        # Remove password fields from cleaned_data before saving Employee
        self.cleaned_data.pop('password', None)
        self.cleaned_data.pop('confirm_password', None)

        # Save employee
        return super().save(commit=commit)


class EmployeeUpdateForm(forms.ModelForm):
    """Form for updating existing employees"""

    class Meta:
        model = Employee
        fields = [
            'name', 'full_name', 'email', 'contact',
            'aadhar_card_number', 'account_number', 'ifsc_code', 'pan_card',
            'profile_picture'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter contact number'
            }),
            'aadhar_card_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter 12-digit Aadhar number'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bank account number'
            }),
            'ifsc_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter IFSC code'
            }),
            'pan_card': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter PAN card number'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        help_texts = {
            'name': 'Employee\'s first name',
            'full_name': 'Employee\'s complete name',
            'email': 'Email address (will be used as username)',
            'contact': 'Contact phone number',
            'aadhar_card_number': '12-digit Aadhar card number',
            'account_number': 'Bank account number (9-18 digits)',
            'ifsc_code': '11-character IFSC code',
            'pan_card': '10-character PAN card number (e.g., ABCDE1234F)',
            'profile_picture': 'Upload new profile picture (optional)',
        }

    def clean_email(self):
        """Validate email uniqueness (excluding current user)"""
        email = self.cleaned_data.get('email')
        employee = self.instance

        # Check if email is different from current
        if employee.user.email != email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('A user with this email already exists.')

        return email

    def clean_aadhar_card_number(self):
        """Validate Aadhar number format"""
        aadhar = self.cleaned_data.get('aadhar_card_number')
        if len(aadhar) != 12 or not aadhar.isdigit():
            raise forms.ValidationError('Aadhar number must be exactly 12 digits.')
        return aadhar

    def clean_pan_card(self):
        """Validate PAN card format"""
        pan = self.cleaned_data.get('pan_card').upper()
        if len(pan) != 10:
            raise forms.ValidationError('PAN card number must be exactly 10 characters.')

        # PAN format: 5 letters, 4 numbers, 1 letter
        if not (pan[:5].isalpha() and pan[5:9].isdigit() and pan[9].isalpha()):
            raise forms.ValidationError('Invalid PAN card format. Should be ABCDE1234F.')

        return pan

    def clean_ifsc_code(self):
        """Validate IFSC code format"""
        ifsc = self.cleaned_data.get('ifsc_code').upper()
        if len(ifsc) != 11:
            raise forms.ValidationError('IFSC code must be exactly 11 characters.')

        # IFSC format: 4 letters, 0, 6 alphanumeric
        if not (ifsc[:4].isalpha() and ifsc[4] == '0' and ifsc[5:].isalnum()):
            raise forms.ValidationError('Invalid IFSC code format.')

        return ifsc


class LoginForm(forms.Form):
    """Login form for authentication"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email or username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
