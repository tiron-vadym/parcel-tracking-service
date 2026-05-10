import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ParcelStatus(models.TextChoices):
    CREATED = "created", "Created"
    ACCEPTED = "accepted", "Accepted"
    IN_TRANSIT = "in_transit", "In transit"
    ARRIVED = "arrived", "Arrived"
    DELIVERED = "delivered", "Delivered"
    RETURNED = "returned", "Returned"


class PostOffice(models.Model):
    number = models.PositiveIntegerField(unique=True)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)

    class Meta:
        ordering = ["city", "number"]

    def __str__(self) -> str:
        return f"{self.city} #{self.number}"


class Parcel(models.Model):
    tracking_number = models.CharField(max_length=20, unique=True, db_index=True, editable=False)
    sender_full_name = models.CharField(max_length=255)
    sender_phone = models.CharField(max_length=30)
    recipient_full_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=30)
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("30"))],
    )
    declared_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    origin_office = models.ForeignKey(PostOffice, on_delete=models.PROTECT, related_name="origin_parcels")
    destination_office = models.ForeignKey(
        PostOffice, on_delete=models.PROTECT, related_name="destination_parcels"
    )
    current_status = models.CharField(
        max_length=20,
        choices=ParcelStatus.choices,
        default=ParcelStatus.CREATED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.tracking_number

    def clean(self) -> None:
        super().clean()
        if self.origin_office_id and self.destination_office_id and self.origin_office_id == self.destination_office_id:
            raise ValidationError(
                {"destination_office": "Origin and destination offices must be different."}
            )

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self._generate_tracking_number()
        self.full_clean()
        return super().save(*args, **kwargs)

    @classmethod
    def _generate_tracking_number(cls) -> str:
        while True:
            candidate = f"TRK{uuid.uuid4().hex[:10].upper()}"
            if not cls.objects.filter(tracking_number=candidate).exists():
                return candidate


class ParcelStatusHistory(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name="status_history")
    new_status = models.CharField(max_length=20, choices=ParcelStatus.choices)
    office = models.ForeignKey(PostOffice, on_delete=models.PROTECT, related_name="status_updates")
    comment = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["changed_at", "id"]

    def __str__(self) -> str:
        return f"{self.parcel.tracking_number}: {self.new_status}"
