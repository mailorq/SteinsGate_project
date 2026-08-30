from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_verification_code_hash"),
    ]

    operations = [
        migrations.AddField(
            model_name="emailverificationcode",
            name="code_nonce",
            field=models.CharField(default="", max_length=64),
        ),
    ]
