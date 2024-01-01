import datetime
import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.test import TestCase
from parameterized import parameterized


from trip.factories import (TripFactory, TripReportFactory, TripBasicFactory,
                            TripAdvancedFactory, TripCostFactory,
                            TripAdditionalInfoFactory, TripPersonalChecklistFactory)
from trip.forms import (TripForm, TripReportForm, TripCostForm,
                        TripBasicChecklistForm, TripAdvancedChecklistForm,
                        TripPersonalChecklistForm, TripAdditionalInfoForm)


User = get_user_model()
logger = logging.getLogger("test")


class TripFormTests(TestCase):
    """Tests for TripForm class."""

    def setUp(self):
        self.trip = TripFactory()
        self.form = TripForm(trip_names=["Test name"])
        self.fields = [
            "name",
            "type",
            "destination",
            "start_date",
            "end_date",
            "transport",
            "estimated_cost",
            "participants_number",
            "participants",
            "reservations",
            "notes",
            "access_granted",
        ]

    def test_trip_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_trip_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa podróży"))
        self.assertEqual(self.form.fields["type"].label, _("Rodzaj podróży"))
        self.assertEqual(self.form.fields["destination"].label,
                         _("Miejsce podróży"))
        self.assertEqual(self.form.fields["start_date"].label,
                         _("Rozpoczęcie wyjazdu"))
        self.assertEqual(self.form.fields["end_date"].label,
                         _("Zakończenie wyjazdu"))
        self.assertEqual(self.form.fields["transport"].label,
                         _("Środki transportu"))
        self.assertEqual(self.form.fields["estimated_cost"].label,
                         _("Szacunkowy koszt podróży"))
        self.assertEqual(self.form.fields["participants_number"].label,
                         _("Liczba osób na wyjeździe"))
        self.assertEqual(self.form.fields["participants"].label,
                         _("Towarzysze podróży"))
        self.assertEqual(self.form.fields["reservations"].label,
                         _("Informacje o rezerwacjach"))
        self.assertEqual(self.form.fields["notes"].label, _("Uwagi"))
        self.assertEqual(self.form.fields["access_granted"].label,
                         _("Dostęp do danych"))

    def test_trip_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Pole wymagane."))
            elif field == "start_date" or field == "end_date":
                self.assertEqual(self.form.fields["start_date"].help_text,
                                 self.form.fields["end_date"].help_text, _(
                        "Format: YYYY-MM-DD (np. 2020-07-21)."))
            elif field == "access_granted":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać te dane."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_trip_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "start_date" or field == "end_date":
                self.assertEqual(self.form.fields[field].error_messages,
                                 {"required": "To pole jest wymagane.",
                                  "invalid": "Wpisz poprawną datę."})
            elif field == "type":
                self.assertEqual(self.form.fields[field].error_messages,
                                 {"required": "To pole jest wymagane.",
                                  "invalid_choice": "Wybierz poprawną wartość. "
                                                    "%(value)s nie jest żadną z "
                                                    "dostępnych opcji.",
                                  "invalid_list": "Podaj listę wartości."})
            elif field == "estimated_cost" or field == "participants_number":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz liczbę całkowitą."})
            elif field == "access_granted":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid_choice": "Wybierz poprawną wartość. %(value)s nie "
                                      "jest żadną z dostępnych opcji."})
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane."})

    def test_trip_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
            "destination",
            "transport",
        ]
        textareas = [
            "participants",
            "reservations",
            "notes"
        ]
        for charfield in charfields:
            self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "TextInput")
        for textarea in textareas:
            self.assertEqual(self.form.fields[
                       textarea].widget.__class__.__name__, "Textarea")
        self.assertEqual(self.form.fields[
                   "type"].widget.__class__.__name__, "CheckboxSelectMultiple")
        self.assertEqual(self.form.fields["participants_number"].widget.__class__.__name__,
                         self.form.fields["estimated_cost"].widget.__class__.__name__,
                         "NumberInput")
        self.assertEqual(
            self.form.fields["start_date"].widget.__class__.__name__,
            self.form.fields["end_date"].widget.__class__.__name__,
            "DateInput"
        )
        self.assertEqual(self.form.fields["access_granted"].widget.__class__.__name__,
                         "Select")

    def test_trip_clean_method_start_date_validation(self):
        """
        Test if clean method validates start_date data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "name": "Some trip",
            "start_date": "2020,11,11",
            "access_granted": "Brak dostępu",
        }
        form = TripForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["start_date"])

    def test_trip_clean_method_end_date_validation(self):
        """
        Test if clean method validates end_date data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "name": "Some trip",
            "start_date": datetime.date(2020, 10, 15),
            "end_date": "2020,11,11",
            "access_granted": "Brak dostępu",
        }
        form = TripForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["end_date"])

    def test_trip_clean_method_start_and_end_date_validation(self):
        """
        Test if clean method validates start_date and end_date data type correctly.
        End date cannot happen before start date.
        """
        payload = {
            "name": "Some trip",
            "start_date": datetime.date(2020, 10, 15),
            "end_date": datetime.date(2020, 10, 10),
            "access_granted": "Brak dostępu",
        }
        form = TripForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Data zakończenia podróży nie może przypadać wcześniej "
                      "niż data jej rozpoczęcia.", form.errors["end_date"])

    def test_trip_clean_method_not_unique_name_validation(self):
        """Test if clean method validates if name field is always
        unique for one user."""
        payload = {
            "name": "Test name",
            "access_granted": "Brak dostępu",
        }
        form = TripForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już podróż o podanej nazwie w bazie danych. "
                      "Podaj inną nazwę.", form.errors["name"])

    def test_trip_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "name": "New trip",
            "type": ["Wyjazd na ryby"],
            "destination": "Jezioro",
            "start_date": datetime.date(2020, 2, 2),
            "end_date": datetime.date(2020, 2, 12),
            "transport": "Car",
            "estimated_cost": 222,
            "participants_number": 2,
            "participants": "Me and myself",
            "reservations": "Camping",
            "notes": None,
            "access_granted": "Udostępnij dane",
        }
        form = TripForm(data=payload, trip_names=["Test name"])
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Not unique name field", "name",
             {"name": "Test name", "type": ["Wyjazd na ryby"],
              "access_granted": "Udostępnij dane"},
             "Istnieje już podróż o podanej nazwie w bazie danych. "
             "Podaj inną nazwę."),
            ("Empty name field", "name",
             {"name": "", "type": ["Wyjazd na ryby"],
              "access_granted": "Udostępnij dane"},
             "To pole jest wymagane."),
            ("Invalid field 'type' (not in form of a list)", "type",
             {"name": "Trip name", "type": "Wyjazd na ryby",
              "access_granted": "Udostępnij dane"}, "Podaj listę wartości."),
            ("Invalid field 'start_date' or 'end_date' (incorrect date form)",
             "start_date",
             {"name": "Trip name", "type": ["Wyjazd na ryby"],
              "start_date": "2020,11,11",
              "access_granted": "Udostępnij dane"}, "Wpisz poprawną datę."),
        ]
    )
    def test_trip_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = TripForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])


class TripReportFormTests(TestCase):
    """Tests for TripReportForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="trip_report",
            email="tr@example.com",
            password="testpass123"
        )
        self.trip_report = TripReportFactory(user=self.user)
        self.form = TripReportForm()        # !
        self.fields = [
            "start_date",
            "end_date",
            "description",
            "notes",
            "facebook",
            "youtube",
            "instagram",
            "pinterest",
            "link",
        ]

    def test_trip_report_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_trip_report_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["start_date"].label,
                         _("Rozpoczęcie relacji"))
        self.assertEqual(self.form.fields["end_date"].label,
                         _("Zakończenie relacji"))
        self.assertEqual(self.form.fields["description"].label, _("Opis"))
        self.assertEqual(self.form.fields["notes"].label, _("Uwagi"))
        self.assertEqual(self.form.fields["facebook"].label,
                         _("Facebook link"))
        self.assertEqual(self.form.fields["youtube"].label,
                         _("Youtube link"))
        self.assertEqual(self.form.fields["instagram"].label,
                         _("Instagram link"))
        self.assertEqual(self.form.fields["pinterest"].label,
                         _("Pinterest link"))
        self.assertEqual(self.form.fields["link"].label,
                         _("Link do relacji"))

    def test_trip_report_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field == "start_date" or field == "end_date":
                self.assertEqual(self.form.fields["start_date"].help_text,
                                 self.form.fields["end_date"].help_text,
                                 _("Format: YYYY-MM-DD (np. 2020-07-21)."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_trip_report_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "start_date" or field == "end_date":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz poprawną datę.",
                })
            elif field == "notes" or field == "description":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    'invalid': 'Wpisz poprawny URL.',
                })

    def test_trip_report_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "notes",
            "description",
        ]
        urlfields = [
            "facebook",
            "youtube",
            "instagram",
            "pinterest",
            "link",
        ]
        for charfield in charfields:
            self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "Textarea")
        for urlfield in urlfields:
            self.assertEqual(self.form.fields[
                       urlfield].widget.__class__.__name__, "URLInput")
        self.assertEqual(
            self.form.fields["start_date"].widget.__class__.__name__,
            self.form.fields["end_date"].widget.__class__.__name__, "DateInput"
        )

    def test_trip_report_clean_method_start_date_validation(self):
        """
        Test if clean method validates start_date data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "start_date": "2020,11,11",
            "end_date": datetime.date(2020, 10, 10),
        }
        form = TripReportForm(data=payload)
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["start_date"])

    def test_trip_report_clean_method_end_date_validation(self):
        """
        Test if clean method validates end_date data type correctly.
        Correct format: datetime.date.
        """
        payload = {
            "start_date": datetime.date(2020, 10, 15),
            "end_date": "2020,11,11",
        }
        form = TripReportForm(data=payload)
        self.assertFalse(form.is_valid())
        self.assertIn("Wpisz poprawną datę.", form.errors["end_date"])

    def test_trip_report_clean_method_start_and_end_date_validation(self):
        """
        Test if clean method validates start_date and end_date data type correctly.
        End date cannot happen before start date.
        """
        payload = {
            "start_date": datetime.date(2020, 10, 15),
            "end_date": datetime.date(2020, 10, 10),
        }
        form = TripReportForm(data=payload)
        self.assertFalse(form.is_valid())
        self.assertIn("Data zakończenia relacji nie może przypadać wcześniej "
                      "niż data jej rozpoczęcia.", form.errors["end_date"])

    def test_trip_report_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "trip": self.trip_report.trip,
            # "start_date": datetime.date(2020,2,2),
            # "end_date": datetime.date(2020,2,12),
            "description": "Some descr",
            "notes": None,
            "facebook": None,
            "youtube": "https://www.youtube.com/",
            "instagram": "https://www.instagram.com/",
            "pinterest": None,
            "link": None,
        }
        form = TripReportForm(data=payload)  # !
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Invalid field 'start_date'", "start_date",
             {"start_date": "2020,11,11"}, "Wpisz poprawną datę."),
            ("Invalid field 'end_date' (incorrect date form)", "end_date",
             {"end_date": "2020,11,11"}, "Wpisz poprawną datę."),
            ("Invalid url address", "link", {"link": "Invalid"},
             "Wpisz poprawny URL."),
        ]
    )
    def test_trip_report_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = TripReportForm(data=payload)
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])


class TripBasicFormTests(TestCase):
    """Tests for TripBasicForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="trip_report",
            email="tr@example.com",
            password="testpass123"
        )
        self.trip = TripBasicFactory(user=self.user)
        self.form = TripBasicChecklistForm(trip_names=["Test name"])
        self.fields = [
            "name",
            "wallet",
            "keys",
            "cosmetics",
            "electronics",
            "useful_stuff",
            "basic_drugs",
            "additional_drugs",
        ]

    def test_trip_basic_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_trip_basic_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["wallet"].label, _("Portfel"))
        self.assertEqual(self.form.fields["keys"].label, _("Klucze"))
        self.assertEqual(self.form.fields["cosmetics"].label, _("Kosmetyki"))
        self.assertEqual(self.form.fields["electronics"].label, _("Elektronika"))
        self.assertEqual(self.form.fields["useful_stuff"].label, _("Użyteczne rzeczy"))
        self.assertEqual(self.form.fields["basic_drugs"].label, _("Podstawowe leki"))
        self.assertEqual(self.form.fields["additional_drugs"].label, _("Dodatkowe leki"))

    def test_trip_basic_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            self.assertEqual(self.form.fields[field].help_text, "")

    def test_trip_basic_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "name" or field == "basic_drugs" or field == "additional_drugs":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    'invalid_choice': 'Wybierz poprawną wartość. '
                                      '%(value)s nie jest żadną z dostępnych opcji.',
                    'invalid_list': 'Podaj listę wartości.'
                })

    def test_trip_basic_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
            "basic_drugs",
            "additional_drugs"
        ]
        choicefields = [
            "wallet",
            "keys",
            "cosmetics",
            "electronics",
            "useful_stuff",
        ]
        for charfield in charfields:
            if charfield == "name":
                self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "TextInput")
            else:
                self.assertEqual(self.form.fields[
                           charfield].widget.__class__.__name__, "Textarea")
        for choicefield in choicefields:
            self.assertEqual(self.form.fields[
                       choicefield].widget.__class__.__name__, "CheckboxSelectMultiple")

    def test_trip_clean_method_name_validation(self):
        """Test if clean method validates is name field is always unique for one user."""
        payload = {
            "name": "Test name",
        }
        form = TripBasicChecklistForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już wyposażenie o podanej nazwie w bazie danych. "
                      "Podaj inną nazwę.", form.errors["name"])

    def test_trip_basic_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "trip": self.trip.trip,
            "name": "Basic trip",
            "wallet": ["Winiety", "Waluta", "Ubezpieczenie"],
            "keys": ["Rower", "Bagażnik"],
            "cosmetics": None,
            "electronics": None,
            "useful_stuff": ["Parasol"],
            "basic_drugs": "wit. c, apap",
            "additional_drugs": None,

        }
        form = TripBasicChecklistForm(data=payload, trip_names=["Test name"])
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Invalid name (not unique)", "name",
             {"name": "Test name"},
             "Istnieje już wyposażenie o podanej nazwie w bazie danych. "
             "Podaj inną nazwę."),
            ("Invalid choice field (out of list)", "wallet",
             {"name": "Basic trip", "wallet": ["Kremówki"]},
             "Wybierz poprawną wartość. Kremówki nie jest żadną z dostępnych opcji."),
        ]
    )
    def test_trip_basic_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = TripBasicChecklistForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])


class TripAdvancedFormTests(TestCase):
    """Tests for TripAdvancedForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="trip_report",
            email="tr@example.com",
            password="testpass123"
        )
        self.trip = TripAdvancedFactory(user=self.user)
        self.form = TripAdvancedChecklistForm(trip_names=["Test name"])
        self.fields = [
            "name",
            "trekking",
            "hiking",
            "cycling",
            "camping",
            "fishing",
            "sunbathing",
            "business",
        ]

    def test_trip_advanced_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_trip_advanced_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["trekking"].label, _("Trekking"))
        self.assertEqual(self.form.fields["hiking"].label, _("Wspinaczka"))
        self.assertEqual(self.form.fields["cycling"].label, _("Rower"))
        self.assertEqual(self.form.fields["camping"].label, _("Camping"))
        self.assertEqual(self.form.fields["fishing"].label, _("Wędkarstwo"))
        self.assertEqual(self.form.fields["sunbathing"].label, _("Plażowanie"))
        self.assertEqual(self.form.fields["business"].label, _("Wyjazd służbowy"))

    def test_trip_advanced_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            self.assertEqual(self.form.fields[field].help_text, "")

    def test_trip_advanced_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    'invalid_choice': 'Wybierz poprawną wartość. '
                                      '%(value)s nie jest żadną z dostępnych opcji.',
                    'invalid_list': 'Podaj listę wartości.'
                })

    def test_trip_advanced_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
        ]
        choicefields = [
            "trekking",
            "hiking",
            "cycling",
            "camping",
            "fishing",
            "sunbathing",
            "business",
        ]
        for charfield in charfields:
            self.assertEqual(self.form.fields[
                   charfield].widget.__class__.__name__, "TextInput")
        for choicefield in choicefields:
            self.assertEqual(self.form.fields[
                       choicefield].widget.__class__.__name__, "CheckboxSelectMultiple")

    def test_trip_clean_method_name_validation(self):
        """Test if clean method validates is name field is always unique for one user."""
        payload = {
            "name": "Test name",
        }
        form = TripAdvancedChecklistForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już wyposażenie o podanej nazwie w bazie danych. "
                      "Podaj inną nazwę.", form.errors["name"])

    def test_trip_advanced_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "trip": self.trip.trip,
            "name": "Advanced trip",
            "trekking": ["Mapy", "Siedzisko", "Kask"],
            "hiking": ["Liny", "Magnezja"],
            "cycling": None,
            "camping": None,
            "fishing": ["Przynęty"],
            "sunbathing": ["Klapki"],
            "business": None,

        }
        form = TripAdvancedChecklistForm(data=payload, trip_names=["Test name"])
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Invalid name (not unique)", "name",
             {"name": "Test name"}, "Istnieje już wyposażenie o podanej "
                                    "nazwie w bazie danych. Podaj inną nazwę."),
            ("Invalid choice field (not a list)", "sunbathing",
             {"name": "Basic trip", "sunbathing": "Klapki"}, "Podaj listę wartości."),
            ("Invalid choice field (out of a list)", "sunbathing",
             {"name": "Basic trip", "sunbathing": ["Zmywacz"]},
             "Wybierz poprawną wartość. Zmywacz nie jest żadną z dostępnych opcji."),
        ]
    )
    def test_trip_advanced_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = TripAdvancedChecklistForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])


class TripPersonalChecklistFormTests(TestCase):
    """Tests for TripPersonalChecklistForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="trip_report",
            email="tr@example.com",
            password="testpass123"
        )
        self.trip = TripPersonalChecklistFactory(user=self.user)
        self.form = TripPersonalChecklistForm(trip_names=["Test name"])
        self.fields = [
            "name",
            "checklist",
        ]

    def test_trip_personal_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_trip_personal_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["checklist"].label, _("Lista"))

    def test_trip_personal_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane."))
            else:
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Elementy listy oddzielaj przecinkami lub "
                                   "średnikami."))

    def test_trip_personal_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            self.assertEqual(self.form.fields[field].error_messages, {
                "required": "To pole jest wymagane."})

    def test_trip_personal_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
            "checklist"
        ]
        for charfield in charfields:
            if charfield == "name":
                self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "TextInput")
            else:
                self.assertEqual(self.form.fields[
                           charfield].widget.__class__.__name__, "Textarea")

    def test_trip_clean_method_name_validation(self):
        """Test if clean method validates is name field is always unique for one user."""
        payload = {
            "name": "Test name",
        }
        form = TripPersonalChecklistForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już lista o podanej nazwie w bazie danych. "
                      "Podaj inną nazwę.", form.errors["name"])

    def test_trip_personal_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "trip": self.trip.trip,
            "name": "Personal trip",
            "checklist": "XYZ",
        }
        form = TripPersonalChecklistForm(data=payload, trip_names=["Test name"])
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Invalid name (not unique)", "name",
             {"name": "Test name"},
             "Istnieje już lista o podanej nazwie w bazie danych. "
             "Podaj inną nazwę."),
            ("Empty name field", "name", {"name": None},
             "To pole jest wymagane."),
        ]
    )
    def test_trip_personal_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = TripPersonalChecklistForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])


class TripAdditionalInfoFormTests(TestCase):
    """Tests for TripAdditionalInfoForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="trip_report",
            email="tr@example.com",
            password="testpass123"
        )
        self.trip = TripAdditionalInfoFactory(user=self.user)
        self.form = TripAdditionalInfoForm(trip_names=["Test name"])
        self.fields = [
            "name",
            "info",
            "notes"
        ]

    def test_trip_additional_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_trip_additional_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["info"].label, _("Opis"))
        self.assertEqual(self.form.fields["notes"].label, _("Uwagi"))

    def test_trip_additional_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_trip_additional_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            self.assertEqual(self.form.fields[field].error_messages, {
                "required": "To pole jest wymagane.",
            })

    def test_trip_additional_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
            "info",
            "notes"
        ]
        for charfield in charfields:
            if charfield == "name":
                self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "TextInput")
            else:
                self.assertEqual(self.form.fields[
                           charfield].widget.__class__.__name__, "Textarea")

    def test_trip_clean_method_name_validation(self):
        """Test if clean method validates is name field is always unique for one user."""
        payload = {
            "name": "Test name",
        }
        form = TripAdditionalInfoForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już element o podanej nazwie w bazie danych. "
                      "Podaj inną nazwę.", form.errors["name"])

    def test_trip_additional_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "trip": self.trip.trip,
            "name": "Additional trip",
            "info": "XYZ",
            "notes": "XYZ",
        }
        form = TripAdditionalInfoForm(data=payload, trip_names=["Test name"])
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Invalid name (not unique)", "name",
             {"name": "Test name"}, "Istnieje już element o podanej nazwie w "
                                    "bazie danych. Podaj inną nazwę."),
            ("Empty name field", "name",
             {"name": ""}, "To pole jest wymagane."),
        ]
    )
    def test_trip_additional_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_meg: str):
        """Test if form is not valid with invalid data."""
        form = TripAdditionalInfoForm(data=payload, trip_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn(error_meg, form.errors[field])


class TripCostFormTests(TestCase):
    """Tests for TripCostForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="trip_report",
            email="tr@example.com",
            password="testpass123"
        )
        self.trip = TripCostFactory(user=self.user)
        self.form = TripCostForm()
        self.fields = [
            "name",
            "cost_group",
            "cost_paid",
            "currency",
            "exchange_rate",
            "notes",
        ]

    def test_trip_cost_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_trip_cost_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["cost_group"].label, _("Grupa kosztów"))
        self.assertEqual(self.form.fields["cost_paid"].label, _("Wysokość wydatku"))
        self.assertEqual(self.form.fields["currency"].label, _("Waluta"))
        self.assertEqual(self.form.fields["exchange_rate"].label, _("Kurs wymiany waluty"))
        self.assertEqual(self.form.fields["notes"].label, _("Uwagi"))

    def test_trip_cost_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field in ["name", "exchange_rate", "cost_paid", "cost_group"]:
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_trip_cost_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })
            elif field == "cost_group":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid_choice": "Wybierz poprawną wartość. "
                                      "%(value)s nie jest żadną z dostępnych opcji.",
                })
            elif field == "cost_paid":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz liczbę."
                })
            elif field == "exchange_rate":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz liczbę.",
                    "invalid_value": "Wartość kursu walutowego nie może być ujemna."
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_trip_cost_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
            "currency",
            "notes",
        ]
        decimalfields = [
            "cost_paid",
            "exchange_rate"
        ]
        for charfield in charfields:
            if charfield == "name" or charfield == "currency":
                self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "TextInput")
            else:
                self.assertEqual(self.form.fields[
                           charfield].widget.__class__.__name__, "Textarea")
        for decimalfield in decimalfields:
            self.assertEqual(self.form.fields[
                   decimalfield].widget.__class__.__name__, "NumberInput")
        self.assertEqual(self.form.fields[
                   "cost_group"].widget.__class__.__name__, "Select")

    def test_trip_cost_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "trip": self.trip.trip,
            "name": "Cost trip",
            "cost_group": "Paliwo",
            "cost_paid": 111,
            "currency": "USD",
            "exchange_rate": 4.2000,
            "notes": None,
        }
        form = TripCostForm(data=payload)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Empty name field", "name",
             {"name": "", "cost_group": "Paliwo", "cost_paid": 222,
              "exchange_rate": 1}, "To pole jest wymagane."),
            ("Empty cost_group field", "cost_group",
             {"name": "Some new name", "cost_group": "", "cost_paid": 222,
              "exchange_rate": 1}, "To pole jest wymagane."),
            ("Empty exchange_rate field", "exchange_rate",
             {"name": "Test name", "cost_group": "Paliwo", "cost_paid": 222,
              "exchange_rate": ""}, "To pole jest wymagane."),
            ("Invalid cost group (out of list)", "cost_group",
             {"name": "Cost name", "cost_group": "Używki", "cost_paid": 222,
              "exchange_rate": 1},
             "Wybierz poprawną wartość. Używki nie jest żadną z dostępnych opcji."),
            ("Negative value of exchange rate", "exchange_rate",
             {"name": "Cost name", "cost_group": "Paliwo", "cost_paid": 222,
              "exchange_rate": -2.500},
             "Wartość kursu walutowego nie może być ujemna."),
        ]
    )
    def test_trip_cost_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = TripCostForm(data=payload)
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])
