from django.conf import settings
from django.urls import path

from . import views

app_name = "credit"

urlpatterns = [
    path("credits/", views.credits, name="credits"),
    path("single-credit/<str:pk>/", views.single_credit, name="single-credit"),

    path("add-credit/", views.add_credit, name="add-credit"),
    path("edit-credit/<str:pk>/", views.edit_credit, name="edit-credit"),
    path("delete-credit/<str:pk>/", views.delete_credit, name="delete-credit"),

    path("single-credit/<str:pk>/add-credit-interest-rate/", views.add_credit_interest_rate,
         name="add-credit-interest-rate"),
    path("edit-credit-interest-rate/<str:pk>/", views.edit_credit_interest_rate,
         name="edit-credit-interest-rate"),
    path("delete-credit-interest-rate/<str:pk>/", views.delete_credit_interest_rate,
         name="delete-credit-interest-rate"),

    path("single-credit/<str:pk>/add-credit-insurance/", views.add_credit_insurance,
         name="add-credit-insurance"),
    path("edit-credit-insurance/<str:pk>/", views.edit_credit_insurance,
         name="edit-credit-insurance"),
    path("delete-credit-insurance/<str:pk>/", views.delete_credit_insurance,
         name="delete-credit-insurance"),

    path("single-credit/<str:pk>/add-credit-tranche/", views.add_credit_tranche,
         name="add-credit-tranche"),
    path("edit-credit-tranche/<str:pk>/", views.edit_credit_tranche,
         name="edit-credit-tranche"),
    path("delete-credit-tranche/<str:pk>/", views.delete_credit_tranche,
         name="delete-credit-tranche"),

    path("single-credit/<str:pk>/add-credit-collateral/", views.add_credit_collateral,
         name="add-credit-collateral"),
    path("edit-credit-collateral/<str:pk>/", views.edit_credit_collateral,
         name="edit-credit-collateral"),
    path("delete-credit-collateral/<str:pk>/", views.delete_credit_collateral,
         name="delete-credit-collateral"),

    path("single-credit/<str:pk>/add-credit-additional-cost/", views.add_credit_additional_cost,
         name="add-credit-additional-cost"),
    path("edit-credit-additional-cost/<str:pk>/", views.edit_credit_additional_cost,
         name="edit-credit-additional-cost"),
    path("delete-credit-additional-cost/<str:pk>/", views.delete_credit_additional_cost,
         name="delete-credit-additional-cost"),

    path("single-credit/<str:pk>/add-credit-early-repayment/", views.add_credit_early_repayment,
         name="add-credit-early-repayment"),
    path("edit-credit-early-repayment/<str:pk>/", views.edit_credit_early_repayment,
         name="edit-credit-early-repayment"),
    path("delete-credit-early-repayment/<str:pk>/", views.delete_credit_early_repayment,
         name="delete-credit-early-repayment"),

    path("credit-repayment-schedule/<str:pk>/", views.credit_repayment_schedule,
         name="credit-repayment-schedule"),
    path("access-to-credit-schedule/<slug:slug>/", views.access_to_credit_schedule,
         name="access-to-credit-schedule"),

]

if settings.DEBUG:  # !!! zmienić na produkcji na serwer docelowy!!! # usunąć na produkcji!
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
