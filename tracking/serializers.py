import logging

from django.db import transaction
from rest_framework import serializers

from .models import Parcel, ParcelStatus, ParcelStatusHistory, PostOffice


status_logger = logging.getLogger("tracking.status")


class PostOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostOffice
        fields = ["id", "number", "city", "address", "postal_code"]


class ParcelStatusHistorySerializer(serializers.ModelSerializer):
    office = PostOfficeSerializer(read_only=True)

    class Meta:
        model = ParcelStatusHistory
        fields = ["id", "new_status", "office", "comment", "changed_at"]


class ParcelCreateSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        origin = attrs.get("origin_office")
        destination = attrs.get("destination_office")
        if origin and destination and origin.pk == destination.pk:
            raise serializers.ValidationError(
                {"destination_office": "Origin and destination offices must be different."}
            )
        return attrs

    class Meta:
        model = Parcel
        fields = [
            "tracking_number",
            "sender_full_name",
            "sender_phone",
            "recipient_full_name",
            "recipient_phone",
            "weight_kg",
            "declared_value",
            "origin_office",
            "destination_office",
            "current_status",
            "created_at",
        ]
        read_only_fields = ["tracking_number", "current_status", "created_at"]

    @transaction.atomic
    def create(self, validated_data):
        parcel = super().create(validated_data)
        ParcelStatusHistory.objects.create(
            parcel=parcel,
            new_status=ParcelStatus.CREATED,
            office=parcel.origin_office,
            comment="Parcel created",
        )
        status_logger.info(
            "Parcel created tracking=%s status=%s office=%s",
            parcel.tracking_number,
            ParcelStatus.CREATED,
            parcel.origin_office_id,
        )
        return parcel


class ParcelListSerializer(serializers.ModelSerializer):
    origin_office_city = serializers.CharField(source="origin_office.city", read_only=True)
    destination_office_city = serializers.CharField(source="destination_office.city", read_only=True)

    class Meta:
        model = Parcel
        fields = [
            "tracking_number",
            "current_status",
            "origin_office_city",
            "destination_office_city",
            "created_at",
        ]


class ParcelDetailSerializer(serializers.ModelSerializer):
    origin_office = PostOfficeSerializer(read_only=True)
    destination_office = PostOfficeSerializer(read_only=True)
    status_history = ParcelStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Parcel
        fields = [
            "tracking_number",
            "sender_full_name",
            "sender_phone",
            "recipient_full_name",
            "recipient_phone",
            "weight_kg",
            "declared_value",
            "origin_office",
            "destination_office",
            "current_status",
            "created_at",
            "status_history",
        ]


class ParcelStatusUpdateSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=ParcelStatus.choices)
    office = serializers.PrimaryKeyRelatedField(queryset=PostOffice.objects.all())
    comment = serializers.CharField(required=False, allow_blank=True, max_length=255)

    TERMINAL_STATUSES = {ParcelStatus.DELIVERED, ParcelStatus.RETURNED}

    def validate(self, attrs):
        parcel: Parcel = self.context["parcel"]
        new_status = attrs["new_status"]
        office = attrs["office"]

        if parcel.current_status in self.TERMINAL_STATUSES:
            raise serializers.ValidationError("Terminal parcel status cannot be changed.")

        if new_status == ParcelStatus.DELIVERED and parcel.current_status != ParcelStatus.ARRIVED:
            raise serializers.ValidationError(
                "Parcel can be delivered only after it arrives at destination office."
            )

        if new_status == ParcelStatus.ARRIVED and office.id != parcel.destination_office_id:
            raise serializers.ValidationError("Arrived status must be assigned in destination office.")

        if new_status == ParcelStatus.ACCEPTED and office.id != parcel.origin_office_id:
            raise serializers.ValidationError("Accepted status must be assigned in origin office.")

        if new_status == ParcelStatus.DELIVERED and office.id != parcel.destination_office_id:
            raise serializers.ValidationError("Delivered status must be assigned in destination office.")

        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        parcel: Parcel = self.context["parcel"]
        actor = self.context.get("request_user")
        old_status = parcel.current_status
        parcel.current_status = self.validated_data["new_status"]
        parcel.save(update_fields=["current_status"])
        ParcelStatusHistory.objects.create(
            parcel=parcel,
            new_status=self.validated_data["new_status"],
            office=self.validated_data["office"],
            comment=self.validated_data.get("comment", ""),
        )
        status_logger.info(
            "Parcel status updated tracking=%s from=%s to=%s office=%s by=%s",
            parcel.tracking_number,
            old_status,
            self.validated_data["new_status"],
            self.validated_data["office"].id,
            getattr(actor, "username", "unknown"),
        )
        return parcel
