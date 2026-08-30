from django.core.management.base import BaseCommand, CommandError

from accounts import services


class Command(BaseCommand):
    help = "Удаляет истёкшие неподтверждённые регистрации и неактуальные лимиты отправки"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1_000,
            help="Максимум pending-регистраций за один запуск (по умолчанию 1000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать, сколько записей было бы удалено",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        if batch_size < 1:
            raise CommandError("--batch-size должен быть положительным числом")

        result = services.purge_expired_registrations(
            batch_size=batch_size,
            dry_run=options["dry_run"],
        )
        action = "Будет удалено" if options["dry_run"] else "Удалено"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} pending-регистраций: {result.registrations}; "
                f"неактуальных лимитов отправки: {result.delivery_quotas}"
            )
        )
