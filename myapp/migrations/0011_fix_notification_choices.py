# Generated migration to fix notification choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_remove_notification_sender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('appointment', 'Appointment'),
                    ('confirmation', 'Confirmation'),
                    ('reminder', 'Reminder'),
                    ('status_update', 'Status Update'),
                    ('donation_completed', 'Donation Completed'),
                    ('general', 'General'),
                ],
                default='general',
                help_text='Notification type',
                max_length=20,
            ),
        ),
    ]
