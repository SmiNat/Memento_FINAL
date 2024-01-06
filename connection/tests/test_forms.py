import logging
import os
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from parameterized import parameterized
from reportlab.pdfgen.canvas import Canvas

from connection.factories import CounterpartyFactory, AttachmentFactory
from connection.forms import CounterpartyForm, AttachmentForm
from connection.models import Attachment

logger = logging.getLogger("test")
User = get_user_model()


class CounterpartyFormTests(TestCase):
    """Tests CounterpartyForm class."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test123@example.com", password="testpass456"
        )
        self.fields = [
            "payments",
            "credits",
            "renovations",
            "trips",
            "name",
            "phone_number",
            "email",
            "address",
            "www",
            "bank_account",
            "payment_app",
            "client_number",
            "primary_contact_name",
            "primary_contact_phone_number",
            "primary_contact_email",
            "notes",
            "access_granted",
        ]

    def test_counterparty_form_has_correct_empty_fields(self):
        """Test if form renders all fields."""
        cp_names = []
        form = CounterpartyForm(cp_names=cp_names)
        for field in self.fields:
            self.assertIn(field, form.fields)
        for field in form.fields:
            self.assertIn(field, self.fields)

    def test_counterparty_form_has_correct_field_labels(self):
        """Test if fields have correct labels."""
        form = CounterpartyForm(cp_names=[])
        labels = [
            _("Wybierz płatności"),
            _("Wybierz kredyty"),
            _("Wybierz remonty"),
            _("Wybierz podróże"),
            _("Nazwa"),
            _("Numer telefonu - infolinia"),
            _("Adres email - ogólny"),
            _("Adres korespondencyjny"),
            _("Strona internetowa"),
            _("Numer konta do przelewów"),
            _("Aplikacja do zarządzania płatnościami"),
            _("Numer płatnika (klienta)"),
            _("Imię i nazwisko"),
            _("Numer telefonu"),
            _("Adres email"),
            _("Uwagi"),
            _("Dostęp do danych"),
        ]
        for field, label in zip(self.fields, labels):
            self.assertEqual(form.fields[field].label, label)

    def test_counterparty_form_has_correct_help_text(self):
        """Test if fields have correct help text."""
        form = CounterpartyForm(cp_names=[])
        for field in self.fields:
            if field == "name":
                assert form.fields["name"].help_text == _("Pole wymagane.")
            elif field == "payments":
                self.assertEqual(form.fields[field].help_text, _(
                    "Jeśli kontrahent dotyczy płatności, której nie ma na "
                    "liście, dodaj wpierw płatność."))
            elif field == "credits":
                self.assertEqual(form.fields[field].help_text, _(
                    "Jeśli kontrahent dotyczy kredytu, którego nie ma na "
                    "liście, dodaj wpierw kredyt."))
            elif field == "renovations":
                self.assertEqual(form.fields[field].help_text, _(
                    "Jeśli kontrahent dotyczy remontu, którego nie ma na "
                    "liście, dodaj wpierw remont."))
            elif field == "trips":
                self.assertEqual(form.fields[field].help_text, _(
                    "Jeśli kontrahent dotyczy podróży, której nie ma na "
                    "liście, dodaj wpierw podróż."))
            elif field == "bank_account":
                self.assertEqual(form.fields[field].help_text,
                                 _("Dozwolone znaki: A-Z0-9- ."))
            elif field == "access_granted":
                self.assertEqual(form.fields[field].help_text, _(
                    "Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać te dane."))
            else:
                self.assertEqual(form.fields[field].help_text, "")

    def test_counterparty_form_has_correct_error_messages(self):
        """Test if fields have correct error messages."""
        form = CounterpartyForm(cp_names=[])
        fields_with_choices = [
            "payments",
            "credits",
            "renovations",
            "trips",
        ]
        for field in self.fields:
            if field in fields_with_choices:
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.',
                    'invalid_choice': 'Wybierz poprawną wartość. %(value)s '
                                      'nie jest żadną z dostępnych opcji.',
                    'invalid_list': 'Podaj listę wartości.',
                    'invalid_pk_value': '„%(pk)s” nie jest poprawną wartością.'})
            elif field == "www":
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.',
                    'invalid': 'Wpisz poprawny URL.'})
            elif field == "access_granted":
                self.assertEqual(form.fields["access_granted"].error_messages, {
                    'required': 'To pole jest wymagane.',
                    'invalid_choice': 'Wybierz poprawną wartość. %(value)s nie '
                                      'jest żadną z dostępnych opcji.'})
            else:
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.'})

    def test_counterparty_form_has_correct_widgets(self):
        """Test if fields have correct widgets."""
        form = CounterpartyForm(cp_names=[])
        for field in self.fields:
            if field in ["payments", "credits", "renovations", "trips"]:
                self.assertEqual(form.fields[field].widget.__class__.__name__,
                                 "SelectMultiple")
            elif field == "www":
                self.assertEqual(form.fields["www"].widget.__class__.__name__,
                                 "URLInput")
            elif field in ["email", "primary_contact_email"]:
                self.assertEqual(form.fields[field].widget.__class__.__name__,
                                 "EmailInput")
            elif field == "notes":
                self.assertEqual(form.fields[field].widget.__class__.__name__,
                                 "Textarea")
            elif field == "access_granted":
                self.assertEqual(form.fields[field].widget.__class__.__name__,
                                 "Select")
            else:
                self.assertEqual(form.fields[field].widget.__class__.__name__,
                                 "TextInput")

    def test_counterparty_clean_name_unique_validation(self):
        """Test if clean method validates if name is always unique for one user."""
        counterparty = CounterpartyFactory(user=self.user, name="New test name")
        cp_names = ["ABC counterparty", "Big4 cp", counterparty.name]
        # The same name for different users
        payload = {
            "name": counterparty.name,
            "access_granted": "Dostęp do danych",
        }
        form = CounterpartyForm(data=payload, cp_names=cp_names)
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już kontrahent o podanej nazwie w bazie danych.",
                      form.errors["name"])

    def test_counterparty_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {"name": "New name", "access_granted": "Brak dostępu"}
        cp_names = []
        form = CounterpartyForm(data=payload, cp_names=cp_names)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Empty field: name", "name", {"access_granted": "Brak dostępu"},
             "To pole jest wymagane."),
            ("Empty field: access_granted", "access_granted",
             {"name": "Brak dostępu"}, "To pole jest wymagane."),
            ("Not unique field: name", "name",
             {"name": "some old name", "access_granted": "Brak dostępu"},
             "Istnieje już kontrahent o podanej nazwie w bazie danych."),
            ("Incorrect email field", "email",
             {"name": "New cp", "access_granted": "Brak dostępu",
              "email": "ma$t&@examplecom"}, "Wprowadź poprawny adres email."),
            ("Incorrect url field", "www",
             {"name": "New cp", "access_granted": "Brak dostępu",
              "www": "youtube"}, "Wpisz poprawny URL."),
            ("Incorrect bank_account field", "bank_account",
             {"name": "New cp", "access_granted": "Brak dostępu",
              "bank_account": "SOME 1234"}, "Wpisz poprawną wartość."),
        ]
    )
    def test_counterparty_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        cp_names = ["some old name"]
        form = CounterpartyForm(data=payload, cp_names=cp_names)
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, dict(form.errors)[field])


class AttachmentFormTests(TestCase):
    """Tests AttachmentForm class."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        self.fields = [
            "payments",
            "counterparties",
            "credits",
            "renovations",
            "trips",
            "health_results",
            "medical_visits",
            "attachment_name",
            "attachment_path",
            "file_date",
            "file_info",
            "access_granted",
        ]

        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.attachment = Attachment.objects.create(
            user=self.user, attachment_name="setup attachment")

    def test_attachment_form_has_correct_empty_fields(self):
        """Test if form renders empty fields."""
        attachment_names = []
        form = AttachmentForm(attachment_names=attachment_names)
        for field in self.fields:
            self.assertIn(field, form.fields)
        for field in form.fields:
            self.assertIn(field, self.fields)

    def test_attachment_form_has_correct_field_labels(self):
        """Test if fields have correct labels."""
        labels = [
            _("Wybierz płatność"),
            _("Wybierz kontrahenta"),
            _("Wybierz kredyt"),
            _("Wybierz remont"),
            _("Wybierz podróż"),
            _("Wybierz badania"),
            _("Wybierz wizytę"),
            _("Nazwa dokumentu"),
            _("Załącz dokument"),
            _("Data zawarcia dokumentu"),
            _("Informacja o dokumencie"),
            _("Dostęp do danych"),
        ]
        attachment_names = []
        form = AttachmentForm(attachment_names=attachment_names)
        for field, label in zip(self.fields, labels):
            self.assertEqual(form.fields[field].label, label)

    def test_attachment_form_has_correct_help_text(self):
        """Test if fields have correct help text."""
        attachment_names = []
        form = AttachmentForm(attachment_names=attachment_names)
        self.assertEqual(form.fields["payments"].help_text, _(
            "Jeśli załącznik dotyczy płatności, której nie ma na liście, "
            "dodaj wpierw płatność."))
        self.assertEqual(form.fields["counterparties"].help_text,
                         _("Jeśli załącznik dotyczy kontrahenta, którego nie "
                           "ma na liście, dodaj wpierw kontrahenta."))
        self.assertEqual(form.fields["renovations"].help_text,
                         _("Jeśli załącznik dotyczy remontu, którego nie ma "
                           "na liście, dodaj wpierw remont."))
        self.assertEqual(form.fields["credits"].help_text,
                         _("Jeśli załącznik dotyczy kredytu, którego nie ma "
                           "na liście, dodaj wpierw kredyt."))
        self.assertEqual(form.fields["trips"].help_text,
                         _("Jeśli załącznik dotyczy wyjazdu, którego nie ma "
                           "na liście, dodaj wpierw wyjazd."))
        self.assertEqual(form.fields["health_results"].help_text,
                         _("Jeśli załącznik dotyczy badania, którego nie ma "
                           "na liście, dodaj wpierw badanie."))
        self.assertEqual(form.fields["medical_visits"].help_text,
                         _("Jeśli załącznik dotyczy wizyty, której nie ma "
                           "na liście, dodaj wpierw wizytę."))
        self.assertEqual(form.fields["attachment_name"].help_text,
                         _("Pole wymagane."))
        self.assertEqual(form.fields["attachment_path"].help_text,
                         _("Tylko pliki pdf oraz png i jpg."))
        self.assertEqual(form.fields["file_date"].help_text,
                         "Format: YYYY-MM-DD (np. 2020-07-21).")
        self.assertEqual(form.fields["file_info"].help_text, "")
        self.assertEqual(form.fields["access_granted"].help_text,
                         _("Użytkownik upoważniony do dostępu do danych może "
                           "przeglądać te dane."))

    def test_attachment_form_has_correct_error_messages(self):
        """Test if fields have correct error messages."""
        selectfields = ["access_granted", "counterparties", "renovations",
                        "credits", "trips", "medical_visits", "health_results"]
        attachment_names = []
        form = AttachmentForm(attachment_names=attachment_names)
        for field in selectfields:
            if field == "access_granted":
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.',
                    'invalid_choice': 'Wybierz poprawną wartość. %(value)s nie '
                                      'jest żadną z dostępnych opcji.',
                })
            else:
                self.assertEqual(form.fields[field].error_messages, {
                    'required': 'To pole jest wymagane.',
                    'invalid_choice': 'Wybierz poprawną wartość. %(value)s nie '
                                      'jest żadną z dostępnych opcji.',
                    'invalid_list': 'Podaj listę wartości.',
                    'invalid_pk_value': '„%(pk)s” nie jest poprawną wartością.'
                })
        self.assertEqual(form.fields["attachment_name"].error_messages, {
            'required': 'To pole jest wymagane.'})
        self.assertEqual(form.fields["attachment_path"].error_messages, {
            'required': 'To pole jest wymagane.',
            'invalid': 'Nie wysłano żadnego pliku. Sprawdź typ kodowania '
                       'formularza.',
            'missing': 'Żaden plik nie został przesłany.',
            'empty': 'Wysłany plik jest pusty.',
            'max_length': '',
            'contradiction': 'Prześlij plik lub zaznacz by usunąć, ale nie oba '
                             'na raz.'})
        self.assertEqual(form.fields["file_date"].error_messages, {
            'required': 'To pole jest wymagane.',
            'invalid': 'Wpisz poprawną datę.'})
        self.assertEqual(form.fields["file_info"].error_messages, {
            'required': 'To pole jest wymagane.'})
        self.assertEqual(form.fields["access_granted"].error_messages, {
            'required': 'To pole jest wymagane.',
            'invalid_choice': 'Wybierz poprawną wartość. %(value)s nie jest '
                              'żadną z dostępnych opcji.'})

    def test_attachment_form_has_correct_widgets(self):
        """Test if fields have correct widgets."""
        selectfields = ["counterparties", "renovations", "credits", "trips",
                        "medical_visits", "health_results", "payments"]
        attachment_names = []
        form = AttachmentForm(attachment_names=attachment_names)
        for field in selectfields:
            self.assertEqual(form.fields[field].widget.__class__.__name__,
                             "SelectMultiple")
        self.assertEqual(form.fields["attachment_name"].widget.__class__.__name__,
                         "TextInput")
        self.assertEqual(form.fields["attachment_path"].widget.__class__.__name__,
                         "ClearableFileInput")
        self.assertEqual(form.fields["file_date"].widget.__class__.__name__,
                         "DateInput")
        self.assertEqual(form.fields["file_info"].widget.__class__.__name__,
                         "Textarea")
        self.assertEqual(form.fields["access_granted"].widget.__class__.__name__,
                         "Select")

    def test_attachment_form_widget_has_correct_css_class(self):
        """Test if fields have correct widget class."""
        attachment_names = []
        form = AttachmentForm(attachment_names=attachment_names)
        self.assertEqual(form.fields["attachment_path"].widget.attrs["class"],
                         "attach_field")

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_attachment_clean_name_unique_validation(self):
        """Test if clean method validates if name is always unique for one user."""
        attachment = AttachmentFactory(user=self.user,
                                       attachment_name="New test name")
        attachment_names = ["ABC attachment", "Big4 file",
                            attachment.attachment_name]
        # The same name for different users
        payload = {
            "attachment_name": attachment.attachment_name,
            "access_granted": "Dostęp do danych",
        }
        form = AttachmentForm(data=payload, attachment_names=attachment_names)
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już załącznik o podanej nazwie w bazie danych.",
                      form.errors["attachment_name"])

        path = os.path.join(settings.TEST_ROOT, str(self.user.id))
        if os.path.exists(path):
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            else:
                shutil.rmtree(path)
        # os.rmdir(settings.TEST_ROOT)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_attachment_form_is_valid(self):
        """Test if form is valid with valid data."""
        attachment_names = []
        file_data = {"img": SimpleUploadedFile("test.png", b"file data")}
        payload = {
            "attachment_name": "Some new file",
            "access_granted": "Brak dostępu",
            "attachment_path": file_data,
        }
        form = AttachmentForm(data=payload, attachment_names=attachment_names)
        if form.errors:
            logger.error("🛑 Fail in test: test_attachment_form_is_valid (connection.tests.test_forms). Error message:" % form.errors)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Empty field: attachment_name", "attachment_name",
             {"attachment_name": "", "access_granted": "Brak dostępu"},
             "To pole jest wymagane."),
            ("Empty field: access_granted", "access_granted",
             {"attachment_name": "Some new name", "access_granted": ""},
             "To pole jest wymagane."),
            ("Not unique field: attachment_name", "attachment_name",
             {"attachment_name": "ABCD name", "access_granted": "Brak dostępu"},
             "Istnieje już załącznik o podanej nazwie w bazie danych.")
        ]
    )
    def test_attachment_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        attachment_names = ["ABCD name"]
        form = AttachmentForm(data=payload, attachment_names=attachment_names)
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, dict(form.errors)[field])
