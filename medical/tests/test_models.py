import datetime
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from parameterized import parameterized

from medical.models import MedCard, Medicine, MedicalVisit, HealthTestResult
from medical.factories import (MedCardFactory, MedicineFactory,
                               MedicalVisitFactory, HealthTestResultFactory)
from user.handlers import create_slug, is_memento_slug_correct

User = get_user_model()


class MedCardTests(TestCase):
    """Test MedCard Model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456"
        )
        self.user2 = User.objects.create_user(
            username="new_user_test",
            email="new_test@example.com",
            password="testpass456"
        )
        self.medcard = MedCard.objects.create(
            user=self.user, name="my medcard", slug="johndoe123_slug",
        )
        self.medcard2 = MedCard.objects.create(
            user=self.user2, name="child medcard", slug="new_user_test_slug",
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "name": "Nazwa",
            "slug": "slug",
            "age": "Wiek",
            "weight": "Waga",
            "height": "Wzrost",
            "blood_type": "Grupa krwi",
            "allergies": "Alergie",
            "diseases": "Choroby",
            "permanent_medications": "Stałe leki",
            "additional_medications": "Leki dodatkowe",
            "main_doctor": "Lekarz prowadzący",
            "other_doctors": "Pozostali lekarze",
            "emergency_contact": "Osoba do kontaktu",
            "notes": "Uwagi",
            "access_granted": "Dostęp do karty medycznej",
            "access_granted_medicines": "Dostęp do danych o lekach",
            "access_granted_visits": "Dostęp do wizyt lekarskich",
            "access_granted_test_results": "Dostęp do wyników badań",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }

    def test_create_medcard_successful(self):
        """Test if creating payment instance with valid data is successful."""
        medcard = MedCard.objects.all()
        self.assertEqual(medcard.count(), 2)
        self.assertTrue(medcard[0].user, self.user)
        self.assertTrue(medcard[1].user, self.user2)
        self.assertTrue(medcard[0].slug, self.medcard.slug)
        self.assertTrue(medcard[1].slug, self.medcard2.slug)

    def test_unique_constraint_for_medcard_name(self):
        """Test if user can only have medcard with unique names."""

        # Unique together (only unique name fields for single user)
        with self.assertRaises(ValidationError):
            MedCard.objects.create(
                user=self.medcard.user, name=self.medcard.name
            )

        # Different users can have the same field name
        MedCard.objects.create(user=self.medcard2.user, name=self.medcard.name)
        self.assertEqual(MedCard.objects.count(), 3)

    def test_medcard_id_is_uuid(self):
        """Test if id is represented as uuid"""
        self.assertTrue(isinstance(self.medcard.id, uuid.UUID))
        self.assertEqual(self.medcard.id, uuid.UUID(str(self.medcard.id)))

    def test_field_is_not_none(self):
        """Test if creating an instance without required fields
        raises ValidationError or self.RelatedObjectDoesNotExist."""

        # MedCard without user field
        with self.assertRaises(Exception):
            MedCard.objects.create(notes="test",)

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.medcard), "Karta medyczna")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        all_fields = list(self.field_names.values())
        all_values = list(self.medcard.__dict__.values())
        for field, value in self.medcard:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                self.assertEqual(value, str(all_values[number][0]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            elif all_values[number]:
                self.assertEqual(value, str(all_values[number]))

    def test_validate_choices(self):
        """Test if clean method validates choices before saving instance in database."""
        # test correct access_granted
        self.medcard.access_granted = "Brak dostępu"
        self.medcard.save()
        self.assertEqual(self.medcard.access_granted, "Brak dostępu")
        # test correct access_granted_medicines
        self.medcard.access_granted_medicines = "Brak dostępu"
        self.medcard.save()
        self.assertEqual(self.medcard.access_granted_medicines, "Brak dostępu")
        # test correct access_granted_visits
        self.medcard.access_granted_visits = "Brak dostępu"
        self.medcard.save()
        self.assertEqual(self.medcard.access_granted_visits, "Brak dostępu")
        # test correct access_granted_test_results
        self.medcard.access_granted_test_results = "Brak dostępu"
        self.medcard.save()
        self.assertEqual(self.medcard.access_granted_test_results, "Brak dostępu")

        # test incorrect access_granted
        self.medcard.access_granted = "Brak"
        with self.assertRaises(ValidationError):
            self.medcard.save()
        # test incorrect access_granted_medicines
        self.medcard.access_granted_medicines = ["Brak"]
        with self.assertRaises(ValidationError):
            self.medcard.save()
        # test incorrect access_granted_visits
        self.medcard.access_granted_visits = "Brak"
        with self.assertRaises(ValidationError):
            self.medcard.save()
        # test incorrect access_granted_test_results
        self.medcard.access_granted_test_results = "Brak"
        with self.assertRaises(ValidationError):
            self.medcard.save()

    @parameterized.expand(
        [
            ("Real user instance", {"username": MedCardFactory.user},),
            ("Latin characters in username",
             {"username": "śśżżźźććąąłłóóęęńńŚŚĆĆĄĄŻŻŹŹŃŃŁŁÓÓĘĘ"}),
            ("Forbidden characters in username",
             {"username": "!!@@##$%%^^&&**(())<<>>??..,,++==[[]]{{}}::;;''||\\\"\"\\"}),
        ]
    )
    def test_slug_field_with_no_forbidden_characters(self, name, username):
        """
        Test if save method creates correct string for slug field.
        Allowed characters for slug field:
            Unicode alphabet letters (a-z) and (A-Z)
            Numbers (0-9)
            Hyphens and underscore
        Maximal length of slug: 50 characters.
        """
        slug = create_slug(username)
        self.assertTrue(is_memento_slug_correct(slug))

    def test_unique_slug_field(self):
        """
        Test if there can only be unique field slug for model (for all users).
        """
        slug_test = "test_slug_for_users"
        med = MedCard.objects.create(user=self.medcard.user, slug=slug_test)
        med1 = MedCard.objects.create(user=self.medcard.user, slug=slug_test)
        med2 = MedCard.objects.create(user=self.medcard2.user, slug=slug_test)
        self.assertEqual(slug_test, med.slug)
        self.assertNotEqual(slug_test, med1.slug)
        self.assertNotEqual(slug_test, med2.slug)


class MedicineTests(TestCase):
    """Test model Medicine."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser123",
            email="test123@example.com",
            password="testpass456"
        )
        self.medicine = MedicineFactory(user=self.user)
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "drug_name_and_dose": "Nazwa leku i dawka",
            "daily_quantity": "Ilość dawek dziennie",
            "medication_days": "Dni przyjmowania leków",
            "medication_frequency": "Częstotliwość przyjmowania leków",
            "exact_frequency": "Co ile dni przyjmowane są leki",
            "medication_hours": "Godziny przyjmowania leków",
            "start_date": "Rozpoczęcie przyjmowania leku",
            "end_date": "Zakończenie przyjmowania leku",
            "disease": "Leczona choroba/dolegliwość",
            "notes": "Uwagi",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }

    def test_create_medicine_successful(self):
        """Test if creating a medicine with valid data is successful."""
        medicines = Medicine.objects.all()
        self.assertEqual(medicines.count(), 1)
        self.assertTrue(medicines[0].user, self.user)
        self.assertTrue(medicines[0].drug_name_and_dose, "Symbicort 160")

    def test_medicine_id_is_uuid(self):
        """Test if id is represented as uuid."""
        self.assertTrue(isinstance(self.medicine.id, uuid.UUID))
        self.assertEqual(self.medicine.id, uuid.UUID(str(self.medicine.id)))

    def test_unique_constraint_for_drug_name_and_dose_field(self):
        """Test if user can only have drug_name_and_dose field
        with unique string."""

        # The same user cannot have two the same fields for drug_name_and_dose
        Medicine.objects.create(
            user=self.user, daily_quantity=1, drug_name_and_dose="Med 123"
        )
        self.assertEqual(Medicine.objects.count(), 2)
        with self.assertRaises(ValidationError):
            Medicine.objects.create(
                user=self.user, daily_quantity=1, drug_name_and_dose="Med 123"
            )
        # Different user can have the same field drug_name_and_dose as other user
        new_user = User.objects.create_user(
            username="newuser123",
            email="new123@example.com",
            password="testpass456"
        )
        Medicine.objects.create(
            user=new_user, daily_quantity=1, drug_name_and_dose="Med 123"
        )
        self.assertEqual(Medicine.objects.count(), 3)

    def test_validation_error_for_empty_required_field(self):
        """Test if model without required fields cannot be saved in database."""
        # Empty daily_quantity field
        with self.assertRaises(ValidationError):
            Medicine.objects.create(user=self.user, drug_name_and_dose="Med 123")
        # Empty drug_name_and_dose field
        with self.assertRaises(ValidationError):
            Medicine.objects.create(user=self.user, daily_quantity=2)

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.medicine), "Symbicort 160")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        all_fields = list(self.field_names.values())
        all_values = list(self.medicine.__dict__.values())
        for field, value in self.medicine:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                if len(all_values[number]) > 1:
                    self.assertEqual(
                        value.replace(
                            "[", "").replace(
                                "]", "").replace(
                                    "\"", "").replace(
                                        "'", "").replace(
                                            " ", "").split(","),
                        (all_values[number])
                    )
                else:
                    self.assertEqual(value.split(), (all_values[number]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            elif value == "":
                self.assertEqual(all_values[number], None)
            else:
                self.assertEqual(value, str(all_values[number]))

    def test_string_to_list_method(self):
        """Test if medication_days_to_list method and medication_hours_to_list
        converts string to a list based on comma separator."""
        record = Medicine.objects.create(
            user=self.user,
            drug_name_and_dose="Lek 100",
            daily_quantity=4,
            medication_days="Poniedziałek,Środa,Piątek",
            medication_hours="10:30,13:30,17:30,22:00"
            )
        self.assertEqual(record.medication_days, "Poniedziałek,Środa,Piątek")
        self.assertEqual(record.medication_days_to_list(),
                         ["Poniedziałek", "Środa", "Piątek"])
        self.assertEqual(record.medication_hours, "10:30,13:30,17:30,22:00")
        self.assertEqual(record.medication_hours_to_list(),
                         ["10:30", "13:30", "17:30", "22:00"])

    def test_validate_choices(self):
        """Test if save method validates choices before saving instance in database."""
        # test correct medication_frequency
        self.medicine.medication_frequency = "We wskazane dni tygodnia"
        self.medicine.save()
        self.assertEqual(self.medicine.medication_frequency,
                         "We wskazane dni tygodnia")
        # test correct medication_days
        self.medicine.medication_days = "Poniedziałek,Piątek"
        self.medicine.save()
        self.assertEqual(self.medicine.medication_days, "Poniedziałek,Piątek")

        # test incorrect medication_frequency
        self.medicine.medication_frequency = "Inny dzień"
        with self.assertRaises(ValidationError):
            self.medicine.save()
        # test incorrect medication_days
        self.medicine.medication_days = ["Inny dzień"]
        with self.assertRaises(ValidationError):
            self.medicine.save()
        self.medicine.medication_days = "Poniedziałek,Piontek"
        with self.assertRaises(ValidationError):
            self.medicine.save()


class MedicalVisitTests(TestCase):
    """Test MedicalVisit Model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456"
        )
        self.visit = MedicalVisitFactory(user=self.user,)
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "specialization": "Specjalizacja",
            "doctor": "Lekarz",
            "visit_date": "Dzień wizyty",
            "visit_time": "Godzina wizyty",
            "visit_location": "Lokalizacja wizyty",
            "notes": "Uwagi",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }

    def test_create_visit_successful(self):
        """Test if creating payment instance with valid data is successful."""
        visit = MedicalVisit.objects.all()
        self.assertEqual(visit.count(), 1)
        self.assertTrue(visit[0].user, self.user)
        self.assertTrue(visit[0].specialization, self.visit.specialization)

    def test_unique_together_constraint_for_visit(self):
        """Test if user can only have medical visits with unique fields:
        specialization, visit_date, visit_time (unique together)."""

        # Unique together (only unique specialization, visit_date, visit_time
        # fields for single user)
        with self.assertRaises(ValidationError):
            MedicalVisit.objects.create(
                user=self.user, specialization=self.visit.specialization,
                visit_date=self.visit.visit_date, visit_time=self.visit.visit_time
            )

        # Different users can have the same fields with unique together constraint
        user2 = User.objects.create_user(
            username="newuser123",
            email="new@example.com",
            password="testpass456"
        )
        MedicalVisit.objects.create(
            user=user2, specialization=self.visit.specialization,
            visit_date=self.visit.visit_date, visit_time=self.visit.visit_time
        )
        self.assertEqual(MedicalVisit.objects.count(), 2)

    def test_visit_id_is_uuid(self):
        """Test if id is represented as uuid"""
        self.assertTrue(isinstance(self.visit.id, uuid.UUID))
        self.assertEqual(self.visit.id, uuid.UUID(str(self.visit.id)))

    def test_field_is_not_none(self):
        """Test if creating an instance without required fields
        raises ValidationError."""

        # Visit without user field
        with self.assertRaises(ValidationError):
            MedicalVisit.objects.create(
                specialization="New visit",
                visit_date=self.visit.visit_date,
                visit_time=self.visit.visit_time
            )

        # Visit without specialization field
        with self.assertRaises(ValidationError):
            MedicalVisit.objects.create(
                user=self.user,
                visit_date=self.visit.visit_date,
                visit_time=self.visit.visit_time
            )

        # Visit without visit_date field
        with self.assertRaises(ValidationError):
            MedicalVisit.objects.create(
                user=self.user,
                specialization="New visit",
                visit_time=self.visit.visit_time
            )

        # Visit without visit_time field
        with self.assertRaises(ValidationError):
            MedicalVisit.objects.create(
                user=self.user,
                specialization="New visit",
                visit_date=self.visit.visit_date,
            )

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(
            str(self.visit),
            self.visit.specialization + " - " + str(self.visit.visit_date)
        )

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        all_fields = list(self.field_names.values())
        all_values = list(self.visit.__dict__.values())
        for field, value in self.visit:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                self.assertEqual(value, str(all_values[number][0]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            elif all_values[number]:
                self.assertEqual(value, str(all_values[number]))


class HealthTestResultTests(TestCase):
    """Test HealthTestResult Model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456"
        )
        self.result = HealthTestResultFactory(user=self.user, )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "name": "Nazwa",
            "test_result": "Wynik badania",
            "test_date": "Data badania",
            "disease": "Leczona choroba/dolegliwość",
            "notes": "Uwagi",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }

    def test_create_health_result_successful(self):
        """Test if creating payment instance with valid data is successful."""
        result = HealthTestResult.objects.all()
        self.assertEqual(result.count(), 1)
        self.assertTrue(result[0].user, self.user)
        self.assertTrue(result[0].test_result, self.result.test_result)

    def test_unique_together_constraint_for_visit(self):
        """Test if user can only have medical visits with unique fields:
        name, test_date (unique together)."""

        # Unique together (only unique name, test_date fields for single user)
        with self.assertRaises(ValidationError):
            HealthTestResult.objects.create(
                user=self.user, name=self.result.name,
                test_date=self.result.test_date, test_result="Good"
            )

        # Different users can have the same fields with unique together constraint
        user2 = User.objects.create_user(
            username="newuser123",
            email="new@example.com",
            password="testpass456"
        )
        HealthTestResult.objects.create(
            user=user2, name=self.result.name,
            test_date=self.result.test_date, test_result="Good"
        )
        self.assertEqual(HealthTestResult.objects.count(), 2)

    def test_visit_id_is_uuid(self):
        """Test if id is represented as uuid"""
        self.assertTrue(isinstance(self.result.id, uuid.UUID))
        self.assertEqual(self.result.id, uuid.UUID(str(self.result.id)))

    def test_field_is_not_none(self):
        """Test if creating an instance without required fields
        raises ValidationError."""

        # Visit without user field
        with self.assertRaises(ValidationError):
            HealthTestResult.objects.create(
                name="New result",
                test_date=self.result.test_date,
                test_result="Good"
            )

        # Visit without name field
        with self.assertRaises(ValidationError):
            HealthTestResult.objects.create(
                user=self.user,
                test_date=self.result.test_date,
                test_result="Good"
            )

        # Visit without test_date field
        with self.assertRaises(ValidationError):
            HealthTestResult.objects.create(
                user=self.user,
                name="New result",
                test_result="Good"
            )

        # Visit without test_result field
        with self.assertRaises(ValidationError):
            HealthTestResult.objects.create(
                user=self.user,
                name="New result",
                test_date=self.result.test_date
            )

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.result), self.result.name)

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        all_fields = list(self.field_names.values())
        all_values = list(self.result.__dict__.values())
        for field, value in self.result:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                self.assertEqual(value, str(all_values[number][0]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            elif all_values[number]:
                self.assertEqual(value, str(all_values[number]))
