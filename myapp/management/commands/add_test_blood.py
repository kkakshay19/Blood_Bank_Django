from django.core.management.base import BaseCommand
from myapp.models import BloodBank, BloodDonation, DonorProfile
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Add test blood units to the blood bank'

    def handle(self, *args, **options):
        from django.contrib.auth.models import User
        
        # Create a test user if it doesn't exist
        user, created = User.objects.get_or_create(
            username='test_donor',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'Donor'
            }
        )
        
        # Create a test donor if it doesn't exist
        test_donor, created = DonorProfile.objects.get_or_create(
            user=user,
            defaults={
                'full_name': 'Test Donor',
                'blood_group': 'O+',
                'contact_number': '1234567890',
                'age': 25
            }
        )

        # Create test blood donations
        test_donations = [
            {'blood_group': 'O+', 'quantity': 2},
            {'blood_group': 'A+', 'quantity': 3},
            {'blood_group': 'B+', 'quantity': 1},
            {'blood_group': 'AB+', 'quantity': 2},
            {'blood_group': 'O-', 'quantity': 1},
        ]

        for donation_data in test_donations:
            # Create blood donation
            donation = BloodDonation.objects.create(
                donor=test_donor,
                quantity=donation_data['quantity'],
                donation_date=date.today(),
                status='final_approved'
            )
            
            # Create blood bank unit
            BloodBank.objects.create(
                donation=donation,
                blood_group=donation_data['blood_group'],
                quantity=donation_data['quantity'],
                expiry_date=date.today() + timedelta(days=42),
                status='available'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Added {donation_data["quantity"]} units of {donation_data["blood_group"]} blood')
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully added test blood units to the blood bank!')
        )
