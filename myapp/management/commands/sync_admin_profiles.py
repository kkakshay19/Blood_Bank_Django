from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import AdminProfile


class Command(BaseCommand):
    help = 'Sync admin profile flags with current user group membership and superuser status'

    def handle(self, *args, **options):
        self.stdout.write('Syncing admin profile flags with group membership...')

        admin_profiles = AdminProfile.objects.all()
        updated_count = 0

        for profile in admin_profiles:
            user = profile.user

            # Determine correct flags based on current user status
            should_be_super_admin = user.is_superuser or user.groups.filter(name='Super Admin').exists()
            should_be_secondary_admin = user.groups.filter(name='Secondary Admin').exists()

            # Check if flags need updating
            needs_update = False
            if profile.is_super_admin != should_be_super_admin:
                needs_update = True
            if profile.is_secondary_admin != should_be_secondary_admin:
                needs_update = True

            if needs_update:
                profile.is_super_admin = should_be_super_admin
                profile.is_secondary_admin = should_be_secondary_admin
                profile.save(update_fields=['is_super_admin', 'is_secondary_admin'])
                updated_count += 1
                self.stdout.write(
                    f'Updated {user.username}: super_admin={should_be_super_admin}, secondary_admin={should_be_secondary_admin}'
                )

        if updated_count == 0:
            self.stdout.write('All admin profiles are already in sync.')
        else:
            self.stdout.write(f'Successfully updated {updated_count} admin profile(s).')

        self.stdout.write(self.style.SUCCESS('Admin profile sync completed!'))