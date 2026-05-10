from django.urls import path

from .views import (
    OfficeParcelsAPIView,
    ParcelDetailAPIView,
    ParcelListCreateAPIView,
    ParcelStatusUpdateAPIView,
)

urlpatterns = [
    path("parcels/", ParcelListCreateAPIView.as_view(), name="parcel-list-create"),
    path("parcels/<str:tracking_number>/", ParcelDetailAPIView.as_view(), name="parcel-detail"),
    path(
        "parcels/<str:tracking_number>/status/",
        ParcelStatusUpdateAPIView.as_view(),
        name="parcel-status-update",
    ),
    path("offices/<int:id>/parcels/", OfficeParcelsAPIView.as_view(), name="office-parcels"),
]
