from django.conf import settings
from django.urls import path

from . import views

app_name = "connection"
urlpatterns = [
    path("counterparties/", views.counterparties, name="counterparties"),
    path("counterparty/<str:pk>/",
         views.single_counterparty, name="single-counterparty"),
    path("add-counterparty/", views.add_counterparty, name="add-counterparty"),
    path("edit-counterparty/<str:pk>/",
         views.edit_counterparty, name="edit-counterparty"),
    path(
        "delete-counterparty/<str:pk>/",
        views.delete_counterparty,
        name="delete-counterparty",
    ),

    path("attachments/", views.attachments, name="attachments"),
    path("download-attachment/<slug:slug>/<str:pk>/",
         views.download_attachment, name="download-attachment"),
    path("add-attachment/", views.add_attachment, name="add-attachment"),
    path("delete-attachment/<str:pk>/",
         views.delete_attachment, name="delete-attachment"),

]

if settings.DEBUG:  # !!! zmienić na produkcji na serwer docelowy!!! # usunąć na produkcji!
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
