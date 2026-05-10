from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Apply database migrations and ensure the initial user (convenience for local setup)."

    def handle(self, *args, **options):
        call_command("migrate", interactive=False, no_input=True)
        call_command("ensure_initial_user")
        call_command("seed_demo_data")
