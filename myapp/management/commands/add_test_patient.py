from django.core.management.base import BaseCommand
from myapp.models import PatientProfile, BloodRequest
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Add test patient and blood request'

    def handle(self, *args, **options):
        # Create a test user if it doesn't exist
        user, created = User.objects.get_or_create(
            username='test_patient',
            defaults={
                'email': 'patient@example.com',
                'first_name': 'Test',
                'last_name': 'Patient'
            }
        )
        
        # Create a test patient if it doesn't exist
        test_patient, created = PatientProfile.objects.get_or_create(
            user=user,
            defaults={
                'full_name': 'Test Patient',
                'blood_group': 'O+',
                'contact_number': '9876543210',
                'age': 30
            }
        )
        
        # Create a test blood request
        blood_request, created = BloodRequest.objects.get_or_create(
            patient=test_patient,
            blood_group='O+',
            quantity=1,
            defaults={
                'status': 'pending'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created blood request for {test_patient.full_name} - {blood_request.quantity} units of {blood_request.blood_group}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Blood request already exists')
            )
