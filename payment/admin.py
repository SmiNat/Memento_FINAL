from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user"]
    list_display = [
        "name",
        "payment_type",
        "user",
        "payment_frequency",
        "created",
    ]
