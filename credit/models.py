from __future__ import annotations
import decimal
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .enums import (CreditType, InstallmentType, TypeOfInterest, Currency,
                    Frequency, InsuranceType, RepaymentAction, YesNo)
from access.enums import Access
from user.handlers import create_slug


class Credit(models.Model):

    PAYMENT_DAY = ((0, _("Ostatni dzień miesiąca")),) + tuple(
        (x, str(x)) for x in range(1, 32)
    )

    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    slug = models.SlugField(null=False, unique=True)

    # Basic credit data
    name = models.CharField(
        _("Nazwa kredytu"), max_length=255,
        help_text=_("Pole wymagane."),
    )
    credit_number = models.CharField(
        _("Numer umowy kredytu"), max_length=100,
        null=True, blank=True,
    )
    type = models.CharField(
        _("Rodzaj kredytu"), max_length=100,
        choices=CreditType.choices, default=CreditType.OTHER,
    )
    currency = models.CharField(
        _("Waluta"), max_length=20,
        choices=Currency.choices, default=Currency.PLN,
    )
    credit_amount = models.DecimalField(
        _("Wartość kredytu"), max_digits=11, decimal_places=2,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Pole wymagane.")
    )
    own_contribution = models.DecimalField(
        _("Wkład własny"), max_digits=11, decimal_places=2, default=0,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Nie wlicza się do wartości kredytu."),
    )
    market_value = models.DecimalField(
        _("Wartość rynkowa nabywanej rzeczy/nieruchomości"),
        max_digits=11, decimal_places=2, default=0, null=True, blank=True,
        validators=[MinValueValidator(
            0, message="Wartość nie może być liczbą ujemną.")]
    )
    credit_period = models.PositiveSmallIntegerField(
        _("Okres kredytowania (w miesiącach)"),
        help_text=_("Liczba miesięcy, po której następuje spłata kredytu "
                    "(łącznie z karencją). Pole wymagane."),
    )
    grace_period = models.PositiveSmallIntegerField(
        _("Okres karencji (w miesiącach)"), default=0, null=True, blank=True,
    )

    # Installments
    installment_type = models.CharField(
        _("Rodzaj raty"), max_length=100,
        choices=InstallmentType.choices,
        default=InstallmentType.EQUAL_INSTALLMENTS,
    )
    installment_frequency = models.CharField(
        _("Częstotliwość płatności raty"), max_length=30,
        choices=Frequency.choices, default=Frequency.MONTHLY,
    )
    total_installment = models.DecimalField(
        _("Wysokość raty całkowitej (dla rat równych)"),
        max_digits=8, decimal_places=2,  default=0,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Podaj wysokość raty (zero dla rat malejących). "
                    "Pole wymagane."),
    )
    capital_installment = models.DecimalField(
        _("Wysokość raty kapitałowej (dla rat malejących)"),
        max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Podaj wysokość raty (zero dla rat równych). "
                    "Pole wymagane."),
    )

    # Interest rate
    type_of_interest = models.CharField(
        _("Rodzaj oprocentowania"), max_length=20,
        choices=TypeOfInterest.choices, default=TypeOfInterest.VARIABLE,
    )
    fixed_interest_rate = models.DecimalField(
        _("Wysokość oprocentowania stałego (w %)"),
        max_digits=4, decimal_places=2, default=0,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Wysokość oprocentowania razem z marżą banku. Wpisz zero "
                    "jeśli nie dotyczy. Pole wymagane."),
    )
    floating_interest_rate = models.DecimalField(
        _("Wysokość oprocentowania zmiennego (w %)"),
        max_digits=4, decimal_places=2, default=0,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Wysokość w dniu zawarcia umowy (bez marży banku). "
                    "Wpisz zero jeśli nie dotyczy. Pole wymagane."),
    )
    bank_margin = models.DecimalField(
        _("Marża banku w oprocentowaniu zmiennym (w %)"),
        max_digits=4, decimal_places=2, default=0,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Np. wartość 5.5 oznacza 5,5%. Wpisz zero jeśli nie "
                    "dotyczy. Pole wymagane."),
    )
    interest_rate_benchmark = models.CharField(
        _("Rodzaj benchmarku"), max_length=100,
        default=_("Brak"), null=True, blank=True,
        help_text=_("Przykładowo: WIBOR 3M, EURIBOR 6M."),
    )

    # Dates
    date_of_agreement = models.DateField(
        _("Data zawarcia umowy"),
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane."),
    )
    start_of_credit = models.DateField(
        _("Data uruchomienia kredytu"),
        help_text=_("Data wypłaty środków lub uruchomienia pierwszej transzy "
                    "kredytu. Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane."),
    )
    start_of_payment = models.DateField(
        _("Data rozpoczęcia spłaty kredytu"),
        help_text=_("Data płatności pierwszej raty. "
                    "Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane."),
    )
    payment_day = models.PositiveSmallIntegerField(
        _("Dzień płatności raty"),
        choices=PAYMENT_DAY, help_text=_("Pole wymagane.")
    )

    # Other information
    provision = models.DecimalField(
        _("Wysokość prowizji (w wybranej walucie)"),
        max_digits=11, decimal_places=2, default=0, null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Płatna w dniu uruchomienia kredytu."),
    )
    credited_provision = models.CharField(
        _("Kredytowanie prowizji"), max_length=5,
        choices=YesNo.choices, default=YesNo.NO,
    )
    tranches_in_credit = models.CharField(
        _("Transzowanie wypłat"), max_length=5,
        choices=YesNo.choices, default=YesNo.NO,
    )
    life_insurance_first_year = models.DecimalField(
        _("Kredytowane ubezpieczenie na życie"),
        max_digits=8, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Roczna składka za 1. rok. Kredytowane w dniu "
                    "uruchomienia kredytu."),
    )
    property_insurance_first_year = models.DecimalField(
        _("Kredytowane ubezpieczenie rzeczy/nieruchomości"),
        max_digits=8, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Roczna składka za 1. rok. Kredytowane w dniu "
                    "uruchomienia kredytu."),
    )
    collateral_required = models.CharField(
        _("Wymagane zabezpieczenie kredytu"), max_length=5,
        choices=YesNo.choices, default=YesNo.NO,
    )
    collateral_rate = models.DecimalField(
        _("Oprocentowanie dodatkowe (pomostowe)"),
        max_digits=4, decimal_places=2, default=0, null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Dodatkowe oprocentowanie do czasu ustanowienia "
                    "zabezpieczenia kredytu."),
        )
    notes = models.TextField(_("Uwagi"), max_length=500, null=True, blank=True)

    # Access
    access_granted = models.CharField(
        _("Dostęp do danych"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać te dane."),
    )
    access_granted_for_schedule = models.CharField(
        _("Dostęp do harmonogramu"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może przeglądać "
                    "harmonogram kredytu."),
    )

    # Timestamps
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "name"],
                                    name="unique_credit_name"),
        ]

    def __str__(self) -> str:
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def get_absolute_url(self):
        return reverse("access-to-credit-schedule", args=[str(self.slug)])

    def total_loan_value(self):
        """Total value of debt to repay at the date of agreement.
        Total loan value includes:
        - value of loan to repay,
        - provision amount (if credited),
        - first year life insurance (if credited),
        - first year property insurance (if credited),
        Own contribution is not included in value of loan
        (serves only to calculate loan-to-value indicator)."""
        provision = self.provision if (
                isinstance(self.provision, (int, float, decimal.Decimal))
                and self.provision > 0
                and self.credited_provision == _("Tak")
        ) else 0
        loan_value = self.credit_amount
        loan_value = loan_value + provision
        loan_value = loan_value + (self.life_insurance_first_year if self.life_insurance_first_year else 0)
        loan_value = loan_value + (self.property_insurance_first_year if self.property_insurance_first_year else 0)
        return loan_value

    def full_rate(self):
        """Floating interest rate with bank margin."""
        return decimal.Decimal(self.floating_interest_rate) + decimal.Decimal(self.bank_margin)

    def save(self, *args, **kwargs):
        slugs = Credit.objects.all().exclude(id=self.id).values_list(
            "slug", flat=True)
        if not self.slug:
            self.slug = create_slug(self.user)
        while self.slug in slugs:
            self.slug = create_slug(self.user)
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class CreditTranche(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, verbose_name=_("Użytkownik"))
    credit = models.ForeignKey(
        Credit, on_delete=models.CASCADE, verbose_name=_("Kredyt"))
    tranche_amount = models.DecimalField(
        _("Kwota transzy"),
        max_digits=11, decimal_places=2,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Bez wartości kredytowanych ubezpieczeń. Pole wymagane.")
    )
    tranche_date = models.DateField(
        _("Data wypłaty transzy"),
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane."),
    )
    total_installment = models.DecimalField(
        _("Wysokość raty całkowitej (dla rat stałych)"),
        max_digits=8, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Brak informacji oznacza brak zmiany wysokości raty."),
    )
    capital_installment = models.DecimalField(
        _("Wysokość raty kapitałowej (dla rat malejących)"),
        max_digits=8, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Brak informacji oznacza brak zmiany wysokości raty."),
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.tranche_amount) + " - " + str(self.tranche_date)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    @classmethod
    def total_tranche(cls, queryset):
        total_tranche = 0
        for query in queryset:
            amount = query.tranche_amount
            total_tranche += amount
        return total_tranche

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class CreditInterestRate(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik"))
    credit = models.ForeignKey(
        Credit, on_delete=models.CASCADE, verbose_name=_("Kredyt"))
    interest_rate = models.DecimalField(
        _("Wysokość oprocentowania"),
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Pełna wysokość (z marżą banku i oprocentowaniem "
                    "pomostowym). Pole wymagane.")
    )
    interest_rate_start_date = models.DateField(
        _("Data rozpoczęcia obowiązywania oprocentowania"),
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane.")
    )
    note = models.CharField(
        _("Informacja dodatkowa"), max_length=255, null=True, blank=True)
    total_installment = models.DecimalField(
        _("Wysokość raty całkowitej (dla rat stałych)"),
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Brak informacji oznacza brak zmiany wysokości raty. "
                    "Uwaga: W kredycie o ratach malejących nie można zmieniać "
                    "rat całkowitych.")
    )
    capital_installment = models.DecimalField(
        _("Wysokość raty kapitałowej (dla rat malejących)"),
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Brak informacji oznacza brak zmiany wysokości raty. "
                    "Uwaga: W kredycie o ratach stałych (równych) nie można "
                    "zmieniać rat kapitałowych.")
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.interest_rate) + " - " + str(self.interest_rate_start_date)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class CreditInsurance(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik"))
    credit = models.ForeignKey(
        Credit, on_delete=models.CASCADE, verbose_name=_("Kredyt"))

    type = models.CharField(
        "Rodzaj ubezpieczenia", null=True, blank=True,
        choices=InsuranceType.choices, default=None, max_length=40)
    amount = models.DecimalField(
        _("Wysokość składki"),
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Pole wymagane.")
    )
    frequency = models.CharField(
        _("Częstotliwość płatności"),
        max_length=20, choices=Frequency.choices, default=Frequency.ONE_TIME,
        null=True, blank=True,
    )
    start_date = models.DateField(
        _("Rozpoczęcie płatności"),
        help_text=_("Dla jednorazowych płatności oznacza datę zapłaty. "
                    "Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane."),
    )
    end_date = models.DateField(
        _("Zakończenie płatności"),
        null=True, blank=True,
        help_text=_("Brak daty zakończenia płatności w przypadku braku "
                    "określenia ilości płatności oznacza płatność do całkowitej "
                    "spłaty kredytu. Format: YYYY-MM-DD (np. 2020-07-21)."),
    )
    payment_period = models.PositiveSmallIntegerField(
        _("Liczba okresów płatności"), null=True, blank=True,
        help_text=_("Przez ile okresów będzie dokonywana płatność ubezpieczenia. "
                    "Wpisz, jeśli płatność inna niż jednorazowa."),
    )

    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class CreditCollateral(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik"))
    credit = models.ForeignKey(
        Credit, on_delete=models.CASCADE, verbose_name=_("Kredyt"))
    description = models.CharField(
        _("Nazwa/opis zabezpieczenia"), max_length=255, null=True, blank=True,)
    collateral_value = models.DecimalField(
        _("Wartość zabezpieczenia"),
        max_digits=11, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
    )
    collateral_set_date = models.DateField(
        _("Data ustanowienia zabezpieczenia"),
        help_text=_("Data akceptacji zabezpieczenia przez instytucję finansującą. "
                    "Pole wymagane. Uwaga: Data ustanowienia zabezpieczenia nie "
                    "może przypadać wcześniej niż data rozpoczęcia umowy kredytu. "
                    "Format: YYYY-MM-DD (np. 2020-07-21).")
    )
    total_installment = models.DecimalField(
        _("Wysokość raty całkowitej (dla rat stałych)"),
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Brak informacji oznacza brak zmiany wysokości raty. "
                    "Uwaga: W kredycie o ratach malejących nie można zmieniać "
                    "rat całkowitych.")
    )
    capital_installment = models.DecimalField(
        _("Wysokość raty kapitałowej (dla rat malejących)"),
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Brak informacji oznacza brak zmiany wysokości raty. "
                    "Uwaga: W kredycie o ratach stałych (równych) nie można "
                    "zmieniać rat kapitałowych."),
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.collateral_value) + " - " + str(self.collateral_set_date)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class CreditAdditionalCost(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik"))
    credit = models.ForeignKey(
        Credit, on_delete=models.CASCADE, verbose_name=_("Kredyt"))
    name = models.CharField(
        _("Nazwa"), max_length=255, help_text=_("Pole wymagane."))
    cost_amount = models.DecimalField(
        _("Wysokość kosztu"), max_digits=9, decimal_places=2,
        help_text=_("Pole wymagane. Dopuszczalne wartości ujemne jako korekta "
                    "wcześniejszych kosztów (zwrot).")
    )
    cost_payment_date = models.DateField(
        _("Data płatności"),
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane."))
    notes = models.TextField(_("Uwagi"), max_length=500, blank=True, null=True)
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class CreditEarlyRepayment(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik"))
    credit = models.ForeignKey(
        Credit, on_delete=models.CASCADE, verbose_name=_("Kredyt"))
    repayment_amount = models.DecimalField(
        _("Wartość wcześniejszej spłaty"),
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Pole wymagane.")
    )
    repayment_date = models.DateField(
        _("Data nadpłaty"),
        help_text=_("Pole wymagane. Format: YYYY-MM-DD (np. 2020-07-21).")
    )
    repayment_action = models.CharField(
        _("Efekt nadpłaty"),
        max_length=30,
        choices=RepaymentAction.choices,
        default=RepaymentAction.SHORTER_PAYMENT,
        help_text=_("Pole wymagane."),
    )
    total_installment = models.DecimalField(
        _("Wysokość raty całkowitej (dla rat stałych)"),
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Brak informacji oznacza brak zmiany wysokości raty. "
                    "Uwaga: W kredycie o ratach malejących nie można zmieniać "
                    "rat całkowitych.")
    )
    capital_installment = models.DecimalField(
        _("Wysokość raty kapitałowej (dla rat malejących)"),
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Brak informacji oznacza brak zmiany wysokości raty. "
                    "Uwaga: W kredycie o ratach stałych (równych) nie można "
                    "zmieniać rat kapitałowych."),
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.repayment_amount) + " - " + str(self.repayment_date)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    @classmethod
    def total_repayment(cls, queryset):
        total_repayment = 0
        for query in queryset:
            amount = query.repayment_amount
            total_repayment += amount
        return total_repayment

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
