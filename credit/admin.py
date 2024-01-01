from django.contrib import admin

from .models import (Credit, CreditInsurance, CreditCollateral, CreditTranche,
                     CreditInterestRate, CreditAdditionalCost,
                     CreditEarlyRepayment)


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user"]
    list_display = ["name", "user", "created"]


@admin.register(CreditInterestRate)
class CreditInterestRateAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user"]
    list_display = ["credit", "user", "interest_rate", "created"]


@admin.register(CreditCollateral)
class CreditCollateralAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user"]
    list_display = ["credit", "user", "description", "created"]


@admin.register(CreditInsurance)
class CreditInsuranceAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user"]
    list_display = ["credit", "user", "created"]


@admin.register(CreditTranche)
class CreditTranchesAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user"]
    list_display = ["credit", "user", "created"]


@admin.register(CreditAdditionalCost)
class CreditAdditionalCostsAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user"]
    list_display = ["credit", "user", "name", "created"]


@admin.register(CreditEarlyRepayment)
class CreditEarlyRepaymentAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["user"]
    list_display = ["credit", "user", "created"]
