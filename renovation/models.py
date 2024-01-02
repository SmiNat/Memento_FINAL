from __future__ import annotations
import uuid

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from access.enums import Access


class Renovation(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    name = models.CharField(
        _("Nazwa"), max_length=255, help_text=_("Pole wymagane."))
    description = models.TextField(
        _("Opis"), max_length=500, null=True, blank=True,)
    estimated_cost = models.FloatField(
        _("Szacowany koszt"),
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))]
    )
    start_date = models.DateField(
        _("Data rozpoczęcia"), null=True, blank=True,
        # help_text=_("Format: YYYY-MM-DD (np. 2020-07-21)."),
    )
    end_date = models.DateField(
        _("Data zakończenia"), null=True, blank=True,
        # help_text=_("Format: YYYY-MM-DD (np. 2020-07-21)."),
    )
    access_granted = models.CharField(
        _("Dostęp do danych"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać te dane.")
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"], name="unique_renovation_name"
            )
        ]

    def __str__(self):
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def get_all_costs(self) -> float | None:
        """
        Return sum of all costs for RenovationCost queryset
        calculated on given Renovation instance.
        """
        sum_of_costs = 0
        queryset = self.renovationcost_set.filter(renovation=self.id)
        if queryset:
            for renovation_cost in queryset:
                cost_per_order = (float(renovation_cost.unit_price)
                                  * float(renovation_cost.units))
                sum_of_costs += cost_per_order
            return round(sum_of_costs, 2)
        else:
            return None

    def get_renovation_time_in_days(self) -> int | None:
        """
        Return duration of renovation in days.
        If start date and end date are the same, renovation days equals one.
        If start date and end date are different, both start and end date
        are calculated to overall number of renovation days.
        """
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return delta.days + 1
        else:
            return None

    def clean(self):
        if not self.access_granted in Access.values:
            raise ValidationError(_("Błędna wartość pola 'Dostęp do danych' (%s). Sprawdź czy "
                                    "polskie znaki nie zostały zastąpione innymi znakami."
                                    % self.access_granted))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class RenovationCost(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    renovation = models.ForeignKey(
        Renovation, on_delete=models.CASCADE, verbose_name=_("Remont"))
    name = models.CharField(
        _("Nazwa"), max_length=255,
        help_text=_("Pole wymagane.")
    )
    unit_price = models.FloatField(
        _("Cena jednostkowa"),
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Pole wymagane.")
    )
    units = models.FloatField(
        _("Liczba sztuk"), default=1,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Pole wymagane."),
    )
    description = models.TextField(
        _("Opis"), max_length=500,
        null=True, blank=True,
    )
    order = models.TextField(
        _("Informacje dot. zamówienia"), max_length=500,
        null=True, blank=True,
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def sum_of_costs(self, queryset=None) -> float:
        """
        Return sum of all renovation costs.
        Parameters:
        ----------
        queryset:
            Queryset of RenovationCost model instances.
            If queryset is None, default queryset equals to
            RenovationCost.objects.filter(renovation=self.renovation)
        """
        cost_total = 0
        if not queryset:
            renovation_queryset = RenovationCost.objects.filter(
                renovation=self.renovation)
        else:
            renovation_queryset = queryset
        for cost in renovation_queryset:
            amount = cost.unit_price * cost.units
            cost_total += amount
        return round(cost_total, 2)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
