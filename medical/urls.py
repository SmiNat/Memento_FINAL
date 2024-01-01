from django.conf import settings
from django.urls import path

from . import views

app_name = "medical"

urlpatterns = [
    path("medcard/", views.medcard, name="medcard"),
    path("add-medcard/", views.add_medcard, name="add-medcard"),
    path("edit-medcard/<str:pk>/", views.edit_medcard, name="edit-medcard"),
    path("delete-medcard/<str:pk>/", views.delete_medcard, name="delete-medcard"),

    path("medicines/", views.medicines, name="medicines"),
    path("single-medicine/<str:pk>/", views.single_medicine, name="single-medicine"),
    path("add-medicine/", views.add_medicine, name="add-medicine"),
    path("edit-medicine/<str:pk>/", views.edit_medicine, name="edit-medicine"),
    path("delete-medicine/<str:pk>/", views.delete_medicine, name="delete-medicine"),

    path("medical-visits/", views.medical_visits, name="medical-visits"),
    path("single-visit/<str:pk>/", views.single_visit, name="single-visit"),
    path("add-visit/", views.add_visit, name="add-visit"),
    path("edit-visit/<str:pk>/", views.edit_visit, name="edit-visit"),
    path("delete-visit/<str:pk>/", views.delete_visit, name="delete-visit"),

    path("test-results/", views.test_results, name="test-results"),
    path("single-test-result/<str:pk>/", views.single_test_result, name="single-test-result"),
    path("add-test-result/", views.add_test_result, name="add-test-result"),
    path("edit-test-result/<str:pk>/", views.edit_test_result, name="edit-test-result"),
    path("delete-test-result/<str:pk>/", views.delete_test_result, name="delete-test-result"),

]

if settings.DEBUG:  # !!! zmienić na produkcji na serwer docelowy!!! # usunąć na produkcji!
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
