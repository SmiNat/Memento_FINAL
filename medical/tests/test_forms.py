import datetime
import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.test import TestCase
from parameterized import parameterized

from medical.factories import (MedCardFactory, MedicineFactory,
                               MedicalVisitFactory, HealthTestResultFactory)
from medical.forms import (MedCardForm, MedicineForm,
                           MedicalVisitForm, HealthTestResultForm)


User = get_user_model()
logger = logging.getLogger("test")


class MedCardFormTests(TestCase):
    """Tests for MedCardForm class."""

    def setUp(self):
        self.medcard = MedCardFactory()
        self.form = MedCardForm()
        self.fields = [
            # "name",
            "age",
            "weight",
            "height",
            "blood_type",
            "allergies",
            "diseases",
            "permanent_medications",
            "additional_medications",
            "main_doctor",
            "other_doctors",
            "emergency_contact",
            "notes",
            "access_granted",
            "access_granted_medicines",
            "access_granted_test_results",
            "access_granted_visits",
        ]

    def test_medcard_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            assert field in self.form.fields

    def test_medcard_form_field_labels(self):
        """Test if fields have correct labels."""
        # assert self.form.fields["name"].label == _("Nazwa")
        self.assertEqual(self.form.fields["age"].label, _("Wiek"))
        self.assertEqual(self.form.fields["weight"].label, _("Waga"))
        self.assertEqual(self.form.fields["height"].label, _("Wzrost"))
        self.assertEqual(self.form.fields["blood_type"].label, _("Grupa krwi"))
        self.assertEqual(self.form.fields["allergies"].label, _("Alergie"))
        self.assertEqual(self.form.fields["diseases"].label, _("Choroby"))
        self.assertEqual(self.form.fields["permanent_medications"].label,
                         _("Stałe leki"))
        self.assertEqual(self.form.fields["additional_medications"].label,
                         _("Leki dodatkowe"))
        self.assertEqual(self.form.fields["main_doctor"].label,
                         _("Lekarz prowadzący"))
        self.assertEqual(self.form.fields["other_doctors"].label,
                         _("Pozostali lekarze"))
        self.assertEqual(self.form.fields["emergency_contact"].label,
                         _("Osoba do kontaktu"))
        self.assertEqual(self.form.fields["notes"].label, _("Uwagi"))
        self.assertEqual(self.form.fields["access_granted"].label,
                         _("Dostęp do karty medycznej"))
        self.assertEqual(self.form.fields["access_granted_medicines"].label,
                         _("Dostęp do danych o lekach"))
        self.assertEqual(self.form.fields["access_granted_test_results"].label,
                         _("Dostęp do wyników badań"))
        self.assertEqual(self.form.fields["access_granted_visits"].label,
                         _("Dostęp do wizyt lekarskich"))

    def test_medcard_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field == "access_granted":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Użytkownik upoważniony do dostępu do danych może "
                            "przeglądać kartę medyczną."))
            elif field == "access_granted_medicines":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Użytkownik upoważniony do dostępu do danych może "
                            "przeglądać listę leków."))
            elif field == "access_granted_test_results":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Użytkownik upoważniony do dostępu do danych może "
                            "przeglądać wyniki badań."))
            elif field == "access_granted_visits":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Użytkownik upoważniony do dostępu do danych może "
                            "przeglądać wizyty lekarskie."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_medcard_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "access_granted" \
                    or field == "access_granted_medicines" \
                    or field == "access_granted_test_results" \
                    or field == "access_granted_visits":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid_choice": "Wybierz poprawną wartość. %(value)s nie "
                                      "jest żadną z dostępnych opcji.",
                })
            elif field in ["age", "weight", "height"]:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz liczbę całkowitą."
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_medcard_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            # "name",
            "allergies",
            "diseases",
            "permanent_medications",
            "additional_medications",
            "main_doctor",
            "other_doctors",
            "emergency_contact",
            "notes",
        ]
        numberfields = [
            "age",
            "weight",
            "height",
        ]
        selectfields = [
            "access_granted",
            "access_granted_medicines",
            "access_granted_test_results",
            "access_granted_visits"
        ]
        for charfield in charfields:
            if charfield == "main_doctor" or charfield == "name":
                self.assertEqual(self.form.fields[charfield].widget.__class__.__name__,
                                 "TextInput")
            else:
                self.assertEqual(self.form.fields[charfield].widget.__class__.__name__,
                                 "Textarea")
        for numberfield in numberfields:
            self.assertEqual(self.form.fields[numberfield].widget.__class__.__name__,
                             "NumberInput")
        for selectfield in selectfields:
            self.assertEqual(self.form.fields[selectfield].widget.__class__.__name__ ,
                             "Select")

    def test_medcard_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "blood_type": "A+",
            "allergies": "Grass",
            "permanent_medications": "Telfexo",
            "access_granted": "Udostępnij dane",
            "access_granted_medicines": "Udostępnij dane",
            "access_granted_test_results": "Brak dostępu",
            "access_granted_visits": "Brak dostępu",
        }
        form = MedCardForm(data=payload)
        self.assertTrue(form.is_valid())


class MedicineFormTests(TestCase):
    """Tests for MedicineForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser123",
            email="test123@example.com",
            password="testpass456"
        )
        self.medicine = MedicineFactory(user=self.user)
        self.form = MedicineForm(drug_names=[])
        self.fields = [
            "drug_name_and_dose",
            "daily_quantity",
            "disease",
            "medication_frequency",
            "medication_days",
            "exact_frequency",
            "medication_hours",
            "start_date",
            "start_date",
            "notes",
        ]

    def test_medicine_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_medicine_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["drug_name_and_dose"].label,
                         _("Nazwa leku i dawka"))
        self.assertEqual(self.form.fields["daily_quantity"].label,
                         _("Ilość dawek dziennie"))
        self.assertEqual(self.form.fields["disease"].label,
                         _("Leczona choroba/dolegliwość"))
        self.assertEqual(self.form.fields["medication_frequency"].label,
                         _("Częstotliwość przyjmowania leków"))
        self.assertEqual(self.form.fields["medication_days"].label,
                         _("Dni przyjmowania leków"))
        self.assertEqual(self.form.fields["exact_frequency"].label,
                         _("Co ile dni przyjmowane są leki"))
        self.assertEqual(self.form.fields["medication_hours"].label,
                         _("Godziny przyjmowania leków"))
        self.assertEqual(self.form.fields["start_date"].label,
                         _("Rozpoczęcie przyjmowania leku"))
        self.assertEqual(self.form.fields["end_date"].label,
                         _("Zakończenie przyjmowania leku"))
        self.assertEqual(self.form.fields["notes"].label, _("Uwagi"))

    def test_medicine_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field in ["drug_name_and_dose", "daily_quantity"]:
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane."))
            elif field == "medication_days":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Uzupełnij, jeśli leki przyjmowane są w konkretne dni "
                    "tygodnia."))
            elif field == "exact_frequency":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Uzupełnij, jeśli wskazano jako częstotliwość "
                    "'Co kilka dni' lub 'Inne'."))
            elif field == "start_date" or field == "end_date":
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Format: YYYY-MM-DD (np. 2020-07-21)."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_medicine_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "medication_days" or field == "medication_hours":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid_choice": "Wybierz poprawną wartość. %(value)s "
                                      "nie jest żadną z dostępnych opcji.",
                    "invalid_list": "Podaj listę wartości."
                })
            elif field == "daily_quantity":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz liczbę."
                })
            elif field == "start_date" or field == "end_date":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz poprawną datę."
                })
            elif field == "medication_frequency":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid_choice": "Wybierz poprawną wartość. "
                                      "%(value)s nie jest żadną z dostępnych opcji."
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_medicine_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "drug_name_and_dose",
            "exact_frequency",
            "disease",
            "notes",
        ]
        selectfields = [
            "medication_days",
            "medication_hours"
        ]
        datefields = [
            "start_date",
            "end_date"
        ]
        for field in charfields:
            if field == "notes":
                self.assertEqual(self.form.fields[
                       field].widget.__class__.__name__, "Textarea")
            else:
                self.assertEqual(self.form.fields[
                           field].widget.__class__.__name__, "TextInput")
        for field in selectfields:
            self.assertEqual(self.form.fields[
                   field].widget.__class__.__name__, "CheckboxSelectMultiple")
        for field in datefields:
            self.assertEqual(self.form.fields[
                   field].widget.__class__.__name__, "DateInput")
        self.assertEqual(self.form.fields[
                             "medication_frequency"].widget.__class__.__name__,
                         "Select")
        self.assertEqual(self.form.fields[
                             "daily_quantity"].widget.__class__.__name__, "NumberInput")

    def test_medicine_clean_medication_days_method(self):
        """Test that value of medication_days field is cleaned of all unwanted characters
        and plain values separated with comma as returned in one string."""
        payload = {
            "drug_name_and_dose": "New drug, 200",
            "medication_days": ["Poniedziałek", "Środa", "Sobota"],
            "daily_quantity": 2,
        }
        expected_result = "Poniedziałek,Środa,Sobota"
        form = MedicineForm(data=payload, drug_names=["Some name"])
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["medication_days"], expected_result)

    def test_medicine_clean_medication_hours_method(self):
        """Test that value of medication_hours field is cleaned of all unwanted characters
        and plain values separated with comma as returned in one string."""
        payload = {
            "drug_name_and_dose": "New drug, 200",
            "medication_hours": ["8:30", "10:30", "12:00"],
            "daily_quantity": 2,
        }
        expected_result = "8:30,10:30,12:00"
        form = MedicineForm(data=payload, drug_names=["Some name"])
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["medication_hours"], expected_result)

    def test_medicine_clean_method_not_unique_drug_name_validation(self):
        """Test if clean method validates if drug_name_and_dose field is always
        unique for one user."""
        payload = {
            "drug_name_and_dose": "Some name",
            "daily_quantity": 2,
        }
        form = MedicineForm(data=payload, drug_names=["Some name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już lek o podanej nazwie w bazie danych. "
                      "Podaj inną nazwę.", form.errors["drug_name_and_dose"])

    def test_medicine_clean_method_start_date_validation(self):
        """
        Test if clean method validates start_date data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "drug_name_and_dose": "Some name",
            "daily_quantity": 2,
            "start_date": "2020,11,11",
        }
        form = MedicineForm(data=payload, drug_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["start_date"])

    def test_medicine_clean_method_end_date_validation(self):
        """
        Test if clean method validates end_date data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "drug_name_and_dose": "Some name",
            "daily_quantity": 2,
            "end_date": "2020,11,11",
        }
        form = MedicineForm(data=payload, drug_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["end_date"])

    def test_medicine_clean_method_start_and_end_date_validation(self):
        """
        Test if clean method validates start_date and end_date data type correctly.
        End date cannot happen before start date.
        """
        payload = {
            "drug_name_and_dose": "Some name",
            "daily_quantity": 2,
            "start_date": datetime.date(2020, 11, 15),
            "end_date": datetime.date(2020, 11, 11),
        }
        form = MedicineForm(data=payload, drug_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Data zakończenia przyjmowania leku nie może przypadać "
                      "wcześniej niż data rozpoczęcia przyjmowania leku.",
                      form.errors["end_date"])

    def test_medicine_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "drug_name_and_dose": "Symbicort 160",
            "daily_quantity": 1,
            "medication_days": ["Poniedziałek", "Wtorek"],
            "medication_frequency": "Codziennie",
            "exact_frequency": None,
            "medication_hours": ["8:00", "20:00"],
            "start_date": datetime.date(2020, 1, 1),
            "end_date": None,
            "disease": "Asthma",
        }
        form = MedicineForm(drug_names=["Some name"], data=payload)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Negative number of units", "daily_quantity",
             {"drug_name_and_dose": "Some med", "daily_quantity": -11},
             "Wartość nie może być liczbą ujemną."),
            ("Missing required field: daily_quantity", "daily_quantity",
             {"drug_name_and_dose": "Some med", "daily_quantity": None},
             "To pole jest wymagane."),
            ("Missing required field: drug_name_and_dose", "drug_name_and_dose",
             {"drug_name_and_dose": None, "daily_quantity": 11},
             "To pole jest wymagane."),
            ("Not unique drug_name_and_dose field", "drug_name_and_dose",
             {"drug_name_and_dose": "New med", "daily_quantity": 11},
             "Istnieje już lek o podanej nazwie w bazie danych. Podaj inną nazwę."),
            ("Invalid field 'start_date' (incorrect date form)", "start_date",
             {"drug_name_and_dose": "New test name", "start_date": "2020,11,11",
              "daily_quantity": 1}, "Wpisz poprawną datę."),
            ("Invalid field 'end_date' (incorrect date form)", "end_date",
             {"drug_name_and_dose": "New test name", "end_date": "2020,11,11",
              "daily_quantity": 1}, "Wpisz poprawną datę.")
        ]
    )
    def test_medicine_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = MedicineForm(data=payload, drug_names=["New med"])
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])


class MedicalVisitFormTests(TestCase):
    """Tests for MedicalVisitForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser123",
            email="test123@example.com",
            password="testpass456"
        )
        self.visit = MedicalVisitFactory(user=self.user)
        self.form = MedicalVisitForm(queryset=None)
        self.fields = [
            "specialization",
            "doctor",
            "visit_date",
            "visit_time",
            "visit_location",
            "notes",
        ]

    def test_visit_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_visit_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["specialization"].label, _("Specjalizacja"))
        self.assertEqual(self.form.fields["doctor"].label, _("Lekarz"))
        self.assertEqual(self.form.fields["visit_date"].label, _("Dzień wizyty"))
        self.assertEqual(self.form.fields["visit_time"].label, _("Godzina wizyty"))
        self.assertEqual(self.form.fields["visit_location"].label, _("Lokalizacja wizyty"))
        self.assertEqual(self.form.fields["notes"].label, _("Uwagi"))

    def test_visit_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field in ["specialization", "visit_time"]:
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane."))
            elif field == "visit_date":
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane. Format: YYYY-MM-DD "
                                   "(np. 2020-07-21)."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_visit_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "specialization":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })
            elif field == "visit_time":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz poprawną godzinę."
                })
            elif field == "visit_date":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz poprawną datę."
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_visit_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "specialization",
            "doctor",
            "visit_location",
            "notes"
        ]
        datefields = [
            "visit_date"
        ]
        for field in charfields:
            if field == "notes":
                self.assertEqual(self.form.fields[
                       field].widget.__class__.__name__, "Textarea")
            else:
                self.assertEqual(self.form.fields[
                           field].widget.__class__.__name__, "TextInput")
        for field in datefields:
            self.assertEqual(self.form.fields[
                   field].widget.__class__.__name__, "DateInput")
        self.assertEqual(self.form.fields["visit_time"].widget.__class__.__name__,
                         "TimeInput")

    def test_visit_clean_method_not_unique_together_validation(self):
        """Test if clean method validates if specialization together with
        visit_date and visit_time fields is always unique for one user."""
        # Unique set of data (different visit date)
        queryset = [{"specialization": "Dermatolog",
                     "visit_date": datetime.date(2023, 10, 10),
                     "visit_time": datetime.time(8, 30)}]
        payload = {
            "specialization": "Dermatolog",
            "visit_date": datetime.date(2023, 11, 11),
            "visit_time": datetime.time(8, 30)
        }
        form = MedicalVisitForm(data=payload, queryset=queryset)
        self.assertTrue(form.is_valid())
        # Not unique set of data
        payload = {
            "specialization": "Dermatolog",
            "visit_date": datetime.date(2023, 10, 10),
            "visit_time": datetime.time(8, 30)
        }
        form = MedicalVisitForm(data=payload, queryset=queryset)
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już wizyta u tego specjalisty w danym dniu "
                      "i o wskazanej godzinie.", form.errors["specialization"])

    def test_visit_clean_method_visit_date_validation(self):
        """
        Test if clean method validates visit_date data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "specialization": "Dermatolog",
            "visit_time": datetime.time(12, 30),
            "visit_date": "2020,11,11",
        }
        form = MedicalVisitForm(data=payload, queryset=None)
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["visit_date"])

    def test_visit_form_is_valid(self):
        """Test if form is valid with valid data."""
        queryset = [{'specialization': 'Periodontolog',
                     'visit_date': datetime.date(2023, 10, 31),
                     'visit_time': datetime.time(19, 0)}]
        payload = {
            "specialization": "Dermatolog",
            "visit_date": datetime.date(2023, 10, 31),
            "visit_time": "19:00",
            "doctor": "Dr Howser",
            "visit_location": "Hospital",
        }
        form = MedicalVisitForm(data=payload, queryset=queryset)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Missing required field: specialization", "specialization",
             {"visit_date": datetime.date(2023, 10, 31),
              "visit_time":  datetime.time(19, 0)}, "To pole jest wymagane."),
            ("Missing required field: visit_date", "visit_date",
             {"specialization": "Alergolog",
              "visit_time":  datetime.time(19, 0)}, "To pole jest wymagane."),
            ("Missing required field: visit_time", "visit_time",
             {"specialization": "Alergolog",
              "visit_date": datetime.date(2023, 10, 31)}, "To pole jest wymagane."),
            ("Not unique set of fields", "specialization",
             {"specialization": "Periodontolog",
              "visit_date": datetime.date(2023, 10, 31),
              "visit_time": datetime.time(19, 0)},
             "Istnieje już wizyta u tego specjalisty w danym dniu i o "
             "wskazanej godzinie."),
            ("Invalid field 'visit_date' (incorrect date form)", "visit_date",
             {"specialization": "Alergolog",
              "visit_date": "2020,11,11",
              "visit_time":  datetime.time(19, 0)}, "Wpisz poprawną datę.")
        ]
    )
    def test_visit_form_is_not_valid(
            self, name:str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        queryset = [{"specialization": "Periodontolog",
                     "visit_date": datetime.date(2023, 10, 31),
                     "visit_time": datetime.time(19, 0)}]
        form = MedicalVisitForm(data=payload, queryset=queryset)
        self.assertFalse(form.is_valid())


class HealthTestResultFormTests(TestCase):
    """Tests for HealthTestResultForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser123",
            email="test123@example.com",
            password="testpass456"
        )
        self.test = HealthTestResultFactory(user=self.user)
        self.form = HealthTestResultForm(queryset=None)
        self.fields = [
            "name",
            "test_result",
            "test_date",
            "disease",
            "notes",
        ]

    def test_health_test_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_health_test_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["test_result"].label, _("Wynik badania"))
        self.assertEqual(self.form.fields["test_date"].label, _("Data badania"))
        self.assertEqual(self.form.fields["disease"].label, _("Leczona choroba/dolegliwość"))
        self.assertEqual(self.form.fields["notes"].label, _("Uwagi"))

    def test_health_test_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field in ["name", "test_result"]:
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane."))
            elif field == "test_date":
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane. Format: YYYY-MM-DD "
                                   "(np. 2020-07-21)."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_health_test_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field in ["name", "test_result"]:
                self.assertEqual(
                    self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })
            elif field == "test_date":
                self.assertEqual(
                    self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz poprawną datę."
                })
            else:
                self.assertEqual(
                    self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_health_test_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
            "test_result",
            "disease",
            "notes"
        ]
        datefields = [
            "test_date"
        ]
        for field in charfields:
            if field == "notes" or field == "test_result":
                self.assertEqual(self.form.fields[
                       field].widget.__class__.__name__, "Textarea")
            else:
                self.assertEqual(self.form.fields[
                           field].widget.__class__.__name__, "TextInput")
        for field in datefields:
                self.assertEqual(self.form.fields[
                   field].widget.__class__.__name__, "DateInput")

    def test_health_test_clean_method_not_unique_name_and_date_validation(self):
        """Test if clean method validates if name together with test_date field
         is always unique for one user."""
        queryset = [{"name": "COVID result",
                     "test_date": datetime.date(2023, 10, 10)}]
        payload = {
            "name": "COVID result",
            "test_result": "Negative",
            "test_date": datetime.date(2023, 10, 10)
        }
        form = HealthTestResultForm(data=payload, queryset=queryset)
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już test o tej nazwie wykonany w danym dniu.",
                      form.errors["name"])

    def test_health_test_clean_method_test_date_validation(self):
        """
        Test if clean method validates test_date data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "name": "COVID result",
            "test_result": "Negative",
            "test_date": "2020,11,11",
        }
        form = HealthTestResultForm(data=payload, queryset=None)
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["test_date"])

    def test_health_test_form_is_valid(self):
        """Test if form is valid with valid data."""
        queryset = [{"name": "COVID result",
                     "test_date": datetime.date(2023, 10, 10), }]
        payload = {
            "name": "COVID result",
            "test_result": "Negative",
            "test_date": datetime.date(2020, 1, 1),
            "disease": "Asthma",
        }
        form = HealthTestResultForm(queryset=queryset, data=payload)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Missing required field: name", "name",
             {"test_result": "Negative", "test_date": datetime.date(2020, 1, 1)},
             "To pole jest wymagane."),
            ("Missing required field: test_result", "test_result",
             {"name": "New test", "test_date": datetime.date(2020, 1, 1)},
             "To pole jest wymagane."),
            ("Missing required field: test_date", "test_date",
             {"name": "New test", "test_result": "Negative"},
             "To pole jest wymagane."),
            ("Not unique together name and date field", "name",
             {"name": "COVID result", "test_date": datetime.date(2023, 10, 10),
              "test_result": "Negative"},
             "Istnieje już test o tej nazwie wykonany w danym dniu."),
            ("Invalid field 'test_date' (incorrect date form)", "test_date",
             {"name": "New test", "test_result": "Negative",
              "test_date": "2020,11,11"}, "Wpisz poprawną datę.")
        ]
    )
    def test_health_test_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        queryset = [{"name": "COVID result",
                     "test_date": datetime.date(2023, 10, 10)}]
        form = HealthTestResultForm(data=payload, queryset=queryset)
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])
