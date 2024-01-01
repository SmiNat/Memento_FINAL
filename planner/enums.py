from django.db import models
from django.utils.translation import gettext_lazy as _


class ExecutionStatus(models.TextChoices):
    PLANNED = _("Planowane"), _("Planowane")
    COMPLETED = _("Zrealizowane"), _("Zrealizowane")


class RequirementStatus(models.TextChoices):
    OPTIONAL = _("Opcjonalne"), _("Opcjonalne")
    REQUIRED = _("Niezbędne"), _("Niezbędne")   # Wymagane


class ValidityStatus(models.TextChoices):
    URGENT = _("Pilne"), _("Pilne")
    NOT_URGENT = _("Na kiedyś"), _("Na kiedyś")
