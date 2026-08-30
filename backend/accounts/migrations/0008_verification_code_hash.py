import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_user_email_unique_index"),
    ]

    operations = [
        migrations.RemoveField(model_name="emailverificationcode", name="code"),
        migrations.AddField(
            model_name="emailverificationcode",
            name="code_hash",
            field=models.CharField(default="", max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="emailverificationcode",
            name="resend_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="emailverificationcode",
            name="last_sent_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
