import datetime
import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.test import TestCase
from parameterized import parameterized

from credit.factories import (CreditFactory, CreditAdditionalCostFactory,
                              CreditCollateralFactory, CreditInsuranceFactory,
                              CreditInterestRateFactory, CreditTrancheFactory,
                              CreditEarlyRepaymentFactory)
from credit.forms import (CreditForm, CreditInsuranceForm,
                          CreditCollateralForm, CreditTrancheForm,
                          CreditInterestRateForm, CreditAdditionalCostForm,
                          CreditEarlyRepaymentForm)
from credit.models import (Credit, CreditAdditionalCost, CreditCollateral,
                           CreditInsurance, CreditInterestRate, CreditTranche,
                           CreditEarlyRepayment)
from user.factories import UserFactory

User = get_user_model()
logger = logging.getLogger("test")


class CreditFormTests(TestCase):
    """Tests for CreditForm class."""

    def setUp(self):
        self.credit = CreditFactory()
        self.user = self.credit.user
        self.form = CreditForm(credit_names=["Credit name"])
        self.fields = [
            "name",
            "credit_number",
            "type",
            "currency",
            "credit_amount",
            "own_contribution",
            "market_value",
            "credit_period",
            "grace_period",
            "installment_type",
            "installment_frequency",
            "total_installment",
            "capital_installment",
            "type_of_interest",
            "fixed_interest_rate",
            "floating_interest_rate",
            "bank_margin",
            "interest_rate_benchmark",
            "date_of_agreement",
            "start_of_credit",
            "start_of_payment",
            "payment_day",
            "provision",
            "credited_provision",
            "tranches_in_credit",
            "life_insurance_first_year",
            "property_insurance_first_year",
            "collateral_required",
            "collateral_rate",
            "notes",
            "access_granted",
            "access_granted_for_schedule",
        ]
        self.payload = {
            "user": self.user,
            "name": "New credit",
            "type": _("Samochodowy"),
            "currency": "PLN",
            "credit_amount": 10000,
            "credit_period": 20,
            "grace_period": 0,
            "installment_type": _("Raty malejące"),
            "installment_frequency": _("Miesięczne"),
            "total_installment": 0,
            "capital_installment": 500,
            "type_of_interest": _("Zmienne"),
            "fixed_interest_rate": 0,
            "floating_interest_rate": 5,
            "bank_margin": 1,
            "date_of_agreement": datetime.date(2020, 1, 10),
            "start_of_credit": datetime.date(2020, 1, 13),
            "start_of_payment": datetime.date(2020, 3, 7),
            "payment_day": 7,
            "provision": 0,
            "credited_provision": _("Nie"),
            "tranches_in_credit": _("Nie"),
            "collateral_required": _("Nie"),
            "collateral_rate": 0,
            "access_granted": _("Brak dostępu"),
            "access_granted_for_schedule": _("Brak dostępu"),
        }

    def test_credit_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_credit_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa kredytu"))
        self.assertEqual(self.form.fields["credit_number"].label, _("Numer umowy kredytu"))
        self.assertEqual(self.form.fields["type"].label, _("Rodzaj kredytu"))
        self.assertEqual(self.form.fields["currency"].label, _("Waluta"))
        self.assertEqual(self.form.fields["credit_amount"].label, _("Wartość kredytu"))
        self.assertEqual(self.form.fields["own_contribution"].label, _("Wkład własny"))
        self.assertEqual(self.form.fields["market_value"].label, _("Wartość rynkowa nabywanej rzeczy/nieruchomości"))
        self.assertEqual(self.form.fields["credit_period"].label, _("Okres kredytowania (w miesiącach)"))
        self.assertEqual(self.form.fields["grace_period"].label, _("Okres karencji (w miesiącach)"))
        self.assertEqual(self.form.fields["installment_type"].label, _("Rodzaj raty"))
        self.assertEqual(self.form.fields["installment_frequency"].label, _("Częstotliwość płatności raty"))
        self.assertEqual(self.form.fields["total_installment"].label, _("Wysokość raty całkowitej (dla rat równych)"))
        self.assertEqual(self.form.fields["capital_installment"].label, _("Wysokość raty kapitałowej (dla rat malejących)"))
        self.assertEqual(self.form.fields["type_of_interest"].label, _("Rodzaj oprocentowania"))
        self.assertEqual(self.form.fields["fixed_interest_rate"].label, _("Wysokość oprocentowania stałego (w %)"))
        self.assertEqual(self.form.fields["floating_interest_rate"].label, _("Wysokość oprocentowania zmiennego (w %)"))
        self.assertEqual(self.form.fields["bank_margin"].label, _("Marża banku w oprocentowaniu zmiennym (w %)"))
        self.assertEqual(self.form.fields["interest_rate_benchmark"].label, _("Rodzaj benchmarku"))
        self.assertEqual(self.form.fields["date_of_agreement"].label, _("Data zawarcia umowy"))
        self.assertEqual(self.form.fields["start_of_credit"].label, _("Data uruchomienia kredytu"))
        self.assertEqual(self.form.fields["start_of_payment"].label, _("Data rozpoczęcia spłaty kredytu"))
        self.assertEqual(self.form.fields["payment_day"].label, _("Dzień płatności raty"))
        self.assertEqual(self.form.fields["provision"].label, _("Wysokość prowizji (w wybranej walucie)"))
        self.assertEqual(self.form.fields["credited_provision"].label, _("Kredytowanie prowizji"))
        self.assertEqual(self.form.fields["tranches_in_credit"].label, _("Transzowanie wypłat"))
        self.assertEqual(self.form.fields["life_insurance_first_year"].label, _("Kredytowane ubezpieczenie na życie"))
        self.assertEqual(self.form.fields["property_insurance_first_year"].label, _("Kredytowane ubezpieczenie rzeczy/nieruchomości"))
        self.assertEqual(self.form.fields["collateral_required"].label, _("Wymagane zabezpieczenie kredytu"))
        self.assertEqual(self.form.fields["collateral_rate"].label, _("Oprocentowanie dodatkowe (pomostowe)"))
        self.assertEqual(self.form.fields["notes"].label, _("Uwagi"))
        self.assertEqual(self.form.fields["access_granted"].label, _("Dostęp do danych"))
        self.assertEqual(self.form.fields["access_granted_for_schedule"].label, _("Dostęp do harmonogramu"))

    def test_credit_form_help_text(self):
        """Test if fields have correct help text."""
        for field in ["name", "credit_amount", "payment_day"]:
            self.assertEqual(self.form.fields[field].help_text,
                             _("Pole wymagane."))
        self.assertEqual(self.form.fields["own_contribution"].help_text,
                         _("Nie wlicza się do wartości kredytu."))
        self.assertEqual(self.form.fields["credit_period"].help_text,
                         _("Liczba miesięcy, po której następuje spłata "
                           "kredytu (łącznie z karencją). Pole wymagane."))
        self.assertEqual(self.form.fields["total_installment"].help_text,
                         _("Podaj wysokość raty (zero dla rat malejących). "
                           "Pole wymagane."))
        self.assertEqual(self.form.fields["capital_installment"].help_text,
                         _("Podaj wysokość raty (zero dla rat równych). "
                           "Pole wymagane."))
        self.assertEqual(self.form.fields["fixed_interest_rate"].help_text,
                         _("Wysokość oprocentowania razem z marżą banku. "
                           "Wpisz zero jeśli nie dotyczy. Pole wymagane."))
        self.assertEqual(self.form.fields["floating_interest_rate"].help_text,
                         _("Wysokość w dniu zawarcia umowy (bez marży banku). "
                           "Wpisz zero jeśli nie dotyczy. Pole wymagane."))
        self.assertEqual(self.form.fields["bank_margin"].help_text,
                         _("Np. wartość 5.5 oznacza 5,5%. Wpisz zero jeśli "
                           "nie dotyczy. Pole wymagane."))
        self.assertEqual(self.form.fields["interest_rate_benchmark"].help_text,
                         _("Przykładowo: WIBOR 3M, EURIBOR 6M."))
        self.assertEqual(self.form.fields["date_of_agreement"].help_text,
                         _("Format: YYYY-MM-DD (np. 2020-07-21). "
                           "Pole wymagane."))
        self.assertEqual(self.form.fields["start_of_payment"].help_text,
                         _("Data płatności pierwszej raty. Format: "
                           "YYYY-MM-DD (np. 2020-07-21). Pole wymagane."))
        self.assertEqual(self.form.fields["start_of_credit"].help_text,
                         _("Data wypłaty środków lub uruchomienia pierwszej "
                           "transzy kredytu. Format: ""YYYY-MM-DD "
                           "(np. 2020-07-21). Pole wymagane."))
        self.assertEqual(self.form.fields["date_of_agreement"].help_text,
                         _("Format: YYYY-MM-DD (np. 2020-07-21). "
                           "Pole wymagane."))
        self.assertEqual(self.form.fields["provision"].help_text,
                         _("Płatna w dniu uruchomienia kredytu."))
        for field in ["life_insurance_first_year", "property_insurance_first_year"]:
            self.assertEqual(self.form.fields[field].help_text,
                             _("Roczna składka za 1. rok. Kredytowane w "
                               "dniu uruchomienia kredytu."))
        self.assertEqual(self.form.fields["collateral_rate"].help_text,
                         _("Dodatkowe oprocentowanie do czasu ustanowienia "
                           "zabezpieczenia kredytu."))
        self.assertEqual(self.form.fields["access_granted_for_schedule"].help_text,
                         _("Użytkownik upoważniony do dostępu do danych "
                           "może przeglądać harmonogram kredytu."))
        self.assertEqual(self.form.fields["access_granted"].help_text,
                         _("Użytkownik upoważniony do dostępu do danych "
                           "może przeglądać te dane."))

    def test_credit_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field in ["type", "currency", "installment_type",
                         "installment_frequency", "type_of_interest",
                         "payment_day", "credited_provision",
                         "tranches_in_credit", "collateral_required"]:
                self.assertEqual(
                    self.form.fields[field].error_messages,
                    {"required": "To pole jest wymagane.",
                     "invalid_choice": "Wybierz poprawną wartość. %(value)s nie "
                                       "jest żadną z dostępnych opcji."}
                )
            elif field in ["credit_amount", "total_installment",
                           "capital_installment", "fixed_interest_rate",
                           "floating_interest_rate", "bank_margin",
                           "own_contribution", "market_value", "provision",
                           "life_insurance_first_year", "collateral_rate",
                           "property_insurance_first_year"]:
                self.assertEqual(
                    self.form.fields[field].error_messages,
                    {"invalid": "Wpisz liczbę.",
                     "required": "To pole jest wymagane."}
                )
            elif field in ["credit_period", "grace_period"]:
                self.assertEqual(
                    self.form.fields[field].error_messages,
                    {"required": "To pole jest wymagane.",
                     "invalid": "Wpisz liczbę całkowitą."}
                )
            elif field in ["date_of_agreement", "start_of_credit",
                           "start_of_payment"]:
                self.assertEqual(self.form.fields[field].error_messages,
                                 {"required": "To pole jest wymagane.",
                                  "invalid": "Wpisz poprawną datę."})
            elif field in ["access_granted", "access_granted_for_schedule"]:
                self.assertEqual(
                    self.form.fields[field].error_messages,
                    {"required": "To pole jest wymagane.",
                     "invalid_choice": "Wybierz poprawną wartość. %(value)s nie "
                                       "jest żadną z dostępnych opcji."}
                )
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_credit_form_widgets(self):
        """Test if fields have correct widgets."""
        char_fields = ["name", "credit_number", "interest_rate_benchmark"]
        text_areas = ["notes"]
        select_fields = ["type", "currency", "installment_type",
                         "installment_frequency", "type_of_interest",
                         "payment_day", "credited_provision", "tranches_in_credit",
                         "collateral_required", "access_granted",
                         "access_granted_for_schedule"]
        decimal_fields = ["credit_amount", "own_contribution", "market_value",
                          "total_installment", "capital_installment",
                          "fixed_interest_rate", "floating_interest_rate",
                          "bank_margin", "provision", "life_insurance_first_year",
                          "property_insurance_first_year", "collateral_rate"]
        integer_fields = ["credit_period", "grace_period"]
        date_fields = ["date_of_agreement", "start_of_credit", "start_of_payment"]
        for field in char_fields:
            self.assertEqual(self.form.fields[
                       field].widget.__class__.__name__, "TextInput")
        for field in text_areas:
            self.assertEqual(self.form.fields[
                       field].widget.__class__.__name__, "Textarea")
        for field in integer_fields:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "NumberInput")
        for field in date_fields:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "DateInput")
        for field in select_fields:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "Select")
        for field in decimal_fields:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "NumberInput")

    def test_credit_clean_provision_method_credited_provision_without_value(self):
        """Clean method validates if provision amount is specified if user declared
        that provision is credited."""
        payload = self.payload
        payload["provision"] = 0
        payload["credited_provision"] = _("Tak")
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Nie można wskazać kredytowania prowizji bez podania "
                      "kwoty prowizji. Uzupełnij kwotę lub zmień warunki "
                      "kredytowe.", form.errors["provision"])

    def test_credit_clean_collateral_rate_method_collateral_rate_with_no_value(self):
        """Clean method validates that if collateral value is given without
        collateral_required set to 'NO' ('Nie') error is risen."""
        payload = self.payload
        payload["collateral_rate"] = 1.5
        payload["collateral_required"] = _("Nie")
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Nie można ustanowić oprocentowania dodatkowego "
                      "(pomostowego) bez wymaganego zabezpieczenia kredytu. "
                      "Zmień warunki kredytowe.", form.errors["collateral_required"])

    def test_credit_clean_total_installment_method_total_installment_with_no_value(self):
        """Clean method validates that if installment type is set to
        'Equal installments' ('Raty równe') then total installment is greater than zero."""
        payload = self.payload
        payload["installment_type"] = _("Raty równe")
        payload["total_installment"] = 0
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Podaj wartość raty całkowitej dla kredytu.",
                      form.errors["total_installment"])

    def test_credit_clean_capital_installment_method_capital_installment_with_no_value(self):
        """Clean method validates that if installment type is set to
        'Decreasing installments' ('Raty malejące') then capital installment
        is greater than zero."""
        payload = self.payload
        payload["installment_type"] = _("Raty malejące")
        payload["capital_installment"] = 0
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Podaj wartość raty kapitałowej dla kredytu.",
                      form.errors["capital_installment"])

    def test_credit_clean_fixed_interest_rate_method_fixed_interest_rate_greater_than_zero(self):
        """Clean method validates that if type of interest is set to
        'Floating' ('Zmienne') then fixed interest rate is equal to zero."""
        payload = self.payload
        payload["type_of_interest"] = _("Zmienne")
        payload["fixed_interest_rate"] = 3.3
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Przy wyborze zmiennego oprocentowania wysokość "
                      "oprocentowania stałego powinna wynosić zero.",
                      form.errors["fixed_interest_rate"])

    def test_credit_clean_floating_interest_rate_method_floating_interest_rate_greater_than_zero(self):
        """Clean method validates that if type of interest is set to
        'Fixed' ('Stałe') then floating interest rate is equal to zero."""
        payload = self.payload
        payload["type_of_interest"] = _("Stałe")
        payload["floating_interest_rate"] = 3.3
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Przy wyborze stałego oprocentowania wysokość "
                      "oprocentowania zmiennego powinna wynosić zero.",
                      form.errors["floating_interest_rate"])

    def test_credit_clean_bank_margin_method_bank_margin_greater_than_zero(self):
        """Clean method validates that if type of interest is set to
        'Fixed' ('Stałe') then bank margin is equal to zero."""
        payload = self.payload
        payload["type_of_interest"] = _("Stałe")
        payload["bank_margin"] = 3.3
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Przy wyborze stałego oprocentowania wysokość "
                      "marży banku powinna wynosić zero.",
                      form.errors["bank_margin"])

    def test_credit_clean_access_granted_for_schedule_method(self):
        """User cannot set access to credit schedule if access to credit is
        not granted."""
        payload = self.payload
        payload["access_granted"] = _("Brak dostępu")
        payload["access_granted_for_schedule"] = _("Udostępnij dane")
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Nie można udzielić dostępu do harmonogramu kredytu bez "
                      "dostępu do danych kredytu.",
                      form.errors["access_granted_for_schedule"])

    def test_credit_date_of_agreement_later_than_current_date(self):
        """User cannot set date of agreement with later date than current date."""
        payload = self.payload
        payload["access_granted"] = _("Brak dostępu")
        payload["access_granted_for_schedule"] = _("Udostępnij dane")
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Nie można udzielić dostępu do harmonogramu kredytu bez "
                      "dostępu do danych kredytu.",
                      form.errors["access_granted_for_schedule"])

    def test_credit_start_of_credit_before_date_of_agreement(self):
        """User cannot set date of receiving credit before the date of agreement."""
        payload = self.payload
        payload["date_of_agreement"] = datetime.date(2020, 10, 10)
        payload["start_of_credit"] = datetime.date(2020, 8, 8)
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Data uruchomienia kredytu nie może przypadać wcześniej "
                      "niż data zawarcia umowy kredytu.",
                      form.errors["start_of_credit"])

    def test_credit_start_of_payment_before_start_of_credit(self):
        """User cannot set start of payment before date of receiving credit."""
        payload = self.payload
        payload["start_of_credit"] = datetime.date(2020, 8, 8)
        payload["start_of_payment"] = datetime.date(2020, 5, 5)
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Data rozpoczęcia spłaty kredytu nie może przypadać "
                      "wcześniej niż data uruchomienia kredytu.",
                      form.errors["start_of_payment"])

    def test_credit_start_of_payment_equal_start_of_credit(self):
        """User cannot set start of payment (date of first payment) at the same
        date as date of receiving credit."""
        payload = self.payload
        payload["start_of_credit"] = datetime.date(2020, 8, 8)
        payload["start_of_payment"] = datetime.date(2020, 8, 8)
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Data uruchomienia kredytu i data rozpoczęcia spłaty nie "
                      "mogą być sobie równe. Spłata kredytu następuje po jego "
                      "uruchomieniu.",
                      form.errors["start_of_payment"])

    def test_credit_start_of_payment_before_date_of_agreement(self):
        """User cannot set start of payment before the date of agreement."""
        payload = self.payload
        payload["date_of_agreement"] = datetime.date(2020, 10, 10)
        payload["start_of_payment"] = datetime.date(2020, 8, 8)
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Data rozpoczęcia spłaty nie może przypadać wcześniej "
                      "niż data zawarcia umowy.",
                      form.errors["start_of_payment"])

    @parameterized.expand(
        [
            ("Empty field 'name'", "name", "", "To pole jest wymagane."),
            ("Not unique name field", "name", "Credit test name",
             "Istnieje już kredyt o podanej nazwie w bazie danych. Podaj inną nazwę."),
            ("Empty field 'credit_amount'", "credit_amount", "", "To pole jest wymagane."),
            ("Invalid field 'credit_amount' (negative value is not allowed)",
             "credit_amount", -40000, "Wartość nie może być liczbą ujemną."),
            ("Invalid field 'own_contribution' (negative value is not allowed)",
             "own_contribution", -40000, "Wartość nie może być liczbą ujemną."),
            ("Invalid field 'market_value' (negative value is not allowed)",
             "market_value", -40000, "Wartość nie może być liczbą ujemną."),
            ("Invalid field 'bank_margin' (negative value is not allowed)",
             "bank_margin", -4.5, "Wartość nie może być liczbą ujemną."),
            ("Invalid field 'total_installment' (negative value is not allowed)",
             "total_installment", -1000, "Wartość nie może być liczbą ujemną."),
            ("Invalid field 'capital_installment' (negative value is not allowed)",
             "capital_installment", -1000, "Wartość nie może być liczbą ujemną."),
            ("Invalid field 'fixed_interest_rate' (negative value is not allowed)",
             "fixed_interest_rate", -3.3, "Wartość nie może być liczbą ujemną."),
            ("Invalid field 'floating_interest_rate' (negative value is not allowed)",
             "floating_interest_rate", -3.3, "Wartość nie może być liczbą ujemną."),
            ("Invalid field 'provision' (negative value is not allowed)",
             "provision", -5500, "Wartość nie może być liczbą ujemną."),
            ("Invalid field 'collateral_rate' (negative value is not allowed)",
             "collateral_rate", -40, "Wartość nie może być liczbą ujemną."),
            ("Empty field 'date_of_agreement'", "date_of_agreement", "",
             "To pole jest wymagane."),
            ("Invalid field 'date_of_agreement' (incorrect date form)",
             "date_of_agreement", "2020,11,23", "Wpisz poprawną datę."),
            ("Invalid field 'date_of_agreement' (date of agreement later than "
             "today's date)",  "date_of_agreement",
             datetime.date.today()+datetime.timedelta(days=2),
             "Data zawarcia umowy nie może być późniejsza niż bieżąca data."),
            ("Empty field 'start_of_credit'", "start_of_credit", "",
             "To pole jest wymagane."),
            ("Invalid field 'start_of_credit' (incorrect date form)",
             "start_of_credit", "2020,11,23", "Wpisz poprawną datę."),
            ("Empty field 'start_of_payment'", "start_of_payment", "",
             "To pole jest wymagane."),
            ("Invalid field 'start_of_payment' (incorrect date form)",
             "start_of_payment", "2020,11,23", "Wpisz poprawną datę."),
        ]
    )
    def test_credit_form_is_not_valid(self, name, field_name, field_value, error_msg):
        """Test if form is not valid with invalid data and error messages are correct."""
        payload = self.payload
        payload[field_name] = field_value
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field_name])

    def test_credit_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = self.payload
        form = CreditForm(data=payload, credit_names=["Credit test name"])
        # print("✅FORM", form)
        # logger.error("🛑 TEST CreditForm is valid error: %s" % form.errors)
        self.assertTrue(form.is_valid())


class CreditTrancheFormTests(TestCase):
    """Tests for CreditTrancheForm class."""

    def setUp(self):
        self.user = UserFactory()
        self.credit = CreditFactory(user=self.user)
        self.credit_tranche = CreditTrancheFactory(user=self.user, credit=self.credit)

        self.queryset = CreditTranche.objects.filter(credit=self.credit)
        self.sum_of_tranches = CreditTranche.total_tranche(self.queryset)
        self.dates_of_tranches = list(
            self.queryset.exclude(id=self.credit.id).values_list(
                "tranche_date", flat=True))
        self.form = CreditTrancheForm(
            credit=self.credit,
            queryset=self.queryset,
            sum_of_tranches=self.sum_of_tranches,
            dates_of_tranches=self.dates_of_tranches
        )

        self.fields = [
            "tranche_amount",
            "tranche_date",
            "total_installment",
            "capital_installment"
        ]
        self.payload = {
            "tranche_amount": 1234,
            "tranche_date": self.credit.start_of_credit,
            "total_installment": 0,
            "capital_installment": 1000,
        }

    def test_credit_tranche_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_credit_tranche_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["tranche_amount"].label,
                         _("Kwota transzy"))
        self.assertEqual(self.form.fields["tranche_date"].label,
                         _("Data wypłaty transzy"))
        self.assertEqual(self.form.fields["total_installment"].label,
                         _("Wysokość raty całkowitej (dla rat stałych)"))
        self.assertEqual(self.form.fields["capital_installment"].label,
                         _("Wysokość raty kapitałowej (dla rat malejących)"))

    def test_credit_tranche_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field in ["total_installment", "capital_installment"]:
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Brak informacji oznacza brak zmiany "
                                   "wysokości raty."))
        self.assertEqual(self.form.fields["tranche_amount"].help_text,
                         _("Wartość transzy bez wartości kredytowanych ubezpieczeń. "
                           "Pole wymagane."))
        self.assertEqual(self.form.fields["tranche_date"].help_text,
                         _("Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane."))

    def test_credit_tranche_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in ["tranche_amount", "capital_installment", "total_installment"]:
            self.assertEqual(self.form.fields[field].error_messages,
                             {"required": "To pole jest wymagane.",
                              "invalid": "Wpisz liczbę."})
        self.assertEqual(self.form.fields["tranche_date"].error_messages,
                         {"required": "To pole jest wymagane.",
                          "invalid": "Wpisz poprawną datę."})

    def test_credit_tranche_form_widgets(self):
        """Test if fields have correct widgets."""
        decimal_fields = [
            "tranche_amount",
            "total_installment",
            "capital_installment"
        ]
        for field in decimal_fields:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "NumberInput")
        self.assertEqual(self.form.fields["tranche_date"].widget.__class__.__name__,
                         "DateInput")

    def test_credit_tranche_clean_change_of_initial_tranche_date(self):
        """With credit with tranches user must set first initial tranche
        at the same date as start of credit. Change of that tranche date is not allowed."""
        payload = self.payload
        payload["tranche_date"] = self.credit.start_of_credit + datetime.timedelta(days=30)
        form = CreditTrancheForm(
            data=payload,
            credit=self.credit,
            queryset=self.queryset,
            sum_of_tranches=self.sum_of_tranches,
            dates_of_tranches=self.dates_of_tranches
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Nie można zmienić daty dla transzy inicjalnej. Jedna z "
                      "transz musi mieć datę zgodną z datą uruchomienia kredytu "
                      "(%s)." % self.credit.start_of_credit,
                      form.errors["tranche_date"])

    def test_credit_tranche_clean_initial_tranche_date_for_first_tranche(self):
        """With credit with tranches user must set first initial tranche
        at the same date as start of credit."""
        new_credit = CreditFactory(user=self.user,
                                   name="New credit with no tranches yet")
        queryset = CreditTranche.objects.filter(credit=new_credit)
        sum_of_tranches = CreditTranche.total_tranche(queryset)
        dates_of_tranches = list(
            queryset.exclude(id=new_credit.id).values_list(
                "tranche_date", flat=True))
        payload = self.payload
        payload["tranche_date"] = (new_credit.start_of_credit
                                   + datetime.timedelta(days=30))
        form = CreditTrancheForm(
            data=payload,
            credit=new_credit,
            queryset=queryset,
            sum_of_tranches=sum_of_tranches,
            dates_of_tranches=dates_of_tranches
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Data wypłaty pierwszej transzy musi być zgodna z datą "
                      "uruchomienia kredytu (%s)." % self.credit.start_of_credit,
                      form.errors["tranche_date"])

    def test_credit_tranche_clean_tranche_date_before_start_of_credit(self):
        """With credit with tranches no tranche can have date set before
         start of credit."""
        payload = self.payload
        payload["tranche_date"] = (self.credit.start_of_credit
                                   - datetime.timedelta(days=30))
        form = CreditTrancheForm(
            data=payload,
            credit=self.credit,
            queryset=self.queryset,
            sum_of_tranches=self.sum_of_tranches,
            dates_of_tranches=self.dates_of_tranches
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Data transzy nie może przypadać wcześniej niż data "
                      "uruchomienia kredytu.", form.errors["tranche_date"])

    def test_credit_tranche_clean_capital_installment_method(self):
        """If credit has 'equal installments' ('Raty równe') user cannot set
        capital installments with another tranche."""
        self.credit.installment_type = _("Raty równe")
        self.credit.capital_installment = 0
        self.credit.total_installment = 1000
        self.credit.save()
        payload = self.payload
        payload["capital_installment"] = 1000
        form = CreditTrancheForm(
            data=payload,
            credit=self.credit,
            queryset=self.queryset,
            sum_of_tranches=self.sum_of_tranches,
            dates_of_tranches=self.dates_of_tranches
        )
        self.assertFalse(form.is_valid())
        self.assertIn("W kredycie o ratach stałych (równych) nie można zmieniać "
                      "rat kapitałowych. Wprowadź raty całkowite lub zmień "
                      "warunki kredytu.", form.errors["capital_installment"])

    def test_credit_tranche_clean_total_installment_method(self):
        """If credit has 'decreasing installments' ('Raty malejące') user cannot
        set total installments with another tranche."""
        # self.credit has already set type_of_installment field as 'decreasing'
        payload = self.payload
        payload["total_installment"] = 1000
        form = CreditTrancheForm(
            data=payload,
            credit=self.credit,
            queryset=self.queryset,
            sum_of_tranches=self.sum_of_tranches,
            dates_of_tranches=self.dates_of_tranches
        )
        self.assertFalse(form.is_valid())
        self.assertIn("W kredycie o ratach malejących nie można zmieniać rat "
                      "całkowitych. Wprowadź raty kapitałowe lub zmień warunki "
                      "kredytu.", form.errors["total_installment"])

    def test_credit_tranche_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = self.payload
        form = CreditTrancheForm(
            data=payload,
            credit=self.credit,
            queryset=self.queryset,
            sum_of_tranches=self.sum_of_tranches,
            dates_of_tranches=self.dates_of_tranches
        )
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Missing required field: tranche_amount",
             {"tranche_date": datetime.date(2020, 2, 1)},
             "tranche_amount", "To pole jest wymagane."),
            ("Missing required field: tranche_date",
             {"tranche_amount": 20000},
             "tranche_date", "To pole jest wymagane."),
            ("Incorrect date type",
             {"tranche_date": "2020, 2, 1",
              "tranche_amount": 20000},
             "tranche_date", "Wpisz poprawną datę."),
            ("Negative value of tranche amount",
             {"tranche_date": datetime.date(2020, 2, 1),
              "tranche_amount": -2000},
             "tranche_amount", "Wartość nie może być liczbą ujemną."),
            ("Negative value of total_installment",
             {"tranche_date": datetime.date(2020, 2, 1),
              "tranche_amount": 20000, "total_installment": -1000},
             "total_installment", "Wartość nie może być liczbą ujemną."),
            ("Negative value of capital_installment",
             {"tranche_date": datetime.date(2020, 2, 1),
              "tranche_amount": 20000, "capital_installment": -1000},
             "capital_installment", "Wartość nie może być liczbą ujemną."),
        ]
    )
    def test_credit_tranche_form_is_not_valid(
            self, name, invalid_data, error_field, error):
        """Test if form is not valid with invalid data."""
        form = CreditTrancheForm(
            data=invalid_data,
            credit=self.credit,
            queryset=self.queryset,
            sum_of_tranches=self.sum_of_tranches,
            dates_of_tranches=self.dates_of_tranches
        )
        self.assertFalse(form.is_valid())
        self.assertIn(error, form.errors[error_field])


class CreditInterestRateFormTests(TestCase):
    """Tests for CreditInterestRateForm class."""

    def setUp(self):
        self.user = UserFactory()
        self.credit = CreditFactory(user=self.user)
        self.credit_interest_rate = CreditInterestRateFactory(
            user=self.user, credit=self.credit)

        self.installment_type = self.credit.installment_type
        self.start_of_payment = self.credit.start_of_payment
        self.payment_day = self.credit.payment_day

        self.form = CreditInterestRateForm(
            credit_id=self.credit.id,
            installment_type=self.installment_type,
            start_of_payment=self.start_of_payment,
            payment_day=self.payment_day
        )

        self.fields = [
            "interest_rate",
            "interest_rate_start_date",
            "note",
            "total_installment",
            "capital_installment"
        ]
        self.payload = {
            "interest_rate": 5.5,
            "interest_rate_start_date": datetime.date(2021, 3, 1),
            "note": "Nth new",
            "total_installment": 0,
            "capital_installment": 1000,
        }

    def test_credit_interest_rate_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_credit_interest_rate_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["interest_rate"].label,
                         _("Wysokość oprocentowania"))
        self.assertEqual(self.form.fields["interest_rate_start_date"].label,
                         _("Data rozpoczęcia obowiązywania oprocentowania"))
        self.assertEqual(self.form.fields["note"].label,
                         _("Informacja dodatkowa"))
        self.assertEqual(self.form.fields["total_installment"].label,
                         _("Wysokość raty całkowitej (dla rat stałych)"))
        self.assertEqual(self.form.fields["capital_installment"].label,
                         _("Wysokość raty kapitałowej (dla rat malejących)"))

    def test_credit_interest_rate_form_help_text(self):
        """Test if fields have correct help text."""
        self.assertEqual(self.form.fields["interest_rate"].help_text,
                         _("Pełna wysokość (z marżą banku i oprocentowaniem "
                           "pomostowym). Pole wymagane."))
        self.assertEqual(self.form.fields["interest_rate_start_date"].help_text,
                         _("Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane."))
        self.assertEqual(self.form.fields["total_installment"].help_text,
                         _("Brak informacji oznacza brak zmiany wysokości raty. "
                           "Uwaga: W kredycie o ratach malejących nie można "
                           "zmieniać rat całkowitych."))
        self.assertEqual(self.form.fields["capital_installment"].help_text,
                         _("Brak informacji oznacza brak zmiany wysokości raty. "
                           "Uwaga: W kredycie o ratach stałych (równych) nie "
                           "można zmieniać rat kapitałowych."))

    def test_credit_interest_rate_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in ["interest_rate", "capital_installment", "total_installment"]:
            self.assertEqual(self.form.fields[field].error_messages,
                             {"required": "To pole jest wymagane.",
                              "invalid": "Wpisz liczbę."})
        self.assertEqual(self.form.fields["interest_rate_start_date"].error_messages,
                         {"required": "To pole jest wymagane.",
                          "invalid": "Wpisz poprawną datę."})
        self.assertEqual(self.form.fields["note"].error_messages,
                         {"required": "To pole jest wymagane."})

    def test_credit_interest_rate_form_widgets(self):
        """Test if fields have correct widgets."""
        decimal_fields = [
            "interest_rate",
            "total_installment",
            "capital_installment"
        ]
        for field in decimal_fields:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "NumberInput")
        self.assertEqual(self.form.fields["interest_rate_start_date"].widget.__class__.__name__,
                         "DateInput")
        self.assertEqual(self.form.fields["note"].widget.__class__.__name__,
                         "TextInput")

    def test_credit_interest_rate_clean_date_of_payment(self):
        """User can only set date of new interest rate with the same day as in
        payment_date in credit model."""
        payment_day = self.credit.payment_day
        interest_rate_start_date = datetime.date(2021, 3, 11)
        self.assertNotEqual(payment_day, interest_rate_start_date.day)

        payload = self.payload
        payload["interest_rate_start_date"] = interest_rate_start_date
        form = CreditInterestRateForm(
            data=payload,
            credit_id=self.credit.id,
            installment_type=self.installment_type,
            start_of_payment=self.start_of_payment,
            payment_day=self.payment_day
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Dzień w dacie rozpoczęcia naliczania nowego "
                      "oprocentowania musi być zgodny z dniem płatności raty "
                      "(wybrany dzień: %s)." % self.payment_day,
                      form.errors["interest_rate_start_date"])

    def test_credit_interest_rate_clean_start_date(self):
        """Date of interest rate benchmark cannot be earlier than date of first payment."""
        payload = self.payload
        payload["interest_rate_start_date"] = (self.credit.start_of_payment
                                               - datetime.timedelta(days=30))
        form = CreditInterestRateForm(
            data=payload,
            credit_id=self.credit.id,
            installment_type=self.installment_type,
            start_of_payment=self.start_of_payment,
            payment_day=self.payment_day
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Data benchmarku oprocentowania nie może przypadać "
                      "wcześniej niż data rozpoczęcia spłaty kredytu.",
                      form.errors["interest_rate_start_date"])

    def test_credit_interest_rate_clean_capital_installment_method(self):
        """If credit has 'equal installments' ('Raty równe') user cannot set
        capital installments with another tranche."""
        self.credit.installment_type = _("Raty równe")
        self.credit.capital_installment = 0
        self.credit.total_installment = 1000
        self.credit.save()
        installment_type = self.credit.installment_type
        start_of_payment = self.credit.start_of_payment
        payment_day = self.credit.payment_day

        payload = self.payload
        payload["capital_installment"] = 1000
        form = CreditInterestRateForm(
            data=payload,
            credit_id=self.credit.id,
            installment_type=installment_type,
            start_of_payment=start_of_payment,
            payment_day=payment_day
        )
        self.assertFalse(form.is_valid())
        self.assertIn("W kredycie o ratach stałych (równych) nie można zmieniać "
                      "rat kapitałowych. Wprowadź raty całkowite lub zmień "
                      "warunki kredytu.", form.errors["capital_installment"])

    def test_credit_interest_rate_clean_total_installment_method(self):
        """If credit has 'decreasing installments' ('Raty malejące') user cannot
        set total installments with another tranche."""
        # self.credit has already set type_of_installment field as 'decreasing'
        payload = self.payload
        payload["total_installment"] = 1000
        form = CreditInterestRateForm(
            data=payload,
            credit_id=self.credit.id,
            installment_type=self.installment_type,
            start_of_payment=self.start_of_payment,
            payment_day=self.payment_day
        )
        self.assertFalse(form.is_valid())
        self.assertIn("W kredycie o ratach malejących nie można zmieniać rat "
                      "całkowitych. Wprowadź raty kapitałowe lub zmień warunki "
                      "kredytu.", form.errors["total_installment"])

    def test_credit_interest_rate_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = self.payload
        form = CreditInterestRateForm(
            data=payload,
            credit_id=self.credit.id,
            installment_type=self.installment_type,
            start_of_payment=self.start_of_payment,
            payment_day=self.payment_day
        )
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Missing required field: interest_rate",
             {"interest_rate_start_date": datetime.date(2021, 2, 1)},
             "interest_rate", "To pole jest wymagane."),
            ("Missing required field: interest_rate_start_date",
             {"interest_rate": 4.4},
             "interest_rate_start_date", "To pole jest wymagane."),
            ("Incorrect date type",
             {"interest_rate_start_date": "2021, 2, 1",
              "interest_rate": 4.4},
             "interest_rate_start_date", "Wpisz poprawną datę."),
            ("Negative value of interest rate",
             {"tranche_date": datetime.date(2021, 2, 1),
              "interest_rate": -2.2},
             "interest_rate", "Wartość nie może być liczbą ujemną."),
            ("Negative value of total_installment",
             {"tranche_date": datetime.date(2021, 2, 1),
              "interest_rate": 2.2, "total_installment": -1000},
             "total_installment", "Wartość nie może być liczbą ujemną."),
            ("Negative value of capital_installment",
             {"tranche_date": datetime.date(2021, 2, 1),
              "interest_rate": 2.2, "capital_installment": -1000},
             "capital_installment", "Wartość nie może być liczbą ujemną."),
        ]
    )
    def test_credit_interest_rate_form_is_not_valid(
            self, name, invalid_data, error_field, error):
        """Test if form is not valid with invalid data."""
        form = CreditInterestRateForm(
            data=invalid_data,
            credit_id=self.credit.id,
            installment_type=self.installment_type,
            start_of_payment=self.start_of_payment,
            payment_day=self.payment_day
        )
        self.assertFalse(form.is_valid())
        self.assertIn(error, form.errors[error_field])


class CreditInsuranceFormTests(TestCase):
    """Tests for CreditInsuranceForm class."""

    def setUp(self):
        self.user = UserFactory()
        self.credit = CreditFactory(user=self.user)
        self.credit_insurance = CreditInsuranceFactory(
            user=self.user, credit=self.credit
        )

        self.start_of_credit = self.credit.start_of_credit

        self.form = CreditInsuranceForm(start_of_credit=self.start_of_credit)
        self.fields = [
            "type",
            "amount",
            "frequency",
            "start_date",
            "end_date",
            "payment_period",
            "notes"
        ]
        self.payload = {
            "type": _("Ubezpieczenie na życie"),
            "amount": 550,
            "frequency": _("Półroczne"),
            "start_date": datetime.date(2021, 3, 1),
            "end_date": None,
            "payment_period": 1,
        }

    def test_credit_insurance_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_credit_insurance_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["type"].label,
                         _("Rodzaj ubezpieczenia"))
        self.assertEqual(self.form.fields["amount"].label,
                         _("Wysokość składki"))
        self.assertEqual(self.form.fields["frequency"].label,
                         _("Częstotliwość płatności"))
        self.assertEqual(self.form.fields["start_date"].label,
                         _("Rozpoczęcie płatności"))
        self.assertEqual(self.form.fields["end_date"].label,
                         _("Zakończenie płatności"))
        self.assertEqual(self.form.fields["payment_period"].label,
                         _("Liczba okresów płatności"))

    def test_credit_insurance_form_help_text(self):
        """Test if fields have correct help text."""
        for field in ["type", "frequency"]:
            self.assertEqual(self.form.fields[field].help_text, "")
        self.assertEqual(self.form.fields["payment_period"].help_text,
                         _("Przez ile okresów będzie dokonywana płatność "
                           "ubezpieczenia. Wpisz, jeśli płatność inna niż "
                           "jednorazowa."))
        self.assertEqual(self.form.fields["amount"].help_text,
                         _("Pole wymagane."))
        self.assertEqual(self.form.fields["end_date"].help_text,
                         _("Brak daty zakończenia płatności w przypadku braku "
                           "określenia ilości płatności oznacza płatność do "
                           "całkowitej spłaty kredytu. Format: YYYY-MM-DD "
                           "(np. 2020-07-21)."))
        self.assertEqual(self.form.fields["start_date"].help_text,
                         _("Dla jednorazowych płatności oznacza datę zapłaty. "
                           "Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane."))

    def test_credit_insurance_form_error_messages(self):
        """Test if fields have correct error messages."""
        self.assertEqual(self.form.fields["payment_period"].error_messages,
                         {"required": "To pole jest wymagane.",
                          "invalid": "Wpisz liczbę całkowitą."})
        for field in ["end_date", "end_date"]:
            self.assertEqual(self.form.fields[field].error_messages,
                             {"required": "To pole jest wymagane.",
                              "invalid": "Wpisz poprawną datę."})
        for field in ["frequency", "type"]:
            self.assertEqual(self.form.fields[field].error_messages,
                             {"required": "To pole jest wymagane.",
                              "invalid_choice": "Wybierz poprawną wartość. "
                                                "%(value)s nie jest żadną z "
                                                "dostępnych opcji."})

    def test_credit_insurance_form_widgets(self):
        """Test if fields have correct widgets."""
        number_fields = ["amount", "payment_period"]
        for field in number_fields:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "NumberInput")
        for field in ["frequency", "type"]:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "Select")
        for field in ["start_date", "end_date"]:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "DateInput")

    def test_credit_insurance_clean_insurance_start_date_before_start_of_credit(self):
        """User cannot set date of insurance payment before start of credit date."""
        start_of_credit = self.credit.start_of_credit
        payload = self.payload
        payload["start_date"] = start_of_credit - datetime.timedelta(days=10)
        form = CreditInsuranceForm(
            data=payload,
            start_of_credit=start_of_credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Data rozpoczęcia płatności ubezpieczenia nie może "
                      "przypadać wcześniej niż data udzielenia kredytu.",
                      form.errors["start_date"])

    def test_credit_insurance_clean_insurance_end_date(self):
        """User cannot set end date of insurance before start date."""
        payload = self.payload
        payload["end_date"] = payload["start_date"] - datetime.timedelta(days=10)
        form = CreditInsuranceForm(
            data=payload,
            start_of_credit=self.start_of_credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Data zakończenia płatności ubezpieczenia nie może "
                      "przypadać wcześniej niż data rozpoczęcia płatności.",
                      form.errors["end_date"])

    def test_credit_insurance_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = self.payload
        form = CreditInsuranceForm(
            data=payload,
            start_of_credit=self.start_of_credit
        )
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Empty field: amount", {"amount": ""}, "amount",
             "To pole jest wymagane."),
            ("Empty field: start_date", {"start_date": ""}, "start_date",
             "To pole jest wymagane."),
            ("Incorrect date type in end_date", {"end_date": "2021, 2, 1"},
             "end_date", "Wpisz poprawną datę."),
            ("Incorrect date type in start_date", {"start_date": "2021, 2, 1"},
             "start_date", "Wpisz poprawną datę."),
            ("Negative value of payment period", {"payment_period": -12},
             "payment_period",
             "Upewnij się, że ta wartość jest większa lub równa 0."),
            ("Incorrect value of payment_period (only positive integers are allowed",
             {"payment_period": 3.45},
             "payment_period", "Wpisz liczbę całkowitą."),
        ]
    )
    def test_credit_insurance_form_is_not_valid(
            self, name, invalid_data, error_field, error):
        """Test if form is not valid with invalid data."""
        form = CreditInsuranceForm(
            data=invalid_data,
            start_of_credit=self.credit.start_of_credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(error, form.errors[error_field])


class CreditCollateralFormTests(TestCase):
    """Tests for CreditCollateralForm class."""

    def setUp(self):
        self.user = UserFactory()
        self.credit = CreditFactory(user=self.user)
        self.credit_collateral = CreditCollateralFactory(
            user=self.user, credit=self.credit)

        self.form = CreditCollateralForm(credit=self.credit)

        self.fields = [
            "description",
            "collateral_value",
            "collateral_set_date",
            "total_installment",
            "capital_installment",
        ]
        self.payload = {
            "description": "Required collateral",
            "collateral_value": 1234567,
            "collateral_set_date": datetime.date(2021, 2, 15),
            "total_installment": 0,
            "capital_installment": 1000,
        }

    def test_credit_collateral_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_credit_collateral_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["description"].label,
                         _("Nazwa/opis zabezpieczenia"))
        self.assertEqual(self.form.fields["collateral_value"].label,
                         _("Wartość zabezpieczenia"))
        self.assertEqual(self.form.fields["collateral_set_date"].label,
                         _("Data ustanowienia zabezpieczenia"))
        self.assertEqual(self.form.fields["total_installment"].label,
                         _("Wysokość raty całkowitej (dla rat stałych)"))
        self.assertEqual(self.form.fields["capital_installment"].label,
                         _("Wysokość raty kapitałowej (dla rat malejących)"))

    def test_credit_collateral_form_help_text(self):
        """Test if fields have correct help text."""
        self.assertEqual(self.form.fields["collateral_set_date"].help_text,
                         _("Data akceptacji zabezpieczenia przez instytucję "
                           "finansującą. Pole wymagane. Uwaga: Data "
                           "ustanowienia zabezpieczenia nie może przypadać "
                           "wcześniej niż data rozpoczęcia umowy kredytu. "
                           "Format: YYYY-MM-DD (np. 2020-07-21)."))
        self.assertEqual(self.form.fields["total_installment"].help_text,
                         _("Brak informacji oznacza brak zmiany wysokości raty. "
                           "Uwaga: W kredycie o ratach malejących nie można "
                           "zmieniać rat całkowitych."))
        self.assertEqual(self.form.fields["capital_installment"].help_text,
                         _("Brak informacji oznacza brak zmiany wysokości raty. "
                           "Uwaga: W kredycie o ratach stałych (równych) nie "
                           "można zmieniać rat kapitałowych."))

    def test_credit_collateral_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in ["collateral_value", "capital_installment", "total_installment"]:
            self.assertEqual(self.form.fields[field].error_messages,
                             {"required": "To pole jest wymagane.",
                              "invalid": "Wpisz liczbę."})
        self.assertEqual(self.form.fields["collateral_set_date"].error_messages,
                         {"required": "To pole jest wymagane.",
                          "invalid": "Wpisz poprawną datę."})
        self.assertEqual(self.form.fields["description"].error_messages,
                         {"required": "To pole jest wymagane."})

    def test_credit_collateral_form_widgets(self):
        """Test if fields have correct widgets."""
        decimal_fields = [
            "collateral_value",
            "total_installment",
            "capital_installment"
        ]
        for field in decimal_fields:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "NumberInput")
        self.assertEqual(self.form.fields["collateral_set_date"].widget.__class__.__name__,
                         "DateInput")
        self.assertEqual(self.form.fields["description"].widget.__class__.__name__,
                         "TextInput")

    def test_credit_collateral_clean_capital_installment_method(self):
        """If credit has 'equal installments' ('Raty równe') user cannot set
        capital installments with setting a collateral."""
        self.credit.installment_type = _("Raty równe")
        self.credit.capital_installment = 0
        self.credit.total_installment = 1000
        self.credit.save()

        payload = self.payload
        payload["capital_installment"] = 1000
        form = CreditCollateralForm(
            data=payload,
            credit=self.credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("W kredycie o ratach stałych (równych) nie można zmieniać "
                      "rat kapitałowych. Wprowadź raty całkowite lub zmień "
                      "warunki kredytu.", form.errors["capital_installment"])

    def test_credit_collateral_clean_total_installment_method(self):
        """If credit has 'decreasing installments' ('Raty malejące') user cannot
        set total installments with setting a collateral."""
        # self.credit has already set type_of_installment field as 'decreasing'
        payload = self.payload
        payload["total_installment"] = 1000
        form = CreditCollateralForm(
            data=payload,
            credit=self.credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("W kredycie o ratach malejących nie można zmieniać rat "
                      "całkowitych. Wprowadź raty kapitałowe lub zmień warunki "
                      "kredytu.", form.errors["total_installment"])

    def test_credit_collateral_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = self.payload
        form = CreditCollateralForm(
            data=payload,
            credit=self.credit,
        )
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Missing required field: collateral_set_date",
             {"collateral_set_date": None},
             "collateral_set_date", "To pole jest wymagane."),
            ("Incorrect date type",
             {"collateral_set_date": "2021, 2, 1"},
             "collateral_set_date", "Wpisz poprawną datę."),
            ("Negative collateral value",
             {"collateral_set_date": datetime.date(2021, 2, 1),
              "collateral_value": -1000},
             "collateral_value", "Wartość nie może być liczbą ujemną."),
            ("Negative value of capital_installment",
             {"collateral_set_date": datetime.date(2021, 2, 1),
              "capital_installment": -1000},
             "capital_installment", "Wartość nie może być liczbą ujemną."),
            ("Negative value of total_installment",
             {"collateral_set_date": datetime.date(2021, 2, 1),
              "total_installment": -1000},
             "total_installment", "Wartość nie może być liczbą ujemną."),
        ]
    )
    def test_credit_collateral_form_is_not_valid(
            self, name, invalid_data, error_field, error):
        """Test if form is not valid with invalid data."""
        form = CreditCollateralForm(
            data=invalid_data,
            credit=self.credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(error, form.errors[error_field])


class CreditAdditionalCostFormTests(TestCase):
    """Tests for CreditAdditionalCostForm class."""

    def setUp(self):
        self.user = UserFactory()
        self.credit = CreditFactory(user=self.user)
        self.credit_collateral = CreditAdditionalCostFactory(
            user=self.user, credit=self.credit)

        self.form = CreditAdditionalCostForm(credit=self.credit)

        self.fields = [
            "name",
            "cost_amount",
            "cost_payment_date",
            "notes",
        ]
        self.payload = {
            "name": "Some new credit cost",
            "cost_amount": 3333,
            "cost_payment_date": datetime.date(2021, 2, 15),
            "notes": None,
        }

    def test_credit_cost_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_credit_cost_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["cost_amount"].label,
                         _("Wysokość kosztu"))
        self.assertEqual(self.form.fields["cost_payment_date"].label,
                         _("Data płatności"))
        self.assertEqual(self.form.fields["notes"].label, _("Uwagi"))

    def test_credit_cost_form_help_text(self):
        """Test if fields have correct help text."""
        self.assertEqual(self.form.fields["cost_amount"].help_text,
                         _("Pole wymagane. Dopuszczalne wartości ujemne jako "
                           "korekta wcześniejszych kosztów (zwrot)."))
        self.assertEqual(self.form.fields["cost_payment_date"].help_text,
                         _("Format: YYYY-MM-DD (np. 2020-07-21). Pole wymagane."))
        self.assertEqual(self.form.fields["name"].help_text, _("Pole wymagane."))

    def test_credit_cost_form_error_messages(self):
        """Test if fields have correct error messages."""
        self.assertEqual(self.form.fields["cost_amount"].error_messages,
                         {"required": "To pole jest wymagane.",
                          "invalid": "Wpisz liczbę."})
        self.assertEqual(self.form.fields["cost_payment_date"].error_messages,
                         {"required": "To pole jest wymagane.",
                          "invalid": "Wpisz poprawną datę."})
        for field in ["name", "notes"]:
            self.assertEqual(self.form.fields[field].error_messages,
                             {"required": "To pole jest wymagane."})

    def test_credit_cost_form_widgets(self):
        """Test if fields have correct widgets."""
        self.assertEqual(self.form.fields["notes"].widget.__class__.__name__,
                         "Textarea")
        self.assertEqual(self.form.fields["name"].widget.__class__.__name__,
                         "TextInput")
        self.assertEqual(self.form.fields["cost_payment_date"].widget.__class__.__name__,
                         "DateInput")
        self.assertEqual(self.form.fields["cost_amount"].widget.__class__.__name__,
                         "NumberInput")

    def test_credit_cost_clean_payment_date(self):
        """Date of cost payment cannot be earlier than date of credit agreement."""
        payload = self.payload
        payload["cost_payment_date"] = (self.credit.date_of_agreement
                                        - datetime.timedelta(days=30))
        form = CreditAdditionalCostForm(
            data=payload,
            credit=self.credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Data płatności (zwrotu) kosztu nie może przypadać "
                      "wcześniej niż data zawarcia umowy kredytu (%s)."
                      % self.credit.date_of_agreement,
                      form.errors["cost_payment_date"])

    def test_credit_cost_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = self.payload
        form = CreditAdditionalCostForm(
            data=payload,
            credit=self.credit,
        )
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Missing required field: name",
             {"cost_amount": 444, "cost_payment_date": datetime.date(2021, 3, 15)},
             "name", "To pole jest wymagane."),
            ("Missing required field: cost_payment_date",
             {"cost_amount": 444,
              "name": "new cost"},
             "cost_payment_date", "To pole jest wymagane."),
            ("Missing required field: cost_amount",
             {"name": "new cost",
              "cost_payment_date": datetime.date(2021, 3, 15)},
             "cost_amount", "To pole jest wymagane."),
            ("Incorrect date type",
             {"cost_payment_date": "2021, 2, 1"},
             "cost_payment_date", "Wpisz poprawną datę."),
        ]
    )
    def test_credit_cost_form_is_not_valid(
            self, name, invalid_data, error_field, error):
        """Test if form is not valid with invalid data."""
        form = CreditAdditionalCostForm(
            data=invalid_data,
            credit=self.credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(error, form.errors[error_field])


class CreditEarlyRepaymentFormTests(TestCase):
    """Tests for CreditEarlyRepaymentForm class."""

    def setUp(self):
        self.user = UserFactory()
        self.credit = CreditFactory(user=self.user)
        self.credit_collateral = CreditEarlyRepaymentFactory(
            user=self.user, credit=self.credit)

        self.form = CreditEarlyRepaymentForm(credit=self.credit)

        self.fields = [
            "repayment_amount",
            "repayment_date",
            "repayment_action",
            "total_installment",
            "capital_installment"
        ]
        self.payload = {
            "repayment_amount": 10000,
            "repayment_date": datetime.date(2021, 2, 15),
            "repayment_action": _("Skrócenie kredytowania"),
            "total_installment": 0,
            "capital_installment": 1000,
        }

    def test_credit_repayment_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_credit_collateral_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["repayment_amount"].label,
                         _("Wartość wcześniejszej spłaty"))
        self.assertEqual(self.form.fields["repayment_date"].label,
                         _("Data nadpłaty"))
        self.assertEqual(self.form.fields["repayment_action"].label,
                         _("Efekt nadpłaty"))
        self.assertEqual(self.form.fields["total_installment"].label,
                         _("Wysokość raty całkowitej (dla rat stałych)"))
        self.assertEqual(self.form.fields["capital_installment"].label,
                         _("Wysokość raty kapitałowej (dla rat malejących)"))

    def test_credit_repayment_form_help_text(self):
        """Test if fields have correct help text."""
        self.assertEqual(self.form.fields["repayment_amount"].help_text,
                         _("Pole wymagane."))
        self.assertEqual(self.form.fields["repayment_action"].help_text,
                         _("Pole wymagane."))
        self.assertEqual(self.form.fields["repayment_date"].help_text,
                         _("Pole wymagane. Format: YYYY-MM-DD (np. 2020-07-21)."))
        self.assertEqual(self.form.fields["total_installment"].help_text,
                         _("Brak informacji oznacza brak zmiany wysokości raty. "
                           "Uwaga: W kredycie o ratach malejących nie można "
                           "zmieniać rat całkowitych."))
        self.assertEqual(self.form.fields["capital_installment"].help_text,
                         _("Brak informacji oznacza brak zmiany wysokości raty. "
                           "Uwaga: W kredycie o ratach stałych (równych) nie "
                           "można zmieniać rat kapitałowych."))

    def test_credit_repayment_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in ["repayment_amount", "capital_installment", "total_installment"]:
            self.assertEqual(self.form.fields[field].error_messages,
                             {"required": "To pole jest wymagane.",
                              "invalid": "Wpisz liczbę."})
        self.assertEqual(self.form.fields["repayment_date"].error_messages,
                         {"required": "To pole jest wymagane.",
                          "invalid": "Wpisz poprawną datę."})
        self.assertEqual(self.form.fields["repayment_action"].error_messages,
                         {"required": "To pole jest wymagane.",
                          "invalid_choice": "Wybierz poprawną wartość. "
                                            "%(value)s nie jest żadną z "
                                            "dostępnych opcji."})

    def test_credit_repayment_form_widgets(self):
        """Test if fields have correct widgets."""
        decimal_fields = [
            "repayment_amount",
            "total_installment",
            "capital_installment"
        ]
        for field in decimal_fields:
            self.assertEqual(self.form.fields[field].widget.__class__.__name__,
                             "NumberInput")
        self.assertEqual(self.form.fields["repayment_date"].widget.__class__.__name__,
                         "DateInput")
        self.assertEqual(self.form.fields["repayment_action"].widget.__class__.__name__,
                         "Select")

    def test_credit_repayment_clean_repayment_date_method(self):
        """Date of repayment cannot be before date of first payment."""
        start_of_payment = self.credit.start_of_payment
        early_repayment_date = start_of_payment - datetime.timedelta(days=10)
        payload = self.payload
        payload["repayment_date"] = early_repayment_date
        form = CreditEarlyRepaymentForm(
            data=payload,
            credit=self.credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Data nadpłaty nie może przypadać wcześniej niż data "
                      "pierwszej płatności raty (%s)."
                      % self.credit.start_of_payment,
                      form.errors["repayment_date"])

    def test_credit_repayment_clean_capital_installment_method(self):
        """If credit has 'equal installments' ('Raty równe') user cannot set
        capital installments with early repayment."""
        self.credit.installment_type = _("Raty równe")
        self.credit.capital_installment = 0
        self.credit.total_installment = 1000
        self.credit.save()

        payload = self.payload
        payload["capital_installment"] = 1000
        form = CreditEarlyRepaymentForm(
            data=payload,
            credit=self.credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("W kredycie o ratach stałych (równych) nie można zmieniać "
                      "rat kapitałowych. Wprowadź raty całkowite lub zmień "
                      "warunki kredytu.", form.errors["capital_installment"])

    def test_credit_repayment_clean_total_installment_method(self):
        """If credit has 'decreasing installments' ('Raty malejące') user cannot
        set total installments with early repayment."""
        # self.credit has already set type_of_installment field as 'decreasing'
        payload = self.payload
        payload["total_installment"] = 1000
        form = CreditEarlyRepaymentForm(
            data=payload,
            credit=self.credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("W kredycie o ratach malejących nie można zmieniać rat "
                      "całkowitych. Wprowadź raty kapitałowe lub zmień warunki "
                      "kredytu.", form.errors["total_installment"])

    def test_credit_repayment_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = self.payload
        form = CreditEarlyRepaymentForm(
            data=payload,
            credit=self.credit,
        )
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Missing required field: repayment_amount",
             {"repayment_date": datetime.date(2022, 1, 1),
              "repayment_action": _("Skrócenie kredytowania")},
             "repayment_amount", "To pole jest wymagane."),
            ("Missing required field: repayment_date",
             {"repayment_amount": 1234,
              "repayment_action": _("Skrócenie kredytowania")},
             "repayment_date", "To pole jest wymagane."),
            ("Missing required field: repayment_action",
             {"repayment_date": datetime.date(2022, 1, 1),
              "repayment_amount": 1234},
             "repayment_action", "To pole jest wymagane."),
            ("Incorrect date type",
             {"repayment_date": "2021, 2, 1"},
             "repayment_date", "Wpisz poprawną datę."),
            ("Negative repayment_amount",
             {"repayment_date": datetime.date(2022, 2, 1),
              "repayment_action": _("Skrócenie kredytowania"),
              "repayment_amount": -1000},
             "repayment_amount", "Wartość nie może być liczbą ujemną."),
            ("Negative value of capital_installment",
             {"repayment_date": datetime.date(2022, 2, 1),
              "repayment_action": _("Skrócenie kredytowania"),
              "repayment_amount": -1000, "capital_installment": -1000},
             "capital_installment", "Wartość nie może być liczbą ujemną."),
            ("Negative value of total_installment",
             {"repayment_date": datetime.date(2022, 2, 1),
              "repayment_action": _("Skrócenie kredytowania"),
              "repayment_amount": -1000, "total_installment": -1000},
             "total_installment", "Wartość nie może być liczbą ujemną."),
            ("Incorrect repayment action field (out of choices)",
             {"repayment_date": datetime.date(2022, 2, 1),
              "repayment_action": _("Wakacje kredytowe"),
              "repayment_amount": 1000},
             "repayment_action", "Wybierz poprawną wartość. Wakacje kredytowe "
                                 "nie jest żadną z dostępnych opcji.")
        ]
    )
    def test_credit_repayment_form_is_not_valid(
            self, name, invalid_data, error_field, error):
        """Test if form is not valid with invalid data."""
        form = CreditEarlyRepaymentForm(
            data=invalid_data,
            credit=self.credit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(error, form.errors[error_field])
