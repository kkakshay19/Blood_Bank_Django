from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .forms import DonorRegistrationForm, AdminLoginForm, AdminRegistrationForm, PatientRegistrationForm, BloodRequestForm, BloodDonationForm, TimeslotForm, AppointmentBookingForm, NotificationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import DonorProfile, AdminProfile, PatientProfile, BloodRequest, BloodDonation, Timeslot, BloodBank, Notification
from django.db.models import F, Case, When, Value, FloatField
from datetime import datetime, timedelta

def index(request):
    """Homepage view that renders the main landing page"""
    return render(request, 'index.html')


def donor_view(request):
    """Donor section view with login and register forms."""
    if request.user.is_authenticated and hasattr(request.user, 'donor_profile'):
        return redirect('donor_dashboard')

    active_form = 'login'
    login_form = AuthenticationForm()
    register_form = DonorRegistrationForm()

    if request.method == 'POST':
        if 'login' in request.POST:
            # Handle login
            data = request.POST.copy()
            entered_username = data.get('username', '')
            if '@' in entered_username:
                email_user = User.objects.filter(email__iexact=entered_username).first()
                if email_user:
                    data['username'] = email_user.username  # Use the actual username for authentication

            login_form = AuthenticationForm(data=data)
            if login_form.is_valid():
                user = login_form.get_user()
                if user is not None and user.is_active and hasattr(user, 'donor_profile'):
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('donor_dashboard')
                else:
                    messages.error(request, 'Invalid credentials or not a donor account.')
            else:
                messages.error(request, 'Invalid email or password. Please try again.')
            active_form = 'login'
        elif 'register' in request.POST:
            # Handle registration
            register_form = DonorRegistrationForm(request.POST)
            if register_form.is_valid():
                register_form.save()
                messages.success(request, 'Registration successful! Please log in to continue.')
                return redirect('donor')
            active_form = 'register'

    # Customize login form fields
    login_form.fields['username'].widget.attrs.update({
        'placeholder': 'Enter your email'
    })
    login_form.fields['password'].widget.attrs.update({
        'placeholder': 'Enter your password'
    })

    context = {
        'login_form': login_form,
        'register_form': register_form,
        'active_form': active_form,
    }
    return render(request, 'donor.html', context)


@login_required
def donor_dashboard(request):
    """Donor dashboard view for authenticated users"""
    if not hasattr(request.user, 'donor_profile'):
        # If the user is authenticated but has no donor profile, they are not a donor.
        # Log them out and redirect to the donor login page.
        logout(request)
        messages.error(request, 'You do not have a donor profile. Please register or log in as a donor.')
        return redirect('donor')

    donor_profile = request.user.donor_profile
    donation_form = BloodDonationForm()
    booking_form = AppointmentBookingForm(donor=donor_profile)

    if request.method == 'POST':
        if 'donation' in request.POST:
            donation_form = BloodDonationForm(request.POST)
            if donation_form.is_valid():
                donation = donation_form.save(commit=False)
                donation.donor = donor_profile
                donation.status = 'pending'
                donation.save()
                messages.success(request, 'Donation request submitted! Awaiting admin approval.')
                return redirect('donor_dashboard')
        elif 'booking' in request.POST:
            booking_form = AppointmentBookingForm(request.POST, donor=donor_profile)
            if booking_form.is_valid():
                timeslot = booking_form.cleaned_data['timeslot']
                # Update the approved donation with timeslot
                approved_donation = BloodDonation.objects.filter(donor=donor_profile, status='approved').first()
                if approved_donation:
                    approved_donation.timeslot = timeslot
                    approved_donation.status = 'waiting'
                    approved_donation.appointment_date = timeslot.date
                    approved_donation.save()
                    # Increment booked count
                    timeslot.booked_count = F('booked_count') + 1
                    timeslot.save()
                    # Create notification
                    Notification.objects.create(
                        recipient=approved_donation.donor.user,
                        sender=None,
                        title='Appointment Booked',
                        message=f'Your appointment for {timeslot.date} at {timeslot.start_time} is waiting for admin confirmation.',
                        notification_type='appointment'
                    )
                    messages.success(request, f'Appointment booked for {timeslot.date} at {timeslot.start_time}. Awaiting final admin approval.')
                    return redirect('donor_dashboard')
                else:
                    messages.error(request, 'No approved donation found for booking.')

    donations = BloodDonation.objects.filter(donor=donor_profile).order_by('-donation_date')
    total_quantity = sum(donation.quantity for donation in donations if donation.quantity)

    # Get approved donations for booking
    approved_donations = BloodDonation.objects.filter(donor=donor_profile, status='approved')

    # Get upcoming appointments
    upcoming_appointments = BloodDonation.objects.filter(
        donor=donor_profile,
        status__in=['confirmed', 'completed'],
        appointment_date__gte=datetime.now().date()
    ).order_by('appointment_date')

    # Get notifications
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')

    # Get available timeslots for booking
    available_timeslots = Timeslot.objects.filter(
        is_active=True,
        date__gte=datetime.now().date()
    ).exclude(
        donations__donor=donor_profile,
        donations__status__in=['confirmed']
    ).order_by('date', 'start_time')[:5]  # Show next 5 available

    # Check donation restriction
    can_donate = True
    restriction_message = None
    if donor_profile.next_eligible_date and donor_profile.next_eligible_date > datetime.now().date():
        can_donate = False
        restriction_message = f'You can donate again after {donor_profile.next_eligible_date}.'

    context = {
        'donor_profile': donor_profile,
        'donation_form': donation_form,
        'booking_form': booking_form,
        'donations': donations,
        'total_quantity': total_quantity,
        'approved_donations': approved_donations,
        'upcoming_appointments': upcoming_appointments,
        'notifications': notifications,
        'available_timeslots': available_timeslots,
        'can_donate': can_donate,
        'restriction_message': restriction_message,
    }
    return render(request, 'donormain.html', context)


def donor_logout(request):
    """Logout view for donors"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('donor')


@login_required
def patient_dashboard(request):
    """Patient dashboard view for authenticated users"""
    try:
        patient_profile = request.user.patient_profile
    except PatientProfile.DoesNotExist:
        # If the user is authenticated but has no patient profile, they are not a patient.
        # Log them out and redirect to the patient login page.
        logout(request)
        messages.error(request, 'You do not have a patient profile. Please register or log in as a patient.')
        return redirect('patient')

    blood_request_form = BloodRequestForm()

    if request.method == 'POST':
        blood_request_form = BloodRequestForm(request.POST)
        if blood_request_form.is_valid():
            blood_request = blood_request_form.save(commit=False)
            blood_request.patient = patient_profile
            blood_request.save()
            messages.success(request, 'Blood request submitted successfully!')
            return redirect('patient_dashboard')

    blood_requests = BloodRequest.objects.filter(patient=patient_profile).order_by('-created_at')

    context = {
        'patient_profile': patient_profile,
        'blood_request_form': blood_request_form,
        'blood_requests': blood_requests,
    }
    return render(request, 'patient.html', context)


def patient_logout(request):
    """Logout view for patients"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('patient')


def patient_view(request):
    """Patient section view with login and register forms."""
    if request.user.is_authenticated and hasattr(request.user, 'patient_profile'):
        return redirect('patient_dashboard')

    active_form = 'login'
    login_form = AuthenticationForm()
    register_form = PatientRegistrationForm()

    if request.method == 'POST':
        if 'login' in request.POST:
            # Handle login
            data = request.POST.copy()
            entered_username = data.get('username', '')
            if '@' in entered_username:
                email_user = User.objects.filter(email__iexact=entered_username).first()
                if email_user:
                    data['username'] = email_user.username  # Use the actual username for authentication

            login_form = AuthenticationForm(data=data)
            if login_form.is_valid():
                user = login_form.get_user()
                if user is not None and user.is_active and hasattr(user, 'patient_profile'):
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('patient_dashboard')
                else:
                    messages.error(request, 'Invalid credentials or not a patient account.')
            else:
                messages.error(request, 'Invalid email or password. Please try again.')
            active_form = 'login'
        elif 'register' in request.POST:
            # Handle registration
            register_form = PatientRegistrationForm(request.POST)
            if register_form.is_valid():
                register_form.save()
                messages.success(request, 'Registration successful! Please log in to continue.')
                return redirect('patient')
            active_form = 'register'

    # Customize login form fields
    login_form.fields['username'].widget.attrs.update({
        'placeholder': 'Enter your email'
    })
    login_form.fields['password'].widget.attrs.update({
        'placeholder': 'Enter your password'
    })

    context = {
        'login_form': login_form,
        'register_form': register_form,
        'active_form': active_form,
    }
    return render(request, 'patientlogin.html', context)


# Admin Management Views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .forms import AdminCreationForm, AdminProfileUpdateForm


def is_superuser(user):
    """Check if user is a superuser or in Super Admin group"""
    return user.is_superuser or user.groups.filter(name='Super Admin').exists()


def is_admin(user):
    """Check if user is superuser or in Super Admin or Secondary Admin group"""
    return user.is_superuser or user.groups.filter(name__in=['Super Admin', 'Secondary Admin']).exists()


@user_passes_test(is_superuser)
def admin_management(request):
    """Main admin management dashboard for superusers"""
    admins = AdminProfile.objects.all().order_by('-created_at')
    context = {
        'admins': admins,
        'total_admins': admins.count(),
        'active_admins': admins.filter(is_active=True).count(),
        'super_admins': admins.filter(is_super_admin=True).count(),
        'secondary_admins': admins.filter(is_secondary_admin=True).count(),
    }
    return render(request, 'admin_management.html', context)


@user_passes_test(is_superuser)
def create_admin(request):
    """Create new secondary admin"""
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            admin_profile = form.save(commit=False)
            admin_profile.created_by = request.user
            admin_profile.save()
            messages.success(request, f'Admin {admin_profile.full_name} created successfully!')
            return redirect('admin_management')
    else:
        form = AdminCreationForm()

    context = {
        'form': form,
        'title': 'Create New Admin'
    }
    return render(request, 'admin_form.html', context)


@user_passes_test(is_superuser)
def update_admin(request, admin_id):
    """Update existing admin profile"""
    admin_profile = get_object_or_404(AdminProfile, id=admin_id)

    # Prevent superusers from editing other superusers (except themselves)
    if admin_profile.is_super_admin and admin_profile.user != request.user:
        messages.error(request, 'You cannot edit other superuser accounts.')
        return redirect('admin_management')

    if request.method == 'POST':
        form = AdminProfileUpdateForm(request.POST, instance=admin_profile)
        if form.is_valid():
            form.save()
            messages.success(request, f'Admin {admin_profile.full_name} updated successfully!')
            return redirect('admin_management')
    else:
        form = AdminProfileUpdateForm(instance=admin_profile)

    context = {
        'form': form,
        'admin_profile': admin_profile,
        'title': f'Update Admin: {admin_profile.full_name}'
    }
    return render(request, 'admin_form.html', context)


@csrf_exempt
@user_passes_test(is_superuser)
def toggle_admin_status(request, admin_id):
    """Toggle admin active status"""
    admin_profile = get_object_or_404(AdminProfile, id=admin_id)

    # Prevent superusers from deactivating other superusers
    if admin_profile.is_super_admin and admin_profile.user != request.user:
        messages.error(request, 'You cannot deactivate other superuser accounts.')
        return redirect('admin_management')

    admin_profile.is_active = not admin_profile.is_active
    admin_profile.save()

    # Also update the associated user account
    admin_profile.user.is_active = admin_profile.is_active
    admin_profile.user.save()

    status = "activated" if admin_profile.is_active else "deactivated"
    messages.success(request, f'Admin {admin_profile.full_name} has been {status}.')
    return redirect('admin_management')


@csrf_exempt
@user_passes_test(is_superuser)
def approve_admin(request, admin_id):
    """Approve pending admin and grant Secondary Admin permissions"""
    admin_profile = get_object_or_404(AdminProfile, id=admin_id)

    # Check if already approved
    if admin_profile.is_active and admin_profile.is_secondary_admin:
        messages.warning(request, f'Admin {admin_profile.full_name} is already approved.')
        return redirect('admin_management')

    # Add user to Secondary Admin group
    secondary_group = Group.objects.get(name='Secondary Admin')
    admin_profile.user.groups.add(secondary_group)

    # Activate the account
    admin_profile.is_active = True
    admin_profile.save()

    # Also update the user account
    admin_profile.user.is_active = True
    admin_profile.user.save()

    messages.success(request, f'Admin {admin_profile.full_name} has been approved and granted Secondary Admin permissions.')
    return redirect('admin_management')


@user_passes_test(is_superuser)
def delete_admin(request, admin_id):
    """Delete admin account"""
    admin_profile = get_object_or_404(AdminProfile, id=admin_id)

    # Prevent deletion of superuser accounts
    if admin_profile.is_super_admin:
        messages.error(request, 'Superuser accounts cannot be deleted.')
        return redirect('admin_management')

    # Prevent self-deletion
    if admin_profile.user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin_management')

    admin_name = admin_profile.full_name
    # Delete the user (this will cascade to the profile due to OneToOneField)
    admin_profile.user.delete()

    messages.success(request, f'Admin {admin_name} has been deleted successfully.')
    return redirect('admin_management')


# Admin Login and Dashboard Views
@csrf_exempt
def admin_login(request):
    """Admin login and registration view"""
    if request.user.is_authenticated and is_admin(request.user) and request.user.is_active:
        return redirect('admin_dashboard')

    login_form = AdminLoginForm()
    register_form = AdminRegistrationForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'login':
            login_form = AdminLoginForm(data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                if user is not None:
                    if is_admin(user):
                        if user.is_active:
                            login(request, user)
                            messages.success(request, f'Welcome back, {user.username}!')
                            return redirect('admin_dashboard')
                        else:
                            messages.error(request, 'Your account is pending approval by the main admin.')
                    else:
                        messages.error(request, 'You do not have admin privileges.')
                else:
                    messages.error(request, 'Invalid username or password.')
            else:
                messages.error(request, 'Invalid username or password.')

        elif form_type == 'register':
            register_form = AdminRegistrationForm(request.POST)
            if register_form.is_valid():
                register_form.save()
                messages.success(request, 'Registration successful! Awaiting superuser approval.')
                return redirect('admin_portal')
            # else: Keep register form with errors

    context = {
        'login_form': login_form,
        'register_form': register_form,
    }
    return render(request, 'admin.html', context)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard view for authenticated admin users"""
    try:
        admin_profile = request.user.admin_profile
    except AdminProfile.DoesNotExist:
        # If no profile exists, redirect to profile setup or create basic one
        messages.warning(request, 'Your admin profile is incomplete. Please contact a super admin.')
        return redirect('admin_portal')

    # Redirect secondary admins to their own dashboard
    if admin_profile.is_secondary_admin and not admin_profile.is_super_admin:
        return redirect('secondary_admin_dashboard')

    # Get pending admin approvals for super admins
    pending_admins = []
    if admin_profile.is_super_admin:
        pending_admins = AdminProfile.objects.filter(is_active=False, is_secondary_admin=False).order_by('-created_at')

    donors = DonorProfile.objects.all()
    patients = PatientProfile.objects.all()
    blood_requests = BloodRequest.objects.filter(status='pending').order_by('-created_at')
    donations = BloodDonation.objects.filter(status__in=['pending', 'waiting']).order_by('-created_at')
    timeslots = Timeslot.objects.all().order_by('-date', 'start_time')
    blood_units = BloodBank.objects.all().order_by('-created_at')

    # Blood bank analytics for enhanced blood bank section
    today = datetime.now().date()
    warning_date = today + timedelta(days=7)

    # Blood inventory summary
    blood_inventory = {}
    for unit in blood_units:
        blood_group = unit.blood_group
        if blood_group not in blood_inventory:
            blood_inventory[blood_group] = 0
        blood_inventory[blood_group] += 1

    # Units expiring soon (within 7 days)
    expiring_units = blood_units.filter(expiry_date__lte=warning_date, expiry_date__gte=today)

    # Expired units
    expired_units = blood_units.filter(expiry_date__lt=today)

    # Low stock types (less than 5 units)
    low_stock_types = {blood_group: count for blood_group, count in blood_inventory.items() if count < 5}

    context = {
        'admin_profile': admin_profile,
        'is_super_admin': admin_profile.is_super_admin,
        'is_secondary_admin': admin_profile.is_secondary_admin,
        'is_super_admin_group': request.user.groups.filter(name='Super Admin').exists(),
        'is_secondary_admin_group': request.user.groups.filter(name='Secondary Admin').exists(),
        'pending_admins': pending_admins,
        'donors': donors,
        'patients': patients,
        'blood_requests': blood_requests,
        'donations': donations,
        'timeslots': timeslots,
        'blood_units': blood_units,
        # Enhanced blood bank context
        'blood_inventory': blood_inventory,
        'expiring_units': expiring_units,
        'expired_units': expired_units,
        'low_stock_types': low_stock_types,
        'today': today,
        'warning_date': warning_date,
    }
    return render(request, 'adminmain.html', context)


@login_required
@user_passes_test(is_admin)
def secondary_admin_dashboard(request):
    """Secondary admin dashboard view with limited access"""
    try:
        admin_profile = request.user.admin_profile
    except AdminProfile.DoesNotExist:
        messages.warning(request, 'Your admin profile is incomplete. Please contact a super admin.')
        return redirect('admin_portal')

    # Ensure only secondary admins can access this view
    if not admin_profile.is_secondary_admin or admin_profile.is_super_admin:
        messages.error(request, 'Access denied. This page is for secondary admins only.')
        return redirect('admin_dashboard')

    donors = DonorProfile.objects.all()
    patients = PatientProfile.objects.all()
    blood_requests = BloodRequest.objects.filter(status='pending').order_by('-created_at')
    donations = BloodDonation.objects.filter(status='pending').order_by('-created_at')

    context = {
        'admin_profile': admin_profile,
        'is_super_admin': False,  # Always false for secondary admins
        'is_secondary_admin': True,
        'is_super_admin_group': False,  # Always false for secondary admins
        'is_secondary_admin_group': True,
        'donors': donors,
        'patients': patients,
        'blood_requests': blood_requests,
        'donations': donations,
    }
    return render(request, 'admin2.html', context)


@login_required
def admin_logout(request):
    """Logout view for admins"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('admin_portal')


@login_required
@user_passes_test(is_admin)
def approve_blood_request(request, request_id):
    """Approve a blood request and deduct from blood bank inventory."""
    blood_request = get_object_or_404(BloodRequest, id=request_id)

    # Check if already approved
    if blood_request.status == 'approved':
        messages.warning(request, 'This blood request is already approved.')
        return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

    # Check if sufficient blood units are available in inventory
    available_units = BloodBank.objects.filter(
        blood_group=blood_request.blood_group,
        status='available',
        expiry_date__gt=datetime.now().date()
    ).aggregate(total_units=models.Sum('quantity'))['total_units'] or 0

    if available_units < blood_request.quantity:
        messages.error(request, f'Insufficient blood units available. Requested: {blood_request.quantity}, Available: {available_units}')
        return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

    # Deduct blood units from inventory (FIFO - First In, First Out)
    units_needed = blood_request.quantity
    blood_units = BloodBank.objects.filter(
        blood_group=blood_request.blood_group,
        status='available',
        expiry_date__gt=datetime.now().date()
    ).order_by('expiry_date')  # Use oldest blood first

    fulfilled_quantity = 0
    for unit in blood_units:
        if units_needed <= 0:
            break

        if unit.quantity <= units_needed:
            # Use entire unit
            unit.status = 'used'
            unit.save()
            fulfilled_quantity += unit.quantity
            units_needed -= unit.quantity
        else:
            # Split unit - create new unit with remaining quantity
            remaining_quantity = unit.quantity - units_needed
            unit.quantity = units_needed
            unit.status = 'used'
            unit.save()

            # Create new unit with remaining quantity
            BloodBank.objects.create(
                donation=unit.donation,
                blood_group=unit.blood_group,
                quantity=remaining_quantity,
                expiry_date=unit.expiry_date,
                status='available',
                location=unit.location
            )
            fulfilled_quantity += units_needed
            units_needed = 0

    # Update blood request
    blood_request.status = 'fulfilled'
    blood_request.fulfilled_quantity = fulfilled_quantity
    blood_request.save()

    # Create notification for patient
    Notification.objects.create(
        recipient=blood_request.patient.user,
        title='Blood Request Fulfilled',
        message=f'Your blood request for {fulfilled_quantity} units of {blood_request.blood_group} blood has been fulfilled.',
        notification_type='status_update',
        related_request=blood_request
    )

    messages.success(request, f'Blood request fulfilled. {fulfilled_quantity} units deducted from inventory.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
@user_passes_test(is_admin)
def reject_blood_request(request, request_id):
    """Reject a blood request."""
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    blood_request.status = 'rejected'
    blood_request.save()
    # Create notification for patient
    Notification.objects.create(
        recipient=blood_request.patient.user,
        sender=None,
        title='Blood Request Rejected',
        message=f'Your blood request has been rejected.',
        notification_type='status_update'
    )
    messages.success(request, 'Blood request rejected. Patient notified.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
@user_passes_test(is_admin)
def approve_donation(request, donation_id):
    """Approve a blood donation."""
    donation = get_object_or_404(BloodDonation, id=donation_id, status='pending')
    donation.status = 'approved'
    donation.save()

    # Create notification for donor
    Notification.objects.create(
        recipient=donation.donor.user,
        title='Donation Approved',
        message='Great! You can now fix the donation appointment.',
        notification_type='appointment',
        related_donation=donation
    )

    messages.success(request, 'Donation approved. Donor notified to book appointment.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
@user_passes_test(is_admin)
def reject_donation(request, donation_id):
    """Reject a blood donation."""
    donation = get_object_or_404(BloodDonation, id=donation_id)
    donation.status = 'rejected'
    donation.save()
    # Create notification for donor
    Notification.objects.create(
        recipient=donation.donor.user,
        sender=None,
        title='Donation Rejected',
        message=f'Your donation request has been rejected.',
        notification_type='status_update'
    )
    messages.success(request, 'Donation rejected. Donor notified.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


# Timeslot Management Views
@login_required
@user_passes_test(is_admin)
def timeslot_list(request):
    """List all timeslots for admin management"""
    timeslots = Timeslot.objects.annotate(
        percentage=Case(
            When(capacity__gt=0, then=(F('booked_count') / F('capacity')) * 100),
            default=Value(0),
            output_field=FloatField()
        )
    ).order_by('-date', 'start_time')
    context = {
        'timeslots': timeslots,
    }
    return render(request, 'timeslot_list.html', context)


@login_required
@user_passes_test(is_admin)
def create_timeslot(request):
    """Create a new timeslot"""
    if request.method == 'POST':
        form = TimeslotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Timeslot created successfully!')
            return redirect('timeslot_list')
    else:
        form = TimeslotForm()
    context = {
        'form': form,
        'title': 'Create Timeslot'
    }
    return render(request, 'timeslot_form.html', context)


@login_required
@user_passes_test(is_admin)
def update_timeslot(request, timeslot_id):
    """Update an existing timeslot"""
    timeslot = get_object_or_404(Timeslot, id=timeslot_id)
    if request.method == 'POST':
        form = TimeslotForm(request.POST, instance=timeslot)
        if form.is_valid():
            form.save()
            messages.success(request, 'Timeslot updated successfully!')
            return redirect('timeslot_list')
    else:
        form = TimeslotForm(instance=timeslot)
    context = {
        'form': form,
        'timeslot': timeslot,
        'title': 'Update Timeslot'
    }
    return render(request, 'timeslot_form.html', context)


@login_required
@user_passes_test(is_admin)
def delete_timeslot(request, timeslot_id):
    """Delete a timeslot"""
    timeslot = get_object_or_404(Timeslot, id=timeslot_id)
    if request.method == 'POST':
        timeslot.delete()
        messages.success(request, 'Timeslot deleted successfully!')
        return redirect('timeslot_list')
    context = {
        'timeslot': timeslot,
    }
    return render(request, 'delete_timeslot.html', context)


@login_required
@user_passes_test(is_admin)
def confirm_appointment(request, donation_id):
    """Confirm a waiting appointment"""
    donation = get_object_or_404(BloodDonation, id=donation_id, status='waiting')
    donation.status = 'confirmed'
    donation.save()

    # Set next eligible date
    donation.donor.next_eligible_date = datetime.now().date() + timedelta(days=90)
    donation.donor.save()

    # Add to blood bank only if not already exists
    if not hasattr(donation, 'blood_unit'):
        BloodBank.objects.create(
            donation=donation,
            blood_group=donation.donor.blood_group,
            quantity=donation.quantity or 450,
            expiry_date=datetime.now().date() + timedelta(days=42)
        )

    # Create notification for donor
    Notification.objects.create(
        recipient=donation.donor.user,
        title='Donation Confirmed',
        message='Congratulations on your valuable donation.',
        notification_type='donation_completed',
        related_donation=donation
    )

    messages.success(request, 'Appointment confirmed and donation completed.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
@user_passes_test(is_admin)
def complete_donation(request, donation_id):
    """Mark donation as completed"""
    donation = get_object_or_404(BloodDonation, id=donation_id, status='confirmed')
    donation.status = 'completed'
    donation.save()

    # Decrement booked count
    donation.timeslot.booked_count = F('booked_count') - 1
    donation.timeslot.save()

    # Create notification for donor
    Notification.objects.create(
        recipient=donation.donor.user,
        sender=None,
        title='Donation Completed',
        message=f'Your donation on {donation.donation_date} has been completed. Thank you for saving lives!',
        notification_type='donation_completed'
    )

    messages.success(request, 'Donation marked as completed.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
@user_passes_test(is_admin)
def blood_bank_list(request):
    """List blood bank inventory"""
    blood_units = BloodBank.objects.all().order_by('-created_at')
    context = {
        'blood_units': blood_units,
    }
    return render(request, 'blood_bank.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect(request.META.get('HTTP_REFERER', 'donor_dashboard'))


def test_admin_login(request):
    """Test view to debug admin login"""
    from django.contrib.auth import authenticate
    from django.contrib.auth.models import User, Group

    result = {}

    # Check if secondary admin exists
    try:
        user = User.objects.get(username='secondary_admin')
        result['user_exists'] = True
        result['user_active'] = user.is_active
        result['user_groups'] = list(user.groups.values_list('name', flat=True))

        # Test authentication
        auth_user = authenticate(username='secondary_admin', password='secondary123')
        result['auth_success'] = auth_user is not None

        if auth_user:
            result['is_admin_check'] = is_admin(auth_user)

        # Check profile
        try:
            profile = user.admin_profile
            result['profile_exists'] = True
            result['is_super_admin'] = profile.is_super_admin
            result['is_secondary_admin'] = profile.is_secondary_admin
        except AdminProfile.DoesNotExist:
            result['profile_exists'] = False

    except User.DoesNotExist:
        result['user_exists'] = False

    # Check groups
    result['available_groups'] = list(Group.objects.values_list('name', flat=True))

    return render(request, 'test_admin.html', {'result': result})
