# Generated migration to remove erroneous sender_id field from Notification table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_remove_timeslot_booked_timeslot_booked_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='sender',
        ),
        migrations.AddField(
            model_name='bloodrequest',
            name='fulfilled_quantity',
            field=models.PositiveIntegerField(default=0, help_text='Number of units actually fulfilled'),
        ),
    ]
