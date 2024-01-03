import logging
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from parameterized import parameterized

from payment.factories import PaymentFactory
from payment.forms import PaymentForm

User = get_user_model()
logger = logging.getLogger("test")


class PaymentFormTests(TestCase):
    def setUp(self):
        self.payment = PaymentFactory()
        self.form = PaymentForm(payment_names=[])
        self.fields = [
            "name",
            "payment_type",
            "payment_method",
            "payment_status",
            "payment_frequency",
            "payment_months",
            "payment_day",
            "payment_value",
            "notes",
            "start_of_agreement",
            "end_of_agreement",
            "access_granted",
        ]

    def test_payment_form_empty_fields(self):
        """Test if form renders all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)
        for field in self.form.fields:
            self.assertIn(field, self.fields)

    def test_payment_form_has_correct_field_labels(self):
        """Test if fields have correct labels."""
        labels = [
            _("Nazwa"),
            _("Grupa opłat"),
            _("Sposób płatności"),
            _("Status płatności"),
            _("Częstotliwość płatności"),
            _("Miesiące płatności"),
            _("Dzień płatności"),
            _("Wysokość płatności"),
            _("Uwagi"),
            _("Data zawarcia umowy"),
            _("Data wygaśnięcia umowy"),
            _("Dostęp do danych"),
        ]
        for field, label in zip(self.fields, labels):
            self.assertEqual(self.form.fields[field].label, label)

    def test_payment_form_has_correct_help_text(self):
        """Test if fields have correct text help."""
        form = PaymentForm(payment_names=[])
        for field in self.fields:
            if field == "name":
                self.assertEqual(form.fields["name"].help_text, _("Pole wymagane."))
            elif field == "access_granted":
                self.assertEqual(form.fields["access_granted"].help_text, _(
                    "Użytkownik upoważniony do dostępu do danych "
                    "może przeglądać te dane."
                ))
            elif field == "start_of_agreement" or field == "end_of_agreement":
                self.assertEqual(form.fields["start_of_agreement"].help_text, _(
                    "Format: YYYY-MM-DD (np. 2020-07-21)."))
            else:
                self.assertEqual(form.fields[field].help_text, "")

    def test_payment_form_has_correct_error_messages(self):
        """Test if fields have error messages."""
        form = PaymentForm(payment_names=[])
        fields_with_choices = [
            "payment_type",
            "payment_method",
            "payment_status",
            "payment_frequency",
            "payment_day",
            "access_granted"
        ]
        for field in self.fields:
            if field in fields_with_choices:
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.',
                    'invalid_choice': 'Wybierz poprawną wartość. %(value)s '
                                      'nie jest żadną z dostępnych opcji.'
                })
            elif field == "name":
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.'
                })
            elif field == "payment_months":
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.',
                    'invalid_choice': 'Wybierz poprawną wartość. %(value)s '
                                      'nie jest żadną z dostępnych opcji.',
                    'invalid_list': 'Podaj listę wartości.'
                })
            elif field == "payment_value":
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.', 'invalid': 'Wpisz liczbę.'
                })
            elif field == "start_of_agreement" or field == "end_of_agreement":
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.',
                    'invalid': 'Wpisz poprawną datę.'
                })
            else:
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.',
                })

    def test_payment_form_has_correct_widgets(self):
        """Test if fields have correct widgets."""
        form = PaymentForm(payment_names=[])
        select_fields = [
            "payment_type",
            "payment_method",
            "payment_status",
            "payment_frequency",
            "payment_day",
            "access_granted",
        ]
        for field in select_fields:
            self.assertEqual(form.fields[field].widget.__class__.__name__,
                             "Select")
        self.assertEqual(form.fields["payment_months"].widget.__class__.__name__,
                         "CheckboxSelectMultiple")
        self.assertEqual(form.fields["payment_value"].widget.__class__.__name__,
                         "NumberInput")
        self.assertEqual(form.fields["name"].widget.__class__.__name__,
                         "TextInput")
        self.assertEqual(form.fields["notes"].widget.__class__.__name__,
                         "Textarea")
        self.assertEqual(form.fields["start_of_agreement"].widget.__class__.__name__,
                         "DateInput")  # "SelectDateWidget"
        self.assertEqual(form.fields["end_of_agreement"].widget.__class__.__name__,
                         "DateInput")

    def test_payment_form_widget_has_correct_css_class(self):
        """Test if fields have correct widget class"""
        form = PaymentForm(payment_names=[])
        fields = [
            "payment_type",
            "payment_method",
            "payment_status",
            "payment_frequency",
            "payment_day",
        ]
        for field in fields:
            self.assertEqual(form.fields[field].widget.attrs["class"], "input_field")

    def test_payment_clean_method_not_unique_name_validation(self):
        """Test if clean method validates if name field is always
        unique for one user."""
        payload = {
            "name": "Some payment",
            "access_granted": "Brak dostępu",
        }
        form = PaymentForm(
            data=payload, payment_names=["Some payment"]
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już płatność o podanej nazwie w bazie danych. "
                      "Podaj inną nazwę.", form.errors["name"])

    def test_payment_clean_payment_months_method(self):
        """Test that value of payment_months field is cleaned of all unwanted characters
        and plain values separated with comma as returned in one string."""
        payload = {
            "name": "New pmt",
            "payment_months": ['1', '3', '5'],  # or [1, 3, 5] as integers
            "access_granted": "Brak dostępu",
        }
        expected_result = "1,3,5"
        form = PaymentForm(data=payload, payment_names=["Some payment"])
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["payment_months"], expected_result)

    def test_payment_clean_method_start_of_agreement_validation(self):
        """
        Test if clean method validates start_of_agreement data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "name": "Some payment",
            "start_of_agreement": "2020,11,11",
            "access_granted": "Brak dostępu",
        }
        form = PaymentForm(data=payload, payment_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["start_of_agreement"])

    def test_payment_clean_method_end_of_agreement_validation(self):
        """
        Test if clean method validates end_of_agreement data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "name": "Some payment",
            "start_of_agreement": "2020-10-20",
            "end_of_agreement": "2020,11,11",
            "access_granted": "Brak dostępu",
        }
        form = PaymentForm(data=payload, payment_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["end_of_agreement"])

    def test_payment_clean_method_start_and_end_date_validation(self):
        """
        Test if clean method validates start_of_agreement and end_of_agreement
        data type correctly.
        End date cannot happen before start date.
        """
        payload = {
            "name": "Some payment",
            "start_of_agreement": date(2020, 11, 15),
            "end_of_agreement": date(2020, 11, 11),
            "access_granted": "Brak dostępu",
        }
        form = PaymentForm(data=payload, payment_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Data wygaśnięcia umowy nie może przypadać wcześniej "
                      "niż data jej zawarcia.", form.errors["end_of_agreement"])

    def test_payment_form_is_form_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "name": "testname123",
            "payment_type": _("Czynsz"),
            "payment_method": None,
            "payment_status": _("Brak informacji"),
            "payment_frequency": _("Rocznie"),
            "payment_months": ["5"],
            "payment_day": 11,
            "payment_value": None,
            "notes": None,
            "start_of_agreement": date(2020, 10, 10),
            "end_of_agreement": date(2020, 10, 15),
            "access_granted": _("Brak dostępu"),
        }
        payment_names = ["setup payment", "test payment"]
        form = PaymentForm(data=payload, payment_names=payment_names)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Empty field: name", "name",
             {"name": None, "access_granted": "Udostępnij dane"},
             "To pole jest wymagane."),
            ("Not unique field: name", "name",
             {"name": "New name", "access_granted": "Udostępnij dane"},
             "Istnieje już płatność o podanej nazwie w bazie danych. "
             "Podaj inną nazwę."),
            ("Invalid field 'start_of_agreement' (incorrect date form)",
             "start_of_agreement",
             {"name": "New test name", "start_of_agreement": "2020,11,11",
              "access_granted": "Udostępnij dane"}, "Wpisz poprawną datę."),
            ("Invalid field 'end_of_agreement' (incorrect date form)",
             "end_of_agreement",
             {"name": "New test name", "end_of_agreement": "2020,11,11",
              "access_granted": "Udostępnij dane"}, "Wpisz poprawną datę."),
            ("Negative value of payment_value", "payment_value",
             {"name": "New test name", "payment_value": -500,
              "access_granted": "Udostępnij dane"},
             "Wartość nie może być liczbą ujemną."),
        ]
    )
    def test_payment_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = PaymentForm(data=payload, payment_names=["New name"])
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])
