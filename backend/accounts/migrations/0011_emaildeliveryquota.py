import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_emailverificationcode_resend_window_started_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailDeliveryQuota",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email_fingerprint", models.CharField(max_length=64, unique=True)),
                ("delivery_count", models.PositiveSmallIntegerField(default=0)),
                ("window_started_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "indexes": [models.Index(fields=["window_started_at"], name="accounts_edq_window_idx")],
            },
        ),
    ]
