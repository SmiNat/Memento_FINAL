import datetime

from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from access.enums import Access
from user.factories import UserFactory
from user.handlers import create_slug
from .enums import MedicationDays, MedicationFrequency
from .models import MedCard, Medicine, MedicalVisit, HealthTestResult


class MedCardFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    slug = create_slug()
    age = 22
    weight = 66
    height = 170
    blood_type = "B+"
    allergies = "Cat, peanuts, dust"
    diseases = "Asthma, hypertension"
    permanent_medications = "Sybmicort, clatra"
    additional_medications = "Vit. D, magnesium"
    main_doctor = "Dr Who"
    other_doctors = Faker("text", max_nb_chars=10)
    emergency_contact = Faker("text", max_nb_chars=10)
    notes = Faker("text", max_nb_chars=10)
    access_granted = Access.NO_ACCESS_GRANTED
    access_granted_medicines = Access.NO_ACCESS_GRANTED
    access_granted_test_results = Access.NO_ACCESS_GRANTED
    access_granted_visits = Access.NO_ACCESS_GRANTED
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = MedCard


class MedicineFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    drug_name_and_dose = "Symbicort 160"
    daily_quantity = 1
    medication_days = "Poniedziałek,Środa,Czwartek,Sobota"
    medication_frequency = MedicationFrequency.EVERY_DAY
    exact_frequency = Faker("text", max_nb_chars=10)
    medication_hours = "8:00,20:00"
    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2021, 1, 1)
    disease = "Asthma"
    notes = "double dose if necessary"
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = Medicine


class MedicalVisitFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    specialization = "dermatologist"
    doctor = "Dr House"
    visit_date = datetime.date(2020, 10, 10)
    visit_time = "9:20"
    visit_location = "St. Peter Hospital"
    notes = ""
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = MedicalVisit


class HealthTestResultFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    name = "Blood test"
    test_result = "Not good"
    test_date = datetime.date(2020, 11, 11)
    disease = "anemia"
    notes = "need to make additional tests"
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = HealthTestResult
