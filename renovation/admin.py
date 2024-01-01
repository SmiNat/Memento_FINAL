from django.contrib import admin

from .models import Renovation, RenovationCost


@admin.register(Renovation)
class RenovationAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user", "name", "created"]
    list_display = ["user", "name", "created"]


@admin.register(RenovationCost)
class RenovationCostAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user", "name", "created"]
    list_display = ["user", "renovation", "name", "created"]
