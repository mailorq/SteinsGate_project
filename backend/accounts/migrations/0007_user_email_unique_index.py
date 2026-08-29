from django.db import migrations

# у встроенной модели User поле email не уникально, поэтому параллельные
# регистрации могут завести два аккаунта на один адрес. частичный
# регистронезависимый индекс закрывает это на уровне бд
CREATE_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS accounts_user_email_ci_uniq
ON auth_user (LOWER(email))
WHERE email <> '';
"""

DROP_INDEX = "DROP INDEX IF EXISTS accounts_user_email_ci_uniq;"


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_delete_passwordresetcode"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_INDEX, reverse_sql=DROP_INDEX),
    ]
