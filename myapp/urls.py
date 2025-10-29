from django.urls import path
from . import views

urlpatterns = [
    # Homepage
    path('', views.index, name='index'),

    # Admin portal
    path('admin-portal/', views.admin_login, name='admin_portal'),
    path('portal/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('portal/secondary-dashboard/', views.secondary_admin_dashboard, name='secondary_admin_dashboard'),
    path('portal/logout/', views.admin_logout, name='admin_logout'),
    path('test-admin/', views.test_admin_login, name='test_admin'),

    # Admin Management (Superuser only)
    path('portal/management/', views.admin_management, name='admin_management'),
    path('portal/create/', views.create_admin, name='create_admin'),
    path('portal/<int:admin_id>/update/', views.update_admin, name='update_admin'),
    path('portal/<int:admin_id>/toggle/', views.toggle_admin_status, name='toggle_admin_status'),
    path('portal/<int:admin_id>/approve/', views.approve_admin, name='approve_admin'),
    path('portal/<int:admin_id>/delete/', views.delete_admin, name='delete_admin'),

    # Donor section
    path('donor/', views.donor_view, name='donor'),
    path('donor/dashboard/', views.donor_dashboard, name='donor_dashboard'),
    path('donor/logout/', views.donor_logout, name='donor_logout'),

    # Patient section
    path('patient/', views.patient_view, name='patient'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/logout/', views.patient_logout, name='patient_logout'),

    # Patient Management
    path('admin/toggle-patient-status/<int:patient_id>/', views.toggle_patient_status, name='toggle_patient_status'),
    path('admin/patient/<int:patient_id>/details/', views.patient_details, name='patient_details'),
    path('admin/patient/<int:patient_id>/edit/', views.edit_patient, name='edit_patient'),

    # Admin actions
    path('request/<int:request_id>/approve/', views.approve_blood_request, name='approve_blood_request'),
    path('request/<int:request_id>/reject/', views.reject_blood_request, name='reject_blood_request'),
    path('donation/<int:donation_id>/approve-initial/', views.approve_donation_initial, name='approve_donation_initial'),
    path('donation/<int:donation_id>/approve-final/', views.approve_donation_final, name='approve_donation_final'),
    path('donation/<int:donation_id>/reject/', views.reject_donation, name='reject_donation'),

    # Timeslot Management
    path('portal/timeslots/', views.timeslot_list, name='timeslot_list'),
    path('portal/timeslots/create/', views.create_timeslot, name='create_timeslot'),
    path('portal/timeslots/<int:timeslot_id>/update/', views.update_timeslot, name='update_timeslot'),
    path('portal/timeslots/<int:timeslot_id>/delete/', views.delete_timeslot, name='delete_timeslot'),


    # Blood Bank
    path('portal/blood-bank/', views.blood_bank_list, name='blood_bank_list'),

    # Notifications
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]