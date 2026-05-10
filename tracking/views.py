from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema

from .models import Parcel, ParcelStatus
from .serializers import (
    ParcelCreateSerializer,
    ParcelDetailSerializer,
    ParcelListSerializer,
    ParcelStatusUpdateSerializer,
)


class ParcelListCreateAPIView(generics.ListCreateAPIView):
    queryset = Parcel.objects.select_related("origin_office", "destination_office").all()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter parcels by current status.",
            ),
            OpenApiParameter(
                name="from_city",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter parcels by origin office city.",
            ),
        ]
    )
    def get_serializer_class(self):
        if self.request.method == "POST":
            return ParcelCreateSerializer
        return ParcelListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        from_city = self.request.query_params.get("from_city")

        if status_filter:
            queryset = queryset.filter(current_status=status_filter)
        if from_city:
            queryset = queryset.filter(origin_office__city__iexact=from_city)

        return queryset


class ParcelDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ParcelDetailSerializer
    lookup_field = "tracking_number"
    queryset = Parcel.objects.select_related("origin_office", "destination_office").prefetch_related(
        "status_history__office"
    )


class ParcelStatusUpdateAPIView(APIView):
    @extend_schema(
        request=ParcelStatusUpdateSerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Update parcel status and create a status history record.",
    )
    def post(self, request, tracking_number: str):
        parcel = generics.get_object_or_404(Parcel, tracking_number=tracking_number)
        serializer = ParcelStatusUpdateSerializer(
            data=request.data,
            context={"parcel": parcel, "request_user": request.user},
        )
        serializer.is_valid(raise_exception=True)
        parcel = serializer.save()
        return Response(
            {"tracking_number": parcel.tracking_number, "current_status": parcel.current_status},
            status=status.HTTP_200_OK,
        )


class OfficeParcelsAPIView(generics.ListAPIView):
    serializer_class = ParcelListSerializer

    def get_queryset(self):
        office_id = self.kwargs["id"]
        return Parcel.objects.select_related("origin_office", "destination_office").filter(
            current_status=ParcelStatus.ARRIVED,
            destination_office_id=office_id,
        )
