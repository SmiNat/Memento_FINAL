from django.conf import \
    settings  # do wyświetlania uploadowanych plików na www (tymczasowe rozw. do czasu developmentu - później serwer AWS/Azure)
from django.conf.urls.static import \
    static  # do wyświetlania uploadowanych plików na www (tymczasowe rozw. do czasu developmentu - później serwer AWS/Azure)
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("user.urls")),
    path("", include("connection.urls")),
    path("", include("payment.urls")),
    path("", include("access.urls")),
    path("", include("credit.urls")),
    path("", include("renovation.urls")),
    path("", include("trip.urls")),
    path("", include("planner.urls")),
    path("", include("medical.urls")),
]


urlpatterns += static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)  # (tymczasowe rozw. do czasu zakończenia developmentu - później serwer AWS/Azure) # usunąć na produkcji!
urlpatterns += static(
    settings.STATIC_URL, document_root=settings.STATIC_ROOT
)  # (tymczasowe rozw. do czasu zakończenia developmentu - później serwer AWS/Azure) # usunąć na produkcji!
