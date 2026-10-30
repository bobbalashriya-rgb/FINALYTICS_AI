from django.core.management.base import BaseCommand
from api.models import InvestmentPrinciple
from api.apps import DEFAULT_PRINCIPLES

class Command(BaseCommand):
    help = "Seeds or resets default investment principles in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing principles and re-seed from default',
        )

    def handle(self, *args, **options):
        if options['reset']:
            deleted, _ = InvestmentPrinciple.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing principles."))

        count = 0
        for p in DEFAULT_PRINCIPLES:
            obj, created = InvestmentPrinciple.objects.update_or_create(
                identifier=p['identifier'],
                defaults=p
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully ensured {len(DEFAULT_PRINCIPLES)} default principles (created {count} new)."))

