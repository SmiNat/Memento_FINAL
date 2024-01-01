from django.contrib import admin

from .models import Attachment, Counterparty


@admin.register(Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user"]
    list_display = ["name", "user", "created"]
    list_filter = (
        "name",
        "user",
    )
    search_fields = [
        "cp_name",
        "user",
    ]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user"]
    list_display = ["attachment_name", "user", "created"]
