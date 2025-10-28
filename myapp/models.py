from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class DonorProfile(models.Model):
    """
    Profile model for blood donors extending Django's User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')

    full_name = models.CharField(max_length=100, help_text="Donor's full name")
    age = models.PositiveIntegerField(blank=True, null=True, help_text="Donor's age")
    blood_group = models.CharField(
        max_length=3,
        choices=[
            ('A+', 'A+'),
            ('A-', 'A-'),
            ('B+', 'B+'),
            ('B-', 'B-'),
            ('O+', 'O+'),
            ('O-', 'O-'),
            ('AB+', 'AB+'),
            ('AB-', 'AB-'),
        ],
        help_text="Blood group"
    )
    contact_number = models.CharField(max_length=15, help_text="Contact phone number")
    address = models.TextField(blank=True, help_text="Donor's address")
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        blank=True,
        help_text="Gender"
    )
    weight = models.PositiveIntegerField(blank=True, null=True, help_text="Weight in kg")
    height = models.PositiveIntegerField(blank=True, null=True, help_text="Height in cm")
    medical_conditions = models.TextField(blank=True, help_text="Any medical conditions")
    next_eligible_date = models.DateField(null=True, blank=True, help_text="Next eligible donation date (90 days after last donation)")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Donor Profile"
        verbose_name_plural = "Donor Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.user.username}) - {self.blood_group}"


class PatientProfile(models.Model):
    """
    Profile model for patients who need blood transfusions.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')

    full_name = models.CharField(max_length=100, help_text="Patient's full name")
    age = models.PositiveIntegerField(help_text="Patient's age")
    blood_group = models.CharField(
        max_length=3,
        choices=[
            ('A+', 'A+'),
            ('A-', 'A-'),
            ('B+', 'B+'),
            ('B-', 'B-'),
            ('O+', 'O+'),
            ('O-', 'O-'),
            ('AB+', 'AB+'),
            ('AB-', 'AB-'),
        ],
        help_text="Required blood group"
    )
    contact_number = models.CharField(max_length=15, help_text="Contact phone number")
    address = models.TextField(blank=True, help_text="Patient's address")
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        blank=True,
        help_text="Gender"
    )
    emergency_contact = models.CharField(max_length=15, blank=True, help_text="Emergency contact number")
    medical_history = models.TextField(blank=True, help_text="Medical history and conditions")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patient Profile"
        verbose_name_plural = "Patient Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.user.username}) - {self.blood_group}"


class AdminProfile(models.Model):
    """
    Profile model for admin users with hierarchical permissions.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')

    full_name = models.CharField(max_length=100, help_text="Admin's full name")
    employee_id = models.CharField(max_length=20, unique=True, help_text="Unique employee ID")
    department = models.CharField(max_length=50, blank=True, help_text="Department")
    phone_number = models.CharField(max_length=15, blank=True, help_text="Contact phone number")

    # Admin level (set by groups, but stored here for reference)
    is_super_admin = models.BooleanField(default=False, help_text="Super admin with full privileges")
    is_secondary_admin = models.BooleanField(default=False, help_text="Secondary admin with limited privileges")

    # Status
    is_active = models.BooleanField(default=True, help_text="Whether this admin account is active")

    # Audit fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_admins',
        help_text="Admin who created this account"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin Profile"
        verbose_name_plural = "Admin Profiles"
        ordering = ['-created_at']

    def __str__(self):
        admin_type = "Super Admin" if self.is_super_admin else "Secondary Admin"
        return f"{self.full_name} ({self.employee_id}) - {admin_type}"

    def save(self, *args, **kwargs):
        # Always sync admin type based on user's current groups and superuser status
        # This ensures flags are always up to date
        if self.user.is_superuser or self.user.groups.filter(name='Super Admin').exists():
            self.is_super_admin = True
            self.is_secondary_admin = False
        elif self.user.groups.filter(name='Secondary Admin').exists():
            self.is_super_admin = False
            self.is_secondary_admin = True
        else:
            # If user is neither superuser nor in any admin groups, reset flags
            self.is_super_admin = False
            self.is_secondary_admin = False

        super().save(*args, **kwargs)

        # Sync is_active with user account
        if self.user.is_active != self.is_active:
            self.user.is_active = self.is_active
            self.user.save(update_fields=['is_active'])


class BloodRequest(models.Model):
    """
    Model for patients to request blood.
    """
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='blood_requests')
    blood_group = models.CharField(max_length=3, choices=PatientProfile.blood_group.field.choices)
    quantity = models.PositiveIntegerField(help_text="Number of units required")
    fulfilled_quantity = models.PositiveIntegerField(default=0, help_text="Number of units actually fulfilled")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('fulfilled', 'Fulfilled'),
        ],
        default='pending'
    )
    # Link to the donor who fulfilled the request
    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fulfilled_requests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request from {self.patient.full_name} for {self.quantity} units of {self.blood_group}"


class Timeslot(models.Model):
    """
    Model for scheduling donation appointments.
    """
    date = models.DateField(help_text="Appointment date")
    start_time = models.TimeField(help_text="Start time of the timeslot")
    end_time = models.TimeField(help_text="End time of the timeslot")
    capacity = models.PositiveIntegerField(default=10, help_text="Maximum number of appointments for this timeslot")
    booked_count = models.PositiveIntegerField(default=0, help_text="Number of appointments already booked")
    is_active = models.BooleanField(default=True, help_text="Whether this timeslot is available for booking")

    class Meta:
        verbose_name = "Timeslot"
        verbose_name_plural = "Timeslots"
        ordering = ['date', 'start_time']
        unique_together = ['date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time} ({self.booked_count}/{self.capacity})"

    @property
    def available_slots(self):
        return self.capacity - self.booked_count

    @property
    def booked(self):
        return self.booked_count

    def is_available(self):
        return self.is_active and self.available_slots > 0


class BloodDonation(models.Model):
    """
    Model to track blood donations from donors with extended workflow.
    """
    donor = models.ForeignKey(DonorProfile, on_delete=models.CASCADE, related_name='donations')
    quantity = models.PositiveIntegerField(help_text="Number of units donated")
    donation_date = models.DateField()
    appointment_date = models.DateField(null=True, blank=True, help_text="Scheduled appointment date")
    timeslot = models.ForeignKey(Timeslot, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    status = models.CharField(
        max_length=20,
        choices=[
            ('waiting', 'Waiting for Appointment'),
            ('confirmed', 'Appointment Confirmed'),
            ('completed', 'Donation Completed'),
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='waiting'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Blood Donation"
        verbose_name_plural = "Blood Donations"
        ordering = ['-created_at']

    def __str__(self):
        return f"Donation from {self.donor.full_name} of {self.quantity} units on {self.donation_date}"

    def save(self, *args, **kwargs):
        # Update donor's next eligible date when donation is completed
        if self.status == 'completed' and not self.donor.next_eligible_date:
            from datetime import timedelta
            self.donor.next_eligible_date = self.donation_date + timedelta(days=90)
            self.donor.save(update_fields=['next_eligible_date'])
        super().save(*args, **kwargs)


class BloodBank(models.Model):
    """
    Model to store donated blood units in the blood bank.
    """
    donation = models.OneToOneField(BloodDonation, on_delete=models.CASCADE, related_name='blood_unit')
    blood_group = models.CharField(max_length=3, choices=DonorProfile.blood_group.field.choices)
    quantity = models.PositiveIntegerField(help_text="Number of units stored")
    storage_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(help_text="Expiry date of the blood unit")
    status = models.CharField(
        max_length=20,
        choices=[
            ('available', 'Available'),
            ('reserved', 'Reserved'),
            ('used', 'Used'),
            ('expired', 'Expired'),
            ('discarded', 'Discarded'),
        ],
        default='available'
    )
    location = models.CharField(max_length=50, blank=True, help_text="Storage location in blood bank")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Blood Bank Unit"
        verbose_name_plural = "Blood Bank Units"
        ordering = ['-storage_date']

    def __str__(self):
        return f"{self.blood_group} - {self.quantity} units (Stored: {self.storage_date})"


class Notification(models.Model):
    """
    Model for notifications sent to donors and patients.
    """
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200, help_text="Notification title")
    message = models.TextField(help_text="Notification message")
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('appointment', 'Appointment'),
            ('confirmation', 'Confirmation'),
            ('reminder', 'Reminder'),
            ('status_update', 'Status Update'),
            ('general', 'General'),
        ],
        default='general'
    )
    is_read = models.BooleanField(default=False, help_text="Whether the notification has been read")
    related_donation = models.ForeignKey(BloodDonation, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_request = models.ForeignKey(BloodRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.username}: {self.title}"

