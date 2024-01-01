from django.contrib import admin

from .models import (Trip, TripCost, TripBasicChecklist, TripAdvancedChecklist,
                     TripAdditionalInfo, TripReport, TripPersonalChecklist)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user", "created"]
    list_display = ["user", "name", "created"]


@admin.register(TripBasicChecklist)
class TripBasicChecklistAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user", "trip", "created"]
    list_display = ["user", "trip", "name", "created"]


@admin.register(TripAdvancedChecklist)
class TripAdvancedChecklistAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user", "trip", "created"]
    list_display = ["user", "trip", "name", "created"]


@admin.register(TripAdditionalInfo)
class TripAdditionalInfoAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user", "trip", "name", "created"]
    list_display = ["user", "trip", "name", "created"]


@admin.register(TripCost)
class TripCostAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user", "trip", "created"]
    list_display = ["user", "trip", "name", "created"]


@admin.register(TripReport)
class TripReportAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user", "trip", "created"]
    list_display = ["user", "trip", "created"]


admin.site.register(TripPersonalChecklist)
