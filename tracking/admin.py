from django.contrib import admin

from .models import Parcel, ParcelStatusHistory, PostOffice


@admin.register(PostOffice)
class PostOfficeAdmin(admin.ModelAdmin):
    list_display = ("id", "number", "city", "postal_code")
    search_fields = ("city", "number", "postal_code")


class ParcelStatusHistoryInline(admin.TabularInline):
    model = ParcelStatusHistory
    extra = 0
    readonly_fields = ("new_status", "office", "comment", "changed_at")


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_number",
        "current_status",
        "origin_office",
        "destination_office",
        "created_at",
    )
    list_filter = ("current_status", "origin_office__city", "destination_office__city")
    search_fields = ("tracking_number", "sender_full_name", "recipient_full_name")
    inlines = [ParcelStatusHistoryInline]


@admin.register(ParcelStatusHistory)
class ParcelStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("parcel", "new_status", "office", "changed_at")
    list_filter = ("new_status", "office__city")
    search_fields = ("parcel__tracking_number",)
