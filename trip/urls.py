from django.conf import settings
from django.urls import path

from . import views

app_name = "trip"

urlpatterns = [
    path("trips/", views.trips, name="trips"),
    path("single-trip/<str:pk>/", views.single_trip, name="single-trip"),

    path("add-trip/", views.add_trip, name="add-trip"),
    path("edit-trip/<str:pk>/", views.edit_trip, name="edit-trip"),
    path("delete-trip/<str:pk>/", views.delete_trip, name="delete-trip"),

    path("single-trip/<str:pk>/add-trip-report/", views.add_trip_report,
         name="add-trip-report"),
    path("edit-trip-report/<str:pk>/", views.edit_trip_report,
         name="edit-trip-report"),
    path("delete-trip-report/<str:pk>/", views.delete_trip_report,
         name="delete-trip-report"),

    path("single-trip/<str:pk>/add-trip-basic/", views.add_trip_basic,
         name="add-trip-basic"),
    path("edit-trip-basic/<str:pk>/", views.edit_trip_basic,
         name="edit-trip-basic"),
    path("delete-trip-basic/<str:pk>/", views.delete_trip_basic,
         name="delete-trip-basic"),

    path("single-trip/<str:pk>/add-trip-advanced/", views.add_trip_advanced,
         name="add-trip-advanced"),
    path("edit-trip-advanced/<str:pk>/", views.edit_trip_advanced,
         name="edit-trip-advanced"),
    path("delete-trip-advanced/<str:pk>/", views.delete_trip_advanced,
         name="delete-trip-advanced"),

    path("single-trip/<str:pk>/add-trip-checklist/", views.add_trip_personal_checklist,
         name="add-trip-personal-checklist"),
    path("edit-trip-checklist/<str:pk>/", views.edit_trip_personal_checklist,
         name="edit-trip-personal-checklist"),
    path("delete-trip-checklist/<str:pk>/", views.delete_trip_personal_checklist,
         name="delete-trip-personal-checklist"),

    path("single-trip/<str:pk>/add-trip-additional/", views.add_trip_additional,
         name="add-trip-additional"),
    path("edit-trip-additional/<str:pk>/", views.edit_trip_additional,
         name="edit-trip-additional"),
    path("delete-trip-additional/<str:pk>/", views.delete_trip_additional,
         name="delete-trip-additional"),

    path("single-trip/<str:pk>/add-trip-cost/", views.add_trip_cost,
         name="add-trip-cost"),
    path("edit-trip-cost/<str:pk>/", views.edit_trip_cost,
         name="edit-trip-cost"),
    path("delete-trip-cost/<str:pk>/", views.delete_trip_cost,
         name="delete-trip-cost"),

]

if settings.DEBUG:  # !!! zmienić na produkcji na serwer docelowy!!! # usunąć na produkcji!
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
