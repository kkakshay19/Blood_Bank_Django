from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .forms import DonorRegistrationForm, AdminLoginForm, AdminRegistrationForm, PatientRegistrationForm, BloodRequestForm, BloodDonationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import DonorProfile, AdminProfile, PatientProfile, BloodRequest, BloodDonation

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

    if request.method == 'POST':
        donation_form = BloodDonationForm(request.POST)
        if donation_form.is_valid():
            donation = donation_form.save(commit=False)
            donation.donor = donor_profile
            donation.save()
            messages.success(request, 'Donation logged successfully!')
            return redirect('donor_dashboard')

    donations = BloodDonation.objects.filter(donor=donor_profile).order_by('-donation_date')
    total_quantity = sum(donation.quantity for donation in donations)

    context = {
        'donor_profile': donor_profile,
        'donation_form': donation_form,
        'donations': donations,
        'total_quantity': total_quantity,
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
    donations = BloodDonation.objects.filter(status='pending').order_by('-created_at')

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
    """Approve a blood request."""
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    blood_request.status = 'approved'
    blood_request.save()
    messages.success(request, 'Blood request approved.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
@user_passes_test(is_admin)
def reject_blood_request(request, request_id):
    """Reject a blood request."""
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    blood_request.status = 'rejected'
    blood_request.save()
    messages.success(request, 'Blood request rejected.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
@user_passes_test(is_admin)
def approve_donation(request, donation_id):
    """Approve a blood donation."""
    donation = get_object_or_404(BloodDonation, id=donation_id)
    donation.status = 'approved'
    donation.save()
    messages.success(request, 'Donation approved.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
@user_passes_test(is_admin)
def reject_donation(request, donation_id):
    """Reject a blood donation."""
    donation = get_object_or_404(BloodDonation, id=donation_id)
    donation.status = 'rejected'
    donation.save()
    messages.success(request, 'Donation rejected.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

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
