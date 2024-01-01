from django.conf import settings
from django.urls import path

from . import views

app_name = "access"

urlpatterns = [
    path("access/", views.access_page, name="access"),
    path("data_access/<slug:slug>/<int:page>/", views.access_to_models, name="data-access"),
    path("data_access_payments/<slug:slug>/<int:page>/", views.access_to_payments, name="data-access-payments"),
    path("data_access_planner/<slug:slug>/<int:page>/", views.access_to_planner, name="data-access-planner"),
    path("data_access_medical/<slug:slug>/<int:page>/", views.access_to_medical, name="data-access-medical"),


]

if settings.DEBUG:  # !!! zmienić na produkcji na serwer docelowy!!! # usunąć na produkcji!
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
