from __future__ import annotations
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from access.enums import Access

from .enums import (PaymentMethod, PaymentType, PaymentStatus, PaymentFrequency,
                    PaymentMonth)


class Payment(models.Model):

    PAYMENT_DAY = ((0, _("Ostatni")),) + tuple(
        (x, str(x)) for x in range(1, 32)
    )

    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik"),
    )
    name = models.CharField(
        _("Nazwa"),
        max_length=255,
        help_text=_("Pole wymagane."),
    )
    payment_type = models.CharField(
        _("Grupa opłat"), max_length=100,
        blank=True, null=True,
        choices=PaymentType.choices,
    )
    payment_method = models.CharField(
        _("Sposób płatności"), max_length=100,
        blank=True, null=True,
        choices=PaymentMethod.choices,
    )
    payment_status = models.CharField(
        _("Status płatności"),
        max_length=100,
        blank=True, null=True,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNKNOWN,
    )
    payment_frequency = models.CharField(
        _("Częstotliwość płatności"),
        max_length=100,
        blank=True, null=True,
        choices=PaymentFrequency.choices,
    )
    payment_months = models.CharField(
        max_length=100,
        blank=True, null=True,
        # choices=PAYMENT_MONTHS,
        verbose_name=_("Miesiące płatności"),
    )
    payment_day = models.PositiveSmallIntegerField(
        _("Dzień płatności"), choices=PAYMENT_DAY, blank=True, null=True,
    )
    payment_value = models.FloatField(
        _("Wysokość płatności"), max_length=12,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message="Wartość nie może być liczbą ujemną.")
        ]
    )
    notes = models.TextField(
        _("Uwagi"), max_length=500,
        null=True, blank=True,
    )
    start_of_agreement = models.DateField(
        _("Data zawarcia umowy"),
        null=True, blank=True,
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21).")
    )
    end_of_agreement = models.DateField(
        _("Data wygaśnięcia umowy"),
        null=True, blank=True,
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21).")
    )
    access_granted = models.CharField(
        _("Dostęp do danych"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych "
                    "może przeglądać te dane.")
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_payment_name")
            ]

    @classmethod
    def field_names(cls) -> list:
        """Return list of model field names (except for many-to-many fields)."""
        return list(f.name for f in cls._meta.fields)

    def __str__(self) -> str:
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield field.verbose_name, field.value_to_string(self)

    def payment_months_to_list(self):
        if not self.payment_months:
            return []
        return self.payment_months.split(",")

    def payment_months_to_list_of_names(self):
        if not self.payment_months_to_list():
            return []
        months_by_names = []
        for month_number in self.payment_months_to_list():
            month = PaymentMonth.choices[int(month_number)-1][1]
            months_by_names.append(month)
        return months_by_names

    def clean(self):
        if self.access_granted not in Access.values:
            raise ValidationError(_("Błędna wartość pola 'Dostęp do danych' (%s). Sprawdź czy "
                                    "polskie znaki nie zostały zastąpione innymi znakami."
                                    % self.access_granted))
        if self.payment_type and self.payment_type not in PaymentType.values:
            raise ValidationError(_("Błędna wartość pola 'Grupa opłat' (%s). Sprawdź czy "
                                    "polskie znaki nie zostały zastąpione innymi znakami."
                                    % self.payment_type))
        if self.payment_method and self.payment_method not in PaymentMethod.values:
            raise ValidationError(_("Błędna wartość pola 'Sposób płatności' (%s). Sprawdź czy "
                                    "polskie znaki nie zostały zastąpione innymi znakami."
                                    % self.payment_method))
        if self.payment_status and self.payment_status not in PaymentStatus.values:
            raise ValidationError(_("Błędna wartość pola 'Status płatności' (%s). Sprawdź czy "
                                    "polskie znaki nie zostały zastąpione innymi znakami."
                                    % self.payment_status))
        if self.payment_frequency and self.payment_frequency not in PaymentFrequency.values:
            raise ValidationError(_("Błędna wartość pola 'Częstotliwość płatności' (%s). Sprawdź czy "
                                    "polskie znaki nie zostały zastąpione innymi znakami."
                                    % self.payment_frequency))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
