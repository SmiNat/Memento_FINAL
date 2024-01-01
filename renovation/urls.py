from django.conf import settings
from django.urls import path

from . import views

app_name = "renovation"

urlpatterns = [
    path("renovations/", views.renovations, name="renovations"),
    path("single-renovation/<str:pk>/", views.single_renovation, name="single-renovation"),

    path("add-renovation/", views.add_renovation, name="add-renovation"),
    path("edit-renovation/<str:pk>/", views.edit_renovation, name="edit-renovation"),
    path("delete-renovation/<str:pk>/", views.delete_renovation, name="delete-renovation"),

    path("single-renovation/<str:pk>/add-renovation-cost/",
         views.add_renovation_cost, name="add-renovation-cost"),
    path("edit-renovation-cost/<str:pk>/", views.edit_renovation_cost,
         name="edit-renovation-cost"),
    path("delete-renovation-cost/<str:pk>/", views.delete_renovation_cost,
         name="delete-renovation-cost"),

]

if settings.DEBUG:  # !!! zmienić na produkcji na serwer docelowy!!! # usunąć na produkcji!
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
