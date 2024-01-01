from django.contrib import admin

from .models import MedCard, Medicine, MedicalVisit, HealthTestResult

admin.site.register(MedCard)
admin.site.register(Medicine)
admin.site.register(MedicalVisit)
admin.site.register(HealthTestResult)
