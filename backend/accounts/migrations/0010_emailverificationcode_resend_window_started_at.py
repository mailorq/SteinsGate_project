import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_emailverificationcode_code_nonce"),
    ]

    operations = [
        migrations.AddField(
            model_name="emailverificationcode",
            name="resend_window_started_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
