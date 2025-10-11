from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from myapp.models import DonorProfile, AdminProfile


class Command(BaseCommand):
    help = 'Set up admin groups and permissions for the blood bank system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up admin groups and permissions...')

        # Create Super Admin group
        super_admin_group, created = Group.objects.get_or_create(name='Super Admin')
        if created:
            self.stdout.write('Created Super Admin group')
        else:
            self.stdout.write('Super Admin group already exists')

        # Create Secondary Admin group
        secondary_admin_group, created = Group.objects.get_or_create(name='Secondary Admin')
        if created:
            self.stdout.write('Created Secondary Admin group')
        else:
            self.stdout.write('Secondary Admin group already exists')

        # Get content types for our models
        donor_profile_ct = ContentType.objects.get_for_model(DonorProfile)
        admin_profile_ct = ContentType.objects.get_for_model(AdminProfile)
        user_ct = ContentType.objects.get_for_model(Group)  # Using Group as proxy for User permissions

        # Get existing permissions (Django creates them automatically when models are registered)
        super_admin_permissions = []
        secondary_admin_permissions = []

        # Get donor permissions
        donor_permissions = Permission.objects.filter(content_type=donor_profile_ct)
        admin_permissions = Permission.objects.filter(content_type=admin_profile_ct)

        # Super Admin gets all permissions
        super_admin_permissions.extend(donor_permissions)
        super_admin_permissions.extend(admin_permissions)

        # Secondary Admin gets limited permissions
        secondary_admin_permissions.extend(
            donor_permissions.filter(
                codename__in=['view_donorprofile', 'change_donorprofile']
            )
        )
        secondary_admin_permissions.extend(
            admin_permissions.filter(codename='view_adminprofile')
        )

        self.stdout.write(f'Found {len(super_admin_permissions)} permissions for Super Admin')
        self.stdout.write(f'Found {len(secondary_admin_permissions)} permissions for Secondary Admin')

        # Assign permissions to Super Admin group
        super_admin_group.permissions.set(super_admin_permissions)
        self.stdout.write(f'Assigned {len(super_admin_permissions)} permissions to Super Admin group')

        # Assign permissions to Secondary Admin group
        secondary_admin_group.permissions.set(secondary_admin_permissions)
        self.stdout.write(f'Assigned {len(secondary_admin_permissions)} permissions to Secondary Admin group')

        self.stdout.write(self.style.SUCCESS('Successfully set up admin groups and permissions!'))

        # Display summary
        self.stdout.write('\n--- Admin Hierarchy Summary ---')
        self.stdout.write('Super Admin Group:')
        for perm in super_admin_group.permissions.all():
            self.stdout.write(f'  - {perm.codename}: {perm.name}')

        self.stdout.write('\nSecondary Admin Group:')
        for perm in secondary_admin_group.permissions.all():
            self.stdout.write(f'  - {perm.codename}: {perm.name}')

        self.stdout.write('\nTo create a superuser, run: python manage.py createsuperuser')
        self.stdout.write('Then assign the superuser to the "Super Admin" group in the Django admin.')