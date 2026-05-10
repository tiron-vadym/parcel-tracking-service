import decimal
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PostOffice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveIntegerField(unique=True)),
                ("city", models.CharField(max_length=100)),
                ("address", models.CharField(max_length=255)),
                ("postal_code", models.CharField(max_length=20)),
            ],
            options={"ordering": ["city", "number"]},
        ),
        migrations.CreateModel(
            name="Parcel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tracking_number", models.CharField(db_index=True, editable=False, max_length=20, unique=True)),
                ("sender_full_name", models.CharField(max_length=255)),
                ("sender_phone", models.CharField(max_length=30)),
                ("recipient_full_name", models.CharField(max_length=255)),
                ("recipient_phone", models.CharField(max_length=30)),
                (
                    "weight_kg",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            django.core.validators.MinValueValidator(decimal.Decimal("0.01")),
                            django.core.validators.MaxValueValidator(decimal.Decimal("30")),
                        ],
                    ),
                ),
                (
                    "declared_value",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0"))],
                    ),
                ),
                (
                    "current_status",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("accepted", "Accepted"),
                            ("in_transit", "In transit"),
                            ("arrived", "Arrived"),
                            ("delivered", "Delivered"),
                            ("returned", "Returned"),
                        ],
                        default="created",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "destination_office",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="destination_parcels",
                        to="tracking.postoffice",
                    ),
                ),
                (
                    "origin_office",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="origin_parcels",
                        to="tracking.postoffice",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ParcelStatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "new_status",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("accepted", "Accepted"),
                            ("in_transit", "In transit"),
                            ("arrived", "Arrived"),
                            ("delivered", "Delivered"),
                            ("returned", "Returned"),
                        ],
                        max_length=20,
                    ),
                ),
                ("comment", models.CharField(blank=True, max_length=255)),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "office",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="status_updates",
                        to="tracking.postoffice",
                    ),
                ),
                (
                    "parcel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="tracking.parcel",
                    ),
                ),
            ],
            options={"ordering": ["changed_at", "id"]},
        ),
    ]
