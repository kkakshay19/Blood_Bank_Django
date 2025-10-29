# Generated migration to remove sender field from Notification table if it exists

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0011_fix_notification_choices'),
    ]

    operations = [
        # First drop the foreign key constraint, then drop the column
        migrations.RunSQL(
            "ALTER TABLE myapp_notification DROP FOREIGN KEY myapp_notification_sender_id_083ce63f_fk_myapp_adminprofile_id;",
            reverse_sql="ALTER TABLE myapp_notification ADD CONSTRAINT myapp_notification_sender_id_083ce63f_fk_myapp_adminprofile_id FOREIGN KEY (sender_id) REFERENCES myapp_adminprofile (id);",
        ),
        migrations.RunSQL(
            "ALTER TABLE myapp_notification DROP COLUMN sender_id;",
            reverse_sql="ALTER TABLE myapp_notification ADD COLUMN sender_id integer NULL;",
        ),
    ]
