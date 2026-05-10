import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = (
        "Create the initial user from environment variables if missing (idempotent). "
        "Ensures an API token exists for that user."
    )

    def handle(self, *args, **options):
        if os.environ.get("INITIAL_USER_SKIP", "").lower() in ("1", "true", "yes"):
            self.stdout.write(self.style.WARNING("INITIAL_USER_SKIP is set; skipping user creation."))
            return

        username = os.environ.get("INITIAL_USER_USERNAME", "worker")
        password = os.environ.get("INITIAL_USER_PASSWORD", "devpass123")
        email = os.environ.get("INITIAL_USER_EMAIL", "")

        if not password:
            self.stdout.write(
                self.style.WARNING("INITIAL_USER_PASSWORD is empty; skipping user creation.")
            )
            return

        is_staff = os.environ.get("INITIAL_USER_STAFF", "true").lower() in ("1", "true", "yes")
        is_superuser = os.environ.get("INITIAL_USER_SUPERUSER", "true").lower() in (
            "1",
            "true",
            "yes",
        )

        User = get_user_model()
        user = User.objects.filter(username=username).first()
        created_user = False
        if user:
            self.stdout.write(f'User "{username}" already exists; skipping creation.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=is_staff,
                is_superuser=is_superuser,
            )
            created_user = True
            self.stdout.write(self.style.SUCCESS(f'Created user "{username}".'))

        token, _ = Token.objects.get_or_create(user=user)
        if created_user:
            self.stdout.write(
                self.style.SUCCESS(
                    f'API token (dev): Authorization: Token {token.key}'
                )
            )
        else:
            self.stdout.write(
                'API token: use POST /api/auth/token/ with username and password.'
            )
