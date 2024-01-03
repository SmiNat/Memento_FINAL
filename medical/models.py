from __future__ import annotations
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .enums import MedicationFrequency, MedicationDays
from access.enums import Access
from user.handlers import create_slug


class MedCard(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    # In theory, user can have many medcards (for himself, for children etc.),
    # therefore ForeignKey is used, but for the purpose of current Memento app,
    # user can create and use only one medcard (for himself) - coded in forms.py
    # and in templates (only one card to create and being visible in app).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    name = models.CharField(_("Nazwa"), max_length=255, null=True, blank=True)
    slug = models.SlugField(null=False, unique=True)
    age = models.PositiveSmallIntegerField(_("Wiek"), null=True, blank=True,)
    weight = models.PositiveSmallIntegerField(_("Waga"), null=True, blank=True,)
    height = models.PositiveSmallIntegerField(_("Wzrost"), null=True, blank=True,)
    blood_type = models.CharField(
        _("Grupa krwi"), max_length=10, null=True, blank=True
    )
    allergies = models.TextField(
        _("Alergie"), max_length=500, null=True, blank=True,
    )
    diseases = models.TextField(
        _("Choroby"), max_length=500, null=True, blank=True,
    )
    permanent_medications = models.TextField(
        _("Stałe leki"), max_length=500, null=True, blank=True,
    )
    additional_medications = models.TextField(
        _("Leki dodatkowe"), max_length=500, null=True, blank=True,
    )
    main_doctor = models.CharField(
        _("Lekarz prowadzący"), max_length=255,  null=True, blank=True,
    )
    other_doctors = models.TextField(
        _("Pozostali lekarze"), max_length=500, null=True, blank=True,
    )
    emergency_contact = models.TextField(
        _("Osoba do kontaktu"), max_length=500,  null=True, blank=True,
    )
    notes = models.TextField(
        _("Uwagi"), max_length=500,  null=True, blank=True,
    )
    access_granted = models.CharField(
        _("Dostęp do karty medycznej"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać kartę medyczną.")
    )
    access_granted_medicines = models.CharField(
        _("Dostęp do danych o lekach"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać listę leków.")
    )
    access_granted_visits = models.CharField(
        _("Dostęp do wizyt lekarskich"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać wizyty lekarskie.")
    )
    access_granted_test_results = models.CharField(
        _("Dostęp do wyników badań"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać wyniki badań.")
    )

    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_medcard_name")
            ]

    def __str__(self):
        return str(_("Karta medyczna"))

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def clean(self):
        if self.access_granted not in Access.values:
            raise ValidationError(_("Błędna wartość pola 'Dostęp do karty medycznej' (%s). "
                                    "Sprawdź czy polskie znaki nie zostały zastąpione "
                                    "innymi znakami." % self.access_granted))
        if self.access_granted_medicines not in Access.values:
            raise ValidationError(_("Błędna wartość pola 'Dostęp do danych o lekach' (%s). "
                                    "Sprawdź czy polskie znaki nie zostały zastąpione "
                                    "innymi znakami." % self.access_granted_medicines))
        if self.access_granted_visits not in Access.values:
            raise ValidationError(_("Błędna wartość pola 'Dostęp do wizyt lekarskich' (%s). "
                                    "Sprawdź czy polskie znaki nie zostały zastąpione "
                                    "innymi znakami." % self.access_granted_visits))
        if self.access_granted_test_results not in Access.values:
            raise ValidationError(_("Błędna wartość pola 'Dostęp do wyników badań' (%s). "
                                    "Sprawdź czy polskie znaki nie zostały zastąpione "
                                    "innymi znakami." % self.access_granted_test_results))

    def save(self, *args, **kwargs):
        slugs = MedCard.objects.all().exclude(id=self.id).values_list(
            "slug", flat=True)
        if not self.slug:
            self.slug = create_slug(self.user)
        while self.slug in slugs:
            self.slug = create_slug(self.user)
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


def med_hours():
    med_hours_list_tuple = list((f"{x}:00", f"{x}:30") for x in range(0, 24))
    med_hours_list = list(element for tup in med_hours_list_tuple for element in tup)
    med_hours = tuple((x, x) for x in med_hours_list)
    return med_hours


class Medicine(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    drug_name_and_dose = models.CharField(
        _("Nazwa leku i dawka"), max_length=255,
        help_text=_("Pole wymagane.")
    )
    daily_quantity = models.DecimalField(
        _("Ilość dawek dziennie"), max_digits=4, decimal_places=1,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
        help_text=_("Pole wymagane."),
    )
    medication_days = models.CharField(
        _("Dni przyjmowania leków"),
        # choices=MedicationDays.choices,
        max_length=255,
        null=True, blank=True,
        help_text=_("Uzupełnij, jeśli leki przyjmowane są w konkretne dni tygodnia.")
    )
    medication_frequency = models.CharField(
        _("Częstotliwość przyjmowania leków"),
        choices=MedicationFrequency.choices, max_length=255,
        null=True, blank=True,
    )
    exact_frequency = models.CharField(
        _("Co ile dni przyjmowane są leki"), max_length=255,
        null=True, blank=True,
        help_text=_("Uzupełnij, jeśli wskazano jako częstotliwość "
                    "'Co kilka dni' lub 'Inne'.")
    )
    medication_hours = models.CharField(
        _("Godziny przyjmowania leków"),
        # choices=med_hours(),
        max_length=255,
        null=True, blank=True,
    )
    start_date = models.DateField(
        _("Rozpoczęcie przyjmowania leku"), null=True, blank=True,
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21).")
    )
    end_date = models.DateField(
        _("Zakończenie przyjmowania leku"), null=True, blank=True,
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21).")
    )
    disease = models.CharField(
        _("Leczona choroba/dolegliwość"), max_length=255,
        null=True, blank=True,
    )
    notes = models.TextField(
        _("Uwagi"), max_length=500, null=True, blank=True,)
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "drug_name_and_dose"], name="unique_drug_name"
            )
        ]

    def __str__(self):
        return str(self.drug_name_and_dose)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def medication_days_to_list(self):
        """Return field value as a list."""
        if not self.medication_days:
            return []
        return self.medication_days.split(",")

    def medication_hours_to_list(self):
        """Return field value as a list."""
        if not self.medication_hours:
            return []
        return self.medication_hours.split(",")

    # No need to use clean method for medication_days field due to clean_medication_days method in forms.py
    # def clean(self):
    #     """Converts data from MultipleChoiceField in forms to plain string with comma
    #     separated values for CharField in model."""
    #     if self.medication_days == [] or self.medication_days =="[]":
    #         self.medication_days = None
    #     elif self.medication_days:
    #         no_brackets = self.medication_days.replace("[", "").replace("]", "")
    #         no_quotation = no_brackets.replace("\"", "").replace("'", "")
    #         no_free_spaces = no_quotation.replace(" ", "")
    #         self.medication_days = no_free_spaces

    def save(self, *args, **kwargs):
        """In case save method will drop polish letters (eg. during dumping and loading
        database as json file) - model will verify if selected chioices are the same as
        those available for specific field."""
        if self.medication_frequency and self.medication_frequency not in MedicationFrequency.values:
            raise ValidationError(_("Błędna wartość pola 'Częstotliwość przyjmowania leków' (%s). "
                                    "Sprawdź czy polskie znaki nie zostały zastąpione "
                                    "innymi znakami." % self.medication_frequency))
        if self.medication_days:
            if not all(element in MedicationDays.values for element in self.medication_days_to_list()):
                raise ValidationError(
                    _("Błędna wartość pola 'Dni przyjmowania leków' (%s). "
                      "Sprawdź czy polskie znaki nie zostały zastąpione innymi znakami."
                      % self.medication_days))
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class MedicalVisit(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    specialization = models.CharField(
        _("Specjalizacja"), max_length=255,
        help_text=_("Pole wymagane.")
    )
    doctor = models.CharField(
        _("Lekarz"), max_length=255,
        blank=True, null=True,
    )
    visit_date = models.DateField(
        _("Dzień wizyty"),
        help_text=_("Pole wymagane. Format: YYYY-MM-DD (np. 2020-07-21)."),
    )
    visit_time = models.TimeField(_("Godzina wizyty"), help_text=_("Pole wymagane."))
    visit_location = models.CharField(
        _("Lokalizacja wizyty"), max_length=255,
        null=True, blank=True,
    )
    notes = models.TextField(
        _("Uwagi"), max_length=500,
        blank=True, null=True,
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.specialization) + " - " + str(self.visit_date)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "specialization", "visit_date", "visit_time"],
                name="unique_specialization_visit_date_time",
            )
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class HealthTestResult(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    name = models.CharField(
        _("Nazwa"), max_length=255, help_text=_("Pole wymagane.")
    )
    test_result = models.TextField(
        _("Wynik badania"), max_length=500, help_text=_("Pole wymagane.")
    )
    test_date = models.DateField(
        _("Data badania"),
        help_text=_("Pole wymagane. Format: YYYY-MM-DD (np. 2020-07-21)."),
    )
    disease = models.CharField(
        _("Leczona choroba/dolegliwość"), max_length=255,
        null=True, blank=True,
    )
    notes = models.TextField(_("Uwagi"), max_length=500, null=True, blank=True,)
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name", "test_date"],
                name="unique_test_name_date"
            )
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
