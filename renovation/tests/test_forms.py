import datetime
import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.test import TestCase
from parameterized import parameterized

from renovation.factories import RenovationFactory, RenovationCostFactory
from renovation.forms import RenovationForm, RenovationCostForm


User = get_user_model()
logger = logging.getLogger("test")


class RenovationFormTests(TestCase):
    """Tests for RenovationForm class."""

    def setUp(self):
        self.renovation = RenovationFactory()
        self.form = RenovationForm(renovation_names=["Test name"])
        self.fields = [
            "name",
            "description",
            "estimated_cost",
            "start_date",
            "end_date",
            "access_granted",
        ]

    def test_renovation_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_renovation_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["description"].label, _("Opis"))
        self.assertEqual(self.form.fields["estimated_cost"].label, _("Szacowany koszt"))
        self.assertEqual(self.form.fields["start_date"].label, _("Data rozpoczęcia"))
        self.assertEqual(self.form.fields["end_date"].label, _("Data zakończenia"))
        self.assertEqual(self.form.fields["access_granted"].label, _("Dostęp do danych"))

    def test_renovation_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Pole wymagane.",
                ))
            elif field == "access_granted":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać te dane."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_renovation_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "start_date" or field == "end_date":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz poprawną datę.",
                })
            elif field == "estimated_cost":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz liczbę.",
                })
            elif field == "access_granted":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid_choice": "Wybierz poprawną wartość. %(value)s nie "
                                      "jest żadną z dostępnych opcji.",
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_renovation_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
        ]
        textareas = [
            "description",
        ]
        for charfield in charfields:
            self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "TextInput")
        for textarea in textareas:
            self.assertEqual(self.form.fields[
                       textarea].widget.__class__.__name__, "Textarea")
        self.assertEqual(self.form.fields["estimated_cost"].widget.__class__.__name__,
                           "NumberInput")
        self.assertEqual(
            self.form.fields["start_date"].widget.__class__.__name__,
            self.form.fields["end_date"].widget.__class__.__name__,
            "SelectDateWidget"
        )
        self.assertEqual(self.form.fields["access_granted"].widget.__class__.__name__,
                          "Select")

    def test_renovation_clean_method_start_date_validation(self):
        """
        Test if clean method validates start_date data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "name": "Some renovation",
            "start_date": "2020,11,11",
            "access_granted": "Brak dostępu",
        }
        form = RenovationForm(data=payload, renovation_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["start_date"])

    def test_renovation_clean_method_end_date_validation(self):
        """
        Test if clean method validates end_date data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "name": "Some renovation",
            "start_date": "2020-10-20",
            "end_date": "2020,11,11",
            "access_granted": "Brak dostępu",
        }
        form = RenovationForm(data=payload, renovation_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["end_date"])

    def test_renovation_clean_method_start_and_end_date_validation(self):
        """
        Test if clean method validates start_date and end_date data type correctly.
        End date cannot happen before start date.
        """
        payload = {
            "name": "Some renovation",
            "start_date": datetime.date(2020, 11, 15),
            "end_date": datetime.date(2020, 11, 11),
            "access_granted": "Brak dostępu",
        }
        form = RenovationForm(data=payload, renovation_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Data zakończenia remontu nie może przypadać wcześniej "
                      "niż data jego rozpoczęcia.", form.errors["end_date"])

    def test_renovation_clean_method_not_unique_name_validation(self):
        """Test if clean method validates if name field is always
        unique for one user."""
        payload = {
            "name": "Renovation test name",
            "access_granted": "Brak dostępu",
        }
        form = RenovationForm(
            data=payload, renovation_names=["Renovation test name"]
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już remont o podanej nazwie w bazie danych. "
                      "Podaj inną nazwę.", form.errors["name"])

    def test_renovation_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "name": "Test of unique name",
            "description": "Bathroom and living room",
            "start_date": datetime.date(2020, 2, 2),
            "end_date": datetime.date(2020, 2, 12),
            "estimated_cost": 20000,
            "access_granted": "Udostępnij dane",
        }
        form = RenovationForm(data=payload, renovation_names=["Test name"])
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Not unique field: name",
             {"name": "Test name", "access_granted": "Udostępnij dane"}),
            ("Invalid field 'start_date' (incorrect date form)",
             {"name": "New test name", "start_date": "2020,11,11",
              "access_granted": "Udostępnij dane"}),
            ("Invalid field 'end_date' (incorrect date form)",
             {"name": "New test name", "end_date": "2020,11,11",
              "access_granted": "Udostępnij dane"}),
            ("Negative value of estimated cost",
             {"name": "New test name", "estimated_cost": -500,
              "access_granted": "Udostępnij dane"}),
        ]
    )
    def test_renovation_form_is_not_valid(self, name, payload):
        """Test if form is not valid with invalid data."""
        form = RenovationForm(data=payload, renovation_names=["Test name"])
        self.assertFalse(form.is_valid())


class RenovationCostFormTests(TestCase):
    """Tests for RenovationCostForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="renovation_report",
            email="rr@example.com",
            password="testpass123"
        )
        self.renovation_cost = RenovationCostFactory(user=self.user)
        self.form = RenovationCostForm()
        self.fields = [
            "name",
            "unit_price",
            "units",
            "description",
            "order",
        ]

    def test_renovation_cost_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_renovation_cost_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label,_("Nazwa"))
        self.assertEqual(self.form.fields["unit_price"].label,
                         _("Cena jednostkowa"))
        self.assertEqual(self.form.fields["units"].label, _("Liczba sztuk"))
        self.assertEqual(self.form.fields["description"].label, _("Opis"))
        self.assertEqual(self.form.fields["order"].label,
                         _("Informacje dot. zamówienia"))

    def test_renovation_cost_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field in ["name", "unit_price", "units"]:
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_renovation_cost_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })
            elif field == "unit_price" or field == "units":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz liczbę."
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_renovation_cost_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
            "description",
            "order"
        ]
        floatfields = [
            "unit_price",
            "units"
        ]
        for charfield in charfields:
            if charfield == "name":
                self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "TextInput")
            else:
                self.assertEqual(self.form.fields[
                           charfield].widget.__class__.__name__, "Textarea")
        for floatfield in floatfields:
            self.assertEqual(self.form.fields[
                   floatfield].widget.__class__.__name__, "NumberInput")

    def test_renovation_cost_form_is_valid(self):
        """Test if form is valid with valid data."""
        correct_data = {
            "name": "New renovation cost",
            "description": "New furniture",
            "unit_price": 130,
            "units": 2,
            "order": None,
        }
        form = RenovationCostForm(data=correct_data)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Negative number of units", "units",
             {"name": "Cost name", "unit_price": 1, "units": -20},
             "Wartość nie może być liczbą ujemną."),
            ("Missing required field: units", "units",
             {"name": "Cost name", "unit_price": 1}, "To pole jest wymagane."),
            ("Missing required field: unit_price", "unit_price",
             {"name": "Cost name", "units": 1}, "To pole jest wymagane."),
            ("Missing required field: unit_price", "name",
             {"unit_price": 100, "units": 1}, "To pole jest wymagane."),
        ]
    )
    def test_renovation_cost_form_is_not_valid(
            self, name: str, field: str, invalid_data: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = RenovationCostForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])
