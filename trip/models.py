from __future__ import annotations
import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _

from .enums import (
    # TripChoices,
    # BasicChecklist,
    # KeysChecklist,
    # CosmeticsChecklist,
    # ElectronicsChecklist,
    # UsefulStaffChecklist,
    # TrekkingChecklist,
    # HikingChecklist,
    # CyclingChecklist,
    # CampingChecklist,
    # FishingChecklist,
    # SunbathingChecklist,
    # BusinessChecklist,
    # HospitalChecklist,
    CostGroup,
)
from access.enums import Access


class Trip(models.Model):

    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    name = models.CharField(
        _("Nazwa podróży"), max_length=255,
        help_text=_("Pole wymagane.")
    )
    type = models.CharField(
        _("Rodzaj podróży"),
        # choices=TripChoices.choices,
        max_length=255,
        null=True, blank=True
    )
    destination = models.CharField(
        _("Miejsce podróży"), max_length=255,
        null=True, blank=True,
    )
    start_date = models.DateField(
        _("Rozpoczęcie wyjazdu"),
        null=True, blank=True,
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21)."),
    )
    end_date = models.DateField(
        _("Zakończenie wyjazdu"),
        null=True, blank=True,
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21)."),
    )
    transport = models.CharField(
        _("Środki transportu"), max_length=255,
        null=True, blank=True,
    )
    estimated_cost = models.PositiveIntegerField(
        _("Szacunkowy koszt podróży"), null=True, blank=True
    )
    participants_number = models.PositiveSmallIntegerField(
        _("Liczba osób na wyjeździe"), null=True, blank=True, default=1
    )
    participants = models.CharField(
        _("Towarzysze podróży"), max_length=255,
        null=True, blank=True,
    )
    reservations = models.TextField(
        _("Informacje o rezerwacjach"), max_length=255,
        null=True, blank=True,
    )
    notes = models.TextField(
        _("Uwagi"), max_length=500,
        null=True, blank=True,
    )
    access_granted = models.CharField(
        _("Dostęp do danych"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_(
            "Użytkownik upoważniony do dostępu do danych może przeglądać te dane."
        )
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"], name="unique_trip_name"
            )
        ]

    @classmethod
    def field_names(cls) -> list:
        """Return list of model field names (except for many-to-many fields)."""
        return list(f.name for f in cls._meta.fields)

    def __str__(self):
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def type_to_list(self):
        """Return trip types as a list."""
        if not self.type:
            return []
        return self.type.split(",")

    def trip_days(self) -> int | None:
        """
        Return number of trip days.
        If start date and end date are the same, trip days equals one.
        If start date and end date are different, both start and end date
        are calculated to overall number of trip days.
        """
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        else:
            return None

    def get_all_costs_pln(self) -> float | None:
        """
        Return sum of all costs in domestic currency
        for TripCost queryset calculated on given Trip instance.
        """
        sum_of_costs_in_domestic_currency = 0
        queryset = self.tripcost_set.filter(trip=self.id)
        if queryset:
            for trip_cost in queryset:
                cost_in_domestic_currency = (
                        float(trip_cost.cost_paid) * float(trip_cost.exchange_rate)
                )
                sum_of_costs_in_domestic_currency += cost_in_domestic_currency
            return round(sum_of_costs_in_domestic_currency)
        else:
            return None

    def clean(self):
        if self.access_granted not in Access.values:
            raise ValidationError(_("Błędna wartość pola 'Dostęp do danych' (%s). Sprawdź czy "
                                    "polskie znaki nie zostały zastąpione innymi znakami."
                                    % self.access_granted))

    def save(self, *args, **kwargs):
        if not self.name:
            raise IntegrityError("Field 'name' is required.")
        self.full_clean()
        super().save(*args, **kwargs)

###############################################################################


class TripReport(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, verbose_name=_("Wyjazd")
    )
    start_date = models.DateField(
        _("Rozpoczęcie relacji"),
        null=True, blank=True,
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21)."),
    )
    end_date = models.DateField(
        _("Zakończenie relacji"),
        null=True, blank=True,
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21)."),
    )
    description = models.TextField(
        _("Opis"), max_length=500,
        null=True, blank=True,
    )
    notes = models.TextField(
        _("Uwagi"), max_length=500,
        null=True, blank=True,
    )
    facebook = models.URLField(_("Facebook link"), null=True, blank=True)
    youtube = models.URLField(_("Youtube link"), null=True, blank=True)
    instagram = models.URLField(_("Instagram link"), null=True, blank=True)
    pinterest = models.URLField(_("Pinterest link"), null=True, blank=True)
    link = models.URLField(_("Link do relacji"), null=True, blank=True)
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

###############################################################################


class TripBasicChecklist(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, verbose_name=_("Wyjazd")
    )
    name = models.CharField(
        _("Nazwa"), max_length=255,
        null=True, blank=True,
    )
    wallet = models.CharField(
        _("Portfel"), max_length=500,
        # choices=BasicChecklist.choices,
        null=True, blank=True,
    )
    keys = models.CharField(
        _("Klucze"),
        # choices=KeysChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    cosmetics = models.CharField(
        _("Kosmetyki"),
        # choices=CosmeticsChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    electronics = models.CharField(
        _("Elektronika"),
        # choices=ElectronicsChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    useful_stuff = models.CharField(
        _("Użyteczne rzeczy"),
        # choices=UsefulStaffChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    basic_drugs = models.TextField(
        _("Podstawowe leki"), max_length=500,
        null=True, blank=True,
    )
    additional_drugs = models.TextField(
        _("Dodatkowe leki"), max_length=500,
        null=True, blank=True,
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "trip", "name"],
                name="unique_trip_basic_name"
            )
        ]

    def __str__(self):
        trip = self.trip.name
        if self.name:
            return str(trip) + " - " + str(self.name)
        return str(trip) + " (basic)"

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def wallet_to_list(self):
        """Return field value as a list."""
        if not self.wallet:
            return []
        return self.wallet.split(",")

    def keys_to_list(self):
        """Return field value as a list."""
        if not self.keys:
            return []
        return self.keys.split(",")

    def cosmetics_to_list(self):
        """Return field value as a list."""
        if not self.cosmetics:
            return []
        return self.cosmetics.split(",")

    def electronics_to_list(self):
        """Return field value as a list."""
        if not self.electronics:
            return []
        return self.electronics.split(",")

    def useful_stuff_to_list(self):
        """Return field value as a list."""
        if not self.useful_stuff:
            return []
        return self.useful_stuff.split(",")

    def basic_drugs_to_list(self) -> list:
        """Transfers string into list based on comma or semicolon separator.
        In case of empty string or string equal to 'None', returns empty list."""
        if self.basic_drugs is None or self.basic_drugs == "None":
            return []
        return str(self.basic_drugs).replace(";", ",").replace(", ", ",").split(",")

    def additional_drugs_to_list(self) -> list:
        """Transfers string into list based on comma or semicolon separator.
        In case of empty string or string equal to 'None', returns empty list."""
        if self.additional_drugs is None or self.additional_drugs == "None":
            return []
        return str(self.additional_drugs).replace(";", ",").replace(", ", ",").split(",")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


###############################################################################


class TripAdvancedChecklist(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, verbose_name=_("Wyjazd")
    )
    name = models.CharField(
        _("Nazwa"), max_length=255,
        null=True, blank=True,
    )
    trekking = models.CharField(
        _("Trekking"),
        # choices=TrekkingChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    hiking = models.CharField(
        _("Wspinaczka"),
        # choices=HikingChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    cycling = models.CharField(
        _("Rower"),
        # choices=CyclingChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    camping = models.CharField(
        _("Camping"),
        # choices=CampingChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    fishing = models.CharField(
        _("Wędkarstwo"),
        # choices=FishingChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    sunbathing = models.CharField(
        _("Plażowanie"),
        # choices=SunbathingChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    business = models.CharField(
        _("Wyjazd służbowy"),
        # choices=BusinessChecklist.choices,
        max_length=500, null=True, blank=True,
    )
    hospital = models.CharField(_("Szpital"), max_length=500, null=True, blank=True,)
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "trip", "name"],
                name="unique_trip_advanced_name"
            )
        ]

    def __str__(self):
        trip = self.trip.name
        if self.name:
            return str(trip) + " - " + str(self.name)
        return str(trip) + " (advanced)"

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def trekking_to_list(self):
        """Return field values as a list."""
        if not self.trekking:
            return []
        return self.trekking.split(",")

    def hiking_to_list(self):
        """Return field values as a list."""
        if not self.hiking:
            return []
        return self.hiking.split(",")

    def cycling_to_list(self):
        """Return field values as a list."""
        if not self.cycling:
            return []
        return self.cycling.split(",")

    def camping_to_list(self):
        """Return field values as a list."""
        if not self.camping:
            return []
        return self.camping.split(",")

    def fishing_to_list(self):
        """Return field values as a list."""
        if not self.fishing:
            return []
        return self.fishing.split(",")

    def sunbathing_to_list(self):
        """Return field values as a list."""
        if not self.sunbathing:
            return []
        return self.sunbathing.split(",")

    def business_to_list(self):
        """Return field values as a list."""
        if not self.business:
            return []
        return self.business.split(",")

    def hospital_to_list(self):
        """Return field values as a list."""
        if not self.hospital:
            return []
        return self.hospital.split(",")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

###############################################################################


class TripPersonalChecklist(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, verbose_name=_("Wyjazd")
    )
    name = models.CharField(
        _("Nazwa"), max_length=255,
        help_text=_("Pole wymagane."),
    )
    checklist = models.TextField(
        _("Lista"), max_length=500, null=True, blank=True,
        help_text="Elementy listy oddzielaj przecinkami lub średnikami."
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "trip", "name"],
                name="unique_trip_checklist_name"
            )
        ]

    def __str__(self):
        trip = self.trip.name
        return str(trip) + " - " + str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def checklist_to_list(self) -> list:
        """Transfers string into list based on comma or semicolon separator.
        In case of empty string or string equal to 'None', returns empty list."""
        if self.checklist is None or self.checklist == "None":
            return []
        return str(self.checklist).replace("; ", ",").replace(";", ",").replace(", ", ",").split(",")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


###############################################################################


class TripAdditionalInfo(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, verbose_name=_("Wyjazd")
    )
    name = models.CharField(
        _("Nazwa"),  max_length=255,
        help_text=_("Pole wymagane.")
    )
    info = models.CharField(
        _("Opis"), max_length=500,
        null=True, blank=True,
    )
    notes = models.TextField(
        _("Uwagi"), max_length=500,
        null=True, blank=True,
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "trip", "name"],
                name="unique_trip_additional_name"
            )
        ]

    def __str__(self):
        trip = self.trip.name
        return str(trip) + " - " + str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

###############################################################################


class TripCost(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, verbose_name=_("Wyjazd")
    )
    name = models.CharField(
        _("Nazwa"), max_length=255,
        help_text=_("Pole wymagane.")
    )
    cost_group = models.CharField(
        _("Grupa kosztów"), max_length=100, choices=CostGroup.choices,
        help_text=_("Pole wymagane.")
    )
    cost_paid = models.FloatField(
        _("Wysokość wydatku"), max_length=10,
        help_text=_("Pole wymagane.")
    )
    currency = models.CharField(
        _("Waluta"), max_length=20, default="PLN",
        null=True, blank=True,
    )
    exchange_rate = models.FloatField(
        _("Kurs wymiany waluty"), max_length=8, default=1.0000,
        validators=[MinValueValidator(0,
                                      message="Wartość nie może być liczbą ujemną.")],
        help_text=_("Pole wymagane.")
    )
    notes = models.TextField(
        _("Uwagi"), max_length=500,
        null=True, blank=True,
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        trip = self.trip.name
        return str(trip) + " - " + str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def calculate_cost_at_exchange_rate(self) -> float:
        """Return single cost in domestic currency."""
        cost_in_domestic_currency = (
                float(self.cost_paid) * float(self.exchange_rate)
        )
        return round(cost_in_domestic_currency, 2)

    def sum_of_trip_costs(self, queryset=None) -> float:
        """
        Return sum of all trip costs converted to domestic currency.
        Parameters:
        ----------
        queryset:
            queryset of TripCost model instances
            If queryset is None, default queryset equals to
            TripCost.objects.filter(trip=self.trip)
        """
        cost_total = 0
        if not queryset:
            trip_queryset = TripCost.objects.filter(trip=self.trip)
        else:
            trip_queryset = queryset
        for query in trip_queryset:
            cost = query.calculate_cost_at_exchange_rate()
            cost_total += cost
        return round(cost_total, 2)

    def trip_duration(self, start_date=None, end_date=None) -> int:
        """
        Return number of trip days based on start and end date.
        If start date and end date are the same, trip days equals one.
        If start date and end date are different, both start and end date
        are calculated to overall number of trip days.
        Parameters:
        ----------
        start_date (datetime.date):
            If start_date is None, default start_date equals to
            Trip.objects.filter(name=self.trip).start_date
        end_date (datetime.date):
            If end_date is None, default start_date equals to
            Trip.objects.filter(name=self.trip).end_date
        """
        if not start_date:
            start = Trip.objects.get(name=self.trip).start_date
        else:
            start = start_date
        if not end_date:
            end = Trip.objects.get(name=self.trip).end_date
        else:
            end = end_date
        delta = (end - start)
        return delta.days + 1

    def cost_per_person(self, queryset=None, participants=None) -> str | float:
        """
        Return cost per person converted to domestic currency.
        Parameters:
        ----------
        queryset:
            queryset of TripCost model instances
            If queryset is None, default queryset equals to
            TripCost.objects.filter(trip=self.trip)
        participants (int):
            number of trip participants
            If participants is None, number of trip participants equals to
            Trip.objects.get(name=self.trip).participants_number
        """
        if not participants:
            number_of_people = Trip.objects.get(
                name=self.trip).participants_number
        else:
            number_of_people = participants
        if number_of_people == 0:
            return "N/A"
        if not queryset:
            trip_queryset = TripCost.objects.filter(trip=self.trip)
        else:
            trip_queryset = queryset
        cost_per_person = self.sum_of_trip_costs(trip_queryset) / number_of_people
        return round(cost_per_person, 2)

    def cost_per_day(self, queryset=None, start_date=None, end_date=None) -> float:
        """
        Return cost per day converted to domestic currency.
        Parameters:
        ----------
        queryset:
            queryset of TripCost model instances
            If queryset is None, default queryset equals to
            TripCost.objects.filter(trip=self.trip)
        start_date (datetime.date):
            If start_date is None, default start_date equals to
            Trip.objects.filter(name=self.trip).start_date
        end_date (datetime.date):
            If end_date is None, default start_date equals to
            Trip.objects.filter(name=self.trip).end_date
        """
        delta = self.trip_duration(start_date=start_date, end_date=end_date)
        if not queryset:
            trip_queryset = TripCost.objects.filter(trip=self.trip)
        else:
            trip_queryset = queryset
        cost_per_day = float(self.sum_of_trip_costs(trip_queryset)) / delta
        return round(cost_per_day, 2)

    def cost_per_person_per_day(
            self, queryset=None, start_date=None, end_date=None, participants=None
    ) -> float | str:
        """
        Return cost per day per person converted to domestic currency.
        Parameters:
        ----------
        queryset:
            queryset of TripCost model instances
            If queryset is None, default queryset equals to
            TripCost.objects.filter(trip=self.trip)
        start_date (datetime.date):
            If start_date is None, default start_date equals to
            Trip.objects.filter(name=self.trip).start_date
        end_date (datetime.date):
            If end_date is None, default start_date equals to
            Trip.objects.filter(name=self.trip).end_date
        participants (int):
            number of trip participants
            If participants is None, number of trip participants equals to
            Trip.objects.get(name=self.trip).participants_number
        """
        delta = self.trip_duration(start_date=start_date, end_date=end_date)
        cost_per_day = float(self.sum_of_trip_costs(queryset)) / delta
        if not participants:
            number_of_people = Trip.objects.get(
                name=self.trip).participants_number
        else:
            number_of_people = participants
        if number_of_people == 0:
            return "N/A"
        cost_per_person_per_day = cost_per_day / number_of_people
        return round(cost_per_person_per_day, 2)

    def clean(self):
        if self.cost_group not in CostGroup.values:
            raise ValidationError(_("Błędna wartość pola 'Grupa kosztów' (%s). Sprawdź czy "
                                    "polskie znaki nie zostały zastąpione innymi znakami."
                                    % self.cost_group))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
