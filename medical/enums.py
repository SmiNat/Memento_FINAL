from django.db import models
from django.utils.translation import gettext_lazy as _


class MedicationDays(models.TextChoices):
    MONDAY = _("Poniedziałek"), _("Poniedziałek")
    TUESDAY = _("Wtorek"), _("Wtorek")
    WEDNESDAY = _("Środa"), _("Środa")
    THURSDAY = _("Czwartek"), _("Czwartek")
    FRIDAY = _("Piątek"), _("Piątek")
    SUNDAY = _("Sobota"), _("Sobota")
    SATURDAY = _("Niedziela"), _("Niedziela")


class MedicationFrequency(models.TextChoices):
    EVERY_DAY = _("Codziennie"), _("Codziennie")
    INDICATED_DAYS = _("We wskazane dni tygodnia"), _("We wskazane dni tygodnia")
    EVERY_FEW_DAYS = _("Co kilka dni"), _("Co kilka dni")
    OCCASIONALLY = _("Sporadycznie"), _("Sporadycznie")
    OTHER = _("Inne"), _("Inne")
