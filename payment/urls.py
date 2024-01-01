from django.conf import settings
from django.urls import path

from . import views

app_name = "payment"

urlpatterns = [
    path("payments/", views.payments, name="payments"),
    path("payment/<str:pk>/", views.single_payment, name="single-payment"),

    path("add-payment/", views.add_payment, name="add-payment"),
    path("edit-payment/<str:pk>/", views.edit_payment, name="edit-payment"),
    path("delete-payment/<str:pk>/", views.delete_payment, name="delete-payment"),

]

if settings.DEBUG:   # !!! zmienić na produkcji na serwer docelowy!!! # usunąć na produkcji!
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
