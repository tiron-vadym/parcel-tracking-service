from django.core.management.base import BaseCommand
from django.db import transaction

from tracking.models import Parcel, ParcelStatus, ParcelStatusHistory, PostOffice


class Command(BaseCommand):
    help = "Seed minimal demo data for quick API verification (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        origin_office, _ = PostOffice.objects.update_or_create(
            number=1,
            defaults={
                "city": "Kyiv",
                "address": "Main st 1",
                "postal_code": "01001",
            },
        )
        destination_office, _ = PostOffice.objects.update_or_create(
            number=2,
            defaults={
                "city": "Lviv",
                "address": "Square 2",
                "postal_code": "79000",
            },
        )

        created_parcel, created = Parcel.objects.get_or_create(
            tracking_number="TRKDEMO00001",
            defaults={
                "sender_full_name": "Ivan Petrenko",
                "sender_phone": "+380501112233",
                "recipient_full_name": "Olena Kovalenko",
                "recipient_phone": "+380671234567",
                "weight_kg": "2.50",
                "declared_value": "1200.00",
                "origin_office": origin_office,
                "destination_office": destination_office,
                "current_status": ParcelStatus.CREATED,
            },
        )
        if created:
            ParcelStatusHistory.objects.create(
                parcel=created_parcel,
                new_status=ParcelStatus.CREATED,
                office=origin_office,
                comment="Demo parcel created",
            )

        arrived_parcel, created = Parcel.objects.get_or_create(
            tracking_number="TRKDEMO00002",
            defaults={
                "sender_full_name": "Demo Sender",
                "sender_phone": "+380931112233",
                "recipient_full_name": "Demo Recipient",
                "recipient_phone": "+380971234567",
                "weight_kg": "1.20",
                "declared_value": "600.00",
                "origin_office": origin_office,
                "destination_office": destination_office,
                "current_status": ParcelStatus.ARRIVED,
            },
        )
        if created:
            ParcelStatusHistory.objects.bulk_create(
                [
                    ParcelStatusHistory(
                        parcel=arrived_parcel,
                        new_status=ParcelStatus.CREATED,
                        office=origin_office,
                        comment="Demo parcel created",
                    ),
                    ParcelStatusHistory(
                        parcel=arrived_parcel,
                        new_status=ParcelStatus.ACCEPTED,
                        office=origin_office,
                        comment="Accepted at origin office",
                    ),
                    ParcelStatusHistory(
                        parcel=arrived_parcel,
                        new_status=ParcelStatus.IN_TRANSIT,
                        office=origin_office,
                        comment="In transit to destination",
                    ),
                    ParcelStatusHistory(
                        parcel=arrived_parcel,
                        new_status=ParcelStatus.ARRIVED,
                        office=destination_office,
                        comment="Arrived at destination office",
                    ),
                ]
            )

        self.stdout.write(self.style.SUCCESS("Demo data is ready: offices #1/#2 and demo parcels."))
