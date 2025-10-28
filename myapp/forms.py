from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group
from django.db.models import F
from .models import DonorProfile, AdminProfile, PatientProfile, BloodRequest, BloodDonation, Timeslot, Notification


class DonorRegistrationForm(UserCreationForm):
    """
    Form for donor registration including profile fields.
    """
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    blood_group = forms.ChoiceField(
        choices=[
            ('', 'Select Blood Group'),
            ('A+', 'A+'),
            ('A-', 'A-'),
            ('B+', 'B+'),
            ('B-', 'B-'),
            ('O+', 'O+'),
            ('O-', 'O-'),
            ('AB+', 'AB+'),
            ('AB-', 'AB-'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    contact_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your contact number'
        })
    )
    age = forms.IntegerField(
        min_value=18,
        max_value=65,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your age'
        })
    )
    gender = forms.ChoiceField(
        choices=[
            ('', 'Select Gender'),
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    weight = forms.IntegerField(
        min_value=40,
        max_value=150,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Weight in kg'
        })
    )
    height = forms.IntegerField(
        min_value=140,
        max_value=220,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Height in cm'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your address',
            'rows': 3
        })
    )
    medical_conditions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Any medical conditions (optional)',
            'rows': 2
        })
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Use email as username and store email
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create donor profile
            DonorProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                age=self.cleaned_data.get('age'),
                blood_group=self.cleaned_data['blood_group'],
                contact_number=self.cleaned_data['contact_number'],
                gender=self.cleaned_data.get('gender'),
                weight=self.cleaned_data.get('weight'),
                height=self.cleaned_data.get('height'),
                address=self.cleaned_data.get('address', ''),
                medical_conditions=self.cleaned_data.get('medical_conditions', ''),
            )
        return user


        self.fields['username'].widget.attrs['placeholder'] = 'Enter your username'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['placeholder'] = 'Enter your password'


class AdminLoginForm(AuthenticationForm):
    """
    Form for admin login (Super Admin and Secondary Admin).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'id': 'username',
            'placeholder': 'Enter admin username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'id': 'password',
            'placeholder': 'Enter admin password'
        })


class AdminCreationForm(forms.ModelForm):
    """
    Form for creating new admin users by superuser.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    admin_type = forms.ChoiceField(
        choices=[
            ('secondary', 'Secondary Admin'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text='Only superusers can create other superusers'
    )

    class Meta:
        model = AdminProfile
        fields = ['full_name', 'employee_id', 'department', 'phone_number']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter employee ID'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
        }

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if AdminProfile.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError('Employee ID already exists.')
        return employee_id

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        # Create the User first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            is_active=False,  # Inactive until super admin grants permission
            first_name=self.cleaned_data['full_name'].split()[0] if self.cleaned_data['full_name'] else '',
            last_name=' '.join(self.cleaned_data['full_name'].split()[1:]) if len(self.cleaned_data['full_name'].split()) > 1 else ''
        )

        # Create the AdminProfile
        admin_profile = super().save(commit=False)
        admin_profile.user = user
        admin_profile.is_active = False  # Require approval
        admin_profile.created_by = self.created_by  # Set by the view

        if commit:
            admin_profile.save()

            # Add user to the appropriate group
            if self.cleaned_data['admin_type'] == 'secondary':
                secondary_group = Group.objects.get(name='Secondary Admin')
                user.groups.add(secondary_group)

        return admin_profile


class AdminRegistrationForm(forms.ModelForm):
    """
    Form for admin registration by potential admins.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = AdminProfile
        fields = ['full_name', 'department', 'employee_id']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your department'
            }),
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your employee ID'
            }),
        }

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if AdminProfile.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError('Employee ID already exists.')
        return employee_id

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        # Create the User first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            is_active=False  # Pending approval
        )

        # Create the AdminProfile
        admin_profile = super().save(commit=False)
        admin_profile.user = user
        admin_profile.is_active = False  # Pending approval

        if commit:
            admin_profile.save()

        return admin_profile


class AdminProfileUpdateForm(forms.ModelForm):
    """
    Form for updating admin profiles.
    """
    class Meta:
        model = AdminProfile
        fields = ['full_name', 'employee_id', 'department', 'phone_number', 'is_active']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter employee ID'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make employee_id read-only for existing profiles
        if self.instance and self.instance.pk:
            self.fields['employee_id'].widget.attrs['readonly'] = True


class PatientRegistrationForm(UserCreationForm):
    """
    Form for patient registration including profile fields.
    """
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your full name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email'
        })
    )
    blood_group = forms.ChoiceField(
        choices=[
            ('', 'Select Blood Group'),
            ('A+', 'A+'),
            ('A-', 'A-'),
            ('B+', 'B+'),
            ('B-', 'B-'),
            ('O+', 'O+'),
            ('O-', 'O-'),
            ('AB+', 'AB+'),
            ('AB-', 'AB-'),
        ],
        widget=forms.Select()
    )
    contact_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your contact number'
        })
    )
    age = forms.IntegerField(
        min_value=18,
        max_value=65,
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Enter your age'
        })
    )
    gender = forms.ChoiceField(
        choices=[
            ('', 'Select Gender'),
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        required=False,
        widget=forms.Select()
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter your address',
            'rows': 3
        })
    )
    emergency_contact = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Emergency contact number'
        })
    )
    medical_history = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Medical history (optional)',
            'rows': 2
        })
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create patient profile
            PatientProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                age=self.cleaned_data.get('age'),
                blood_group=self.cleaned_data['blood_group'],
                contact_number=self.cleaned_data['contact_number'],
                gender=self.cleaned_data.get('gender'),
                address=self.cleaned_data.get('address', ''),
                emergency_contact=self.cleaned_data.get('emergency_contact', ''),
                medical_history=self.cleaned_data.get('medical_history', ''),
            )
        return user


class PatientLoginForm(AuthenticationForm):
    """
    Form for patient login.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Enter your username'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['placeholder'] = 'Enter your password'

class BloodRequestForm(forms.ModelForm):
    """
    Form for patients to request blood.
    """
    class Meta:
        model = BloodRequest
        fields = ['blood_group', 'quantity']
        widgets = {
            'blood_group': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter number of units'
            }),
        }

class TimeslotForm(forms.ModelForm):
    """
    Form for creating donation timeslots.
    """
    class Meta:
        model = Timeslot
        fields = ['date', 'start_time', 'end_time', 'capacity']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum appointments'
            }),
        }


class AppointmentBookingForm(forms.Form):
    """
    Form for donors to book appointments.
    """
    timeslot = forms.ModelChoiceField(
        queryset=Timeslot.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        empty_label="Select a timeslot"
    )

    def __init__(self, *args, **kwargs):
        self.donor = kwargs.pop('donor', None)
        super().__init__(*args, **kwargs)
        # Filter available timeslots
        available_timeslots = Timeslot.objects.filter(
            is_active=True,
            booked_count__lt=F('capacity')
        ).exclude(
            donations__donor=self.donor,
            donations__status__in=['waiting', 'confirmed']
        )
        self.fields['timeslot'].queryset = available_timeslots


class BloodDonationForm(forms.ModelForm):
    """
    Form for donors to log blood donations.
    """
    class Meta:
        model = BloodDonation
        fields = ['quantity', 'donation_date']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter number of units'
            }),
            'donation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class NotificationForm(forms.ModelForm):
    """
    Form for sending notifications to donors.
    """
    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Notification title'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Notification message',
                'rows': 4
            }),
            'notification_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
