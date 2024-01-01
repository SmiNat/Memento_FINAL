import datetime

from factory.django import DjangoModelFactory
from factory import Faker, SubFactory

from access.enums import Access
from user.factories import UserFactory
from .enums import (TripChoices, BasicChecklist, KeysChecklist,
                    CosmeticsChecklist, ElectronicsChecklist,
                    UsefulStaffChecklist, TrekkingChecklist, HikingChecklist,
                    CyclingChecklist, CampingChecklist, FishingChecklist,
                    SunbathingChecklist, BusinessChecklist, CostGroup)
from .models import (Trip, TripReport, TripBasicChecklist,
                     TripAdvancedChecklist, TripAdditionalInfo,
                     TripPersonalChecklist, TripCost)


class TripFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    name = "Test name"
    type = ["Wyjazd pod namiot"]
    destination = "Test place"
    start_date = datetime.date(2020, 10, 10)
    end_date = datetime.date(2020, 10, 18)
    transport = "car"
    estimated_cost = 1000
    participants_number = 4
    participants = Faker("sentence", nb_words=4)
    reservations = Faker("sentence", nb_words=6)
    notes = Faker("text", max_nb_chars=10)
    access_granted = Access.NO_ACCESS_GRANTED
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = Trip


class TripReportFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    trip = SubFactory(TripFactory)
    start_date = datetime.date(2020, 10, 10)
    end_date = datetime.date(2020, 10, 13)
    description = "Cool trip"
    notes = Faker("text", max_nb_chars=10)
    facebook = Faker("url")
    youtube = "https://www.youtube.com"
    instagram = Faker("url")
    pinterest = Faker("url")
    link = Faker("url")
    created = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)

    class Meta:
        model = TripReport


class TripBasicFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    trip = SubFactory(TripFactory)
    name = "Basic trip"
    wallet = ["Paszport"]
    keys = ["Samochód", "Bagażnik"]
    cosmetics = ["Szczotka do zębów", "Pasta do zębów"]
    electronics = ["Słuchawki", "Podkładka pod laptop"]
    useful_stuff = ["Parasol"]
    basic_drugs = "cynk; wit. B i żelazo"
    additional_drugs = "Wit. C, magnez, espumisan"
    created = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)

    class Meta:
        model = TripBasicChecklist


class TripAdvancedFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    trip = SubFactory(TripFactory)
    name = "Advanced trip"
    trekking = ["Mapy", "Czołówka"]
    hiking = ["Czekan", "Worek na magnezję"]
    cycling = ["Kask"]
    camping = ["Gaz", "Spork", "Kubek"]
    fishing = []
    sunbathing = ["Klapki"]
    business = ["Dokumenty", "Karty dostępu"]
    created = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)

    class Meta:
        model = TripAdvancedChecklist


class TripPersonalChecklistFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    trip = SubFactory(TripFactory)
    name = "Personal checklist"
    checklist = "Item 1, item 2, item3; item 4"
    created = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)

    class Meta:
        model = TripPersonalChecklist


class TripAdditionalInfoFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    trip = SubFactory(TripFactory)
    name = "Additional info"
    info = Faker("sentence", nb_words=6)
    notes = Faker("sentence", nb_words=6)
    created = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)

    class Meta:
        model = TripAdditionalInfo


class TripCostFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    trip = SubFactory(TripFactory)
    name = "Cost name"
    cost_group = "Paliwo"
    cost_paid = 111.11
    currency = "EUR"
    exchange_rate = 4.5432
    notes = Faker("sentence", nb_words=6)
    created = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)

    class Meta:
        model = TripCost
