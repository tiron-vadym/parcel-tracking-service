from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Parcel, ParcelStatus, ParcelStatusHistory, PostOffice


class ParcelAPITestCase(APITestCase):
    def setUp(self):
        self.origin_office = PostOffice.objects.create(
            number=1, city="Kyiv", address="Main st 1", postal_code="01001"
        )
        self.destination_office = PostOffice.objects.create(
            number=2, city="Lviv", address="Square 2", postal_code="79000"
        )
        self.user = get_user_model().objects.create_user(username="worker", password="pass12345")
        self.token = Token.objects.create(user=self.user)

    def create_parcel(self, authenticated: bool = True) -> Parcel:
        if authenticated:
            self.authenticate_worker()
        response = self.client.post(
            reverse("parcel-list-create"),
            {
                "sender_full_name": "Ivan Petrenko",
                "sender_phone": "+380501112233",
                "recipient_full_name": "Olena Kovalenko",
                "recipient_phone": "+380671234567",
                "weight_kg": "2.50",
                "declared_value": "1200.00",
                "origin_office": self.origin_office.id,
                "destination_office": self.destination_office.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        tracking_number = response.data["tracking_number"]
        return Parcel.objects.get(tracking_number=tracking_number)

    def authenticate_worker(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token.key}")

    def test_create_parcel_generates_history(self):
        parcel = self.create_parcel()
        self.assertEqual(parcel.current_status, ParcelStatus.CREATED)
        self.assertTrue(
            ParcelStatusHistory.objects.filter(
                parcel=parcel, new_status=ParcelStatus.CREATED, office=self.origin_office
            ).exists()
        )

    def test_cannot_set_same_origin_and_destination(self):
        self.authenticate_worker()
        response = self.client.post(
            reverse("parcel-list-create"),
            {
                "sender_full_name": "Ivan Petrenko",
                "sender_phone": "+380501112233",
                "recipient_full_name": "Olena Kovalenko",
                "recipient_phone": "+380671234567",
                "weight_kg": "2.50",
                "declared_value": "1200.00",
                "origin_office": self.origin_office.id,
                "destination_office": self.origin_office.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_deliver_before_arrived(self):
        parcel = self.create_parcel()
        self.authenticate_worker()
        response = self.client.post(
            reverse("parcel-status-update", kwargs={"tracking_number": parcel.tracking_number}),
            {
                "new_status": ParcelStatus.DELIVERED,
                "office": self.destination_office.id,
                "comment": "Try premature delivery",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_change_terminal_status(self):
        parcel = self.create_parcel()
        parcel.current_status = ParcelStatus.DELIVERED
        parcel.save(update_fields=["current_status"])
        self.authenticate_worker()
        response = self.client.post(
            reverse("parcel-status-update", kwargs={"tracking_number": parcel.tracking_number}),
            {
                "new_status": ParcelStatus.RETURNED,
                "office": self.destination_office.id,
                "comment": "",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_update_requires_token(self):
        parcel = self.create_parcel()
        self.client.credentials()
        response = self.client.post(
            reverse("parcel-status-update", kwargs={"tracking_number": parcel.tracking_number}),
            {
                "new_status": ParcelStatus.ACCEPTED,
                "office": self.origin_office.id,
                "comment": "Accepted at office",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_parcel_routes_require_token(self):
        create_response = self.client.post(
            reverse("parcel-list-create"),
            {
                "sender_full_name": "Ivan Petrenko",
                "sender_phone": "+380501112233",
                "recipient_full_name": "Olena Kovalenko",
                "recipient_phone": "+380671234567",
                "weight_kg": "2.50",
                "declared_value": "1200.00",
                "origin_office": self.origin_office.id,
                "destination_office": self.destination_office.id,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_401_UNAUTHORIZED)

        list_response = self.client.get(reverse("parcel-list-create"))
        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_status_update_creates_history(self):
        parcel = self.create_parcel()
        response = self.client.post(
            reverse("parcel-status-update", kwargs={"tracking_number": parcel.tracking_number}),
            {
                "new_status": ParcelStatus.ACCEPTED,
                "office": self.origin_office.id,
                "comment": "Accepted at office",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parcel.refresh_from_db()
        self.assertEqual(parcel.current_status, ParcelStatus.ACCEPTED)
        self.assertTrue(
            ParcelStatusHistory.objects.filter(
                parcel=parcel, new_status=ParcelStatus.ACCEPTED, office=self.origin_office
            ).exists()
        )
