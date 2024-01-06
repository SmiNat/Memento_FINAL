import datetime
import logging
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from parameterized import parameterized

from access.enums import Access
from credit.enums import (CreditType, InstallmentType, TypeOfInterest, Currency,
                          Frequency, RepaymentAction, YesNo)
from credit.factories import (CreditFactory, CreditAdditionalCostFactory,
                              CreditCollateralFactory, CreditInsuranceFactory,
                              CreditInterestRateFactory, CreditTrancheFactory,
                              CreditEarlyRepaymentFactory)
from credit.models import (Credit, CreditAdditionalCost, CreditCollateral,
                           CreditInsurance, CreditInterestRate, CreditTranche,
                           CreditEarlyRepayment)
from user.handlers import create_slug, is_memento_slug_correct

User = get_user_model()
logger = logging.getLogger("test")


class CreditModelTests(TestCase):
    """Test model Renovation."""

    def setUp(self):
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "slug": "slug",
            "name": "Nazwa kredytu",
            "credit_number": "Numer umowy kredytu",
            "type": "Rodzaj kredytu",
            "currency": "Waluta",
            "credit_amount": "Wartość kredytu",
            "own_contribution": "Wkład własny",
            "market_value": "Wartość rynkowa nabywanej rzeczy/nieruchomości",
            "credit_period": "Okres kredytowania (w miesiącach)",
            "grace_period": "Okres karencji (w miesiącach)",
            "installment_type": "Rodzaj raty",
            "installment_frequency": "Częstotliwość płatności raty",
            "total_installment": "Wysokość raty całkowitej (dla rat równych)",
            "capital_installment": "Wysokość raty kapitałowej (dla rat malejących)",
            "type_of_interest": "Rodzaj oprocentowania",
            "fixed_interest_rate": "Wysokość oprocentowania stałego (w %)",
            "floating_interest_rate": "Wysokość oprocentowania zmiennego (w %)",
            "bank_margin": "Marża banku w oprocentowaniu zmiennym (w %)",
            "interest_rate_benchmark": "Rodzaj benchmarku",
            "date_of_agreement": "Data zawarcia umowy",
            "start_of_credit": "Data uruchomienia kredytu",
            "start_of_payment": "Data rozpoczęcia spłaty kredytu",
            "payment_day": "Dzień płatności raty",
            "provision": "Wysokość prowizji (w wybranej walucie)",
            "credited_provision": "Kredytowanie prowizji",
            "tranches_in_credit": "Transzowanie wypłat",
            "life_insurance_first_year": "Kredytowane ubezpieczenie na życie",
            "property_insurance_first_year": "Kredytowane ubezpieczenie rzeczy/nieruchomości",
            "collateral_required": "Wymagane zabezpieczenie kredytu",
            "collateral_rate": "Oprocentowanie dodatkowe (pomostowe)",
            "notes": "Uwagi",
            "access_granted": "Dostęp do danych",
            "access_granted_for_schedule": "Dostęp do harmonogramu",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }
        self.credit = CreditFactory(name="setup name")
        self.user = self.credit.user
        self.payload = {
            "user": self.user,
            "name": "New credit",
            "type": CreditType.OTHER,
            "currency": "PLN",
            "credit_amount": 10000,
            "credit_period": 20,
            "grace_period": 0,
            "installment_type": InstallmentType.DECREASING_INSTALLMENTS,
            "installment_frequency": Frequency.MONTHLY,
            "total_installment": 0,
            "capital_installment": 500,
            "type_of_interest": TypeOfInterest.VARIABLE,
            "fixed_interest_rate": 0,
            "floating_interest_rate": 5,
            "bank_margin": 1,
            "date_of_agreement": datetime.date(2020, 1, 10),
            "start_of_credit": datetime.date(2020, 1, 13),
            "start_of_payment": datetime.date(2020, 3, 7),
            "payment_day": 7,
            "provision": 0,
            "credited_provision": YesNo.NO,
            "tranches_in_credit": YesNo.NO,
            "collateral_required": YesNo.NO,
            "collateral_rate": 0,
            "access_granted": Access.NO_ACCESS_GRANTED,
            "access_granted_for_schedule": Access.NO_ACCESS_GRANTED,
        }

    def test_create_credit_successful(self):
        """Test if creating credit with valid data is successful."""
        # SetUp data (using factories)
        credits = Credit.objects.all()
        self.assertEqual(credits.count(), 1)
        self.assertTrue(credits[0].user, self.user)
        self.assertTrue(credits[0].name, self.credit.name)
        # Create an instance when required fields are given
        Credit.objects.create(
            user=self.user,
            name="New credit",
            type=CreditType.OTHER,
            currency="PLN",
            credit_amount=10000,
            credit_period=20,
            grace_period=0,
            installment_type=InstallmentType.DECREASING_INSTALLMENTS,
            installment_frequency=Frequency.MONTHLY,
            total_installment=0,
            capital_installment=500,
            type_of_interest=TypeOfInterest.VARIABLE,
            fixed_interest_rate=0,
            floating_interest_rate=5,
            bank_margin=1,
            date_of_agreement=datetime.date(2020, 1, 10),
            start_of_credit=datetime.date(2020, 1, 13),
            start_of_payment=datetime.date(2020, 3, 7),
            payment_day=7,
            provision=0,
            credited_provision=YesNo.NO,
            tranches_in_credit=YesNo.NO,
            collateral_required=YesNo.NO,
            collateral_rate=0,
            access_granted=Access.NO_ACCESS_GRANTED,
            access_granted_for_schedule=Access.NO_ACCESS_GRANTED,
        )
        self.assertEqual(Credit.objects.count(), 2)

    def test_credit_id_is_uuid(self):
        """Test if id is represented as uuid."""
        credit = self.credit
        uuid_value = credit.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    @parameterized.expand(
        [
            ("Empty name field", ["name", ""]),
            ("Empty type field", ["type", ""]),
            ("Empty currency field", ["currency", ""]),
            ("Empty credit_amount field", ["credit_amount", None]),
            ("Empty credit_period field", ["credit_period", None]),
            ("Empty installment_type field", ["installment_type", ""]),
            ("Empty installment_frequency field", ["installment_frequency", ""]),
            ("Empty total_installment field", ["total_installment", ""]),
            ("Empty capital_installment field", ["capital_installment", ""]),
            ("Empty type_of_interest field", ["type_of_interest", ""]),
            ("Empty fixed_interest_rate field", ["fixed_interest_rate", None]),
            ("Empty floating_interest_rate field", ["floating_interest_rate", ""]),
            ("Empty bank_margin field", ["bank_margin", ""]),
            ("Empty date_of_agreement field", ["date_of_agreement", ""]),
            ("Empty start_of_credit field", ["start_of_credit", None]),
            ("Empty start_of_payment field", ["start_of_payment", ""]),
            ("Empty payment_day field", ["payment_day", ""]),
            ("Empty credited_provision field", ["credited_provision", ""]),
            ("Empty tranches_in_credit field", ["tranches_in_credit", ""]),
            ("Empty collateral_required field", ["collateral_required", ""]),
            ("Empty access_granted field", ["access_granted", None]),
            ("Empty access_granted_for_schedule field",
             ["access_granted_for_schedule", ""]),
        ]
    )
    def test_field_is_not_none(self, name, field):
        """Test if model without required fields cannot be saved in database."""
        payload = self.payload
        payload[field[0]] = field[1]

        with transaction.atomic():
            with self.assertRaises(ValidationError):
                Credit.objects.create(
                    user=payload["user"],
                    name=payload["name"],
                    type=payload["type"],
                    currency=payload["currency"],
                    credit_amount=payload["credit_amount"],
                    credit_period=payload["credit_period"],
                    grace_period=payload["grace_period"],
                    installment_type=payload["installment_type"],
                    installment_frequency=payload["installment_frequency"],
                    total_installment=payload["total_installment"],
                    capital_installment=payload["capital_installment"],
                    type_of_interest=payload["type_of_interest"],
                    fixed_interest_rate=payload["fixed_interest_rate"],
                    floating_interest_rate=payload["floating_interest_rate"],
                    bank_margin=payload["bank_margin"],
                    date_of_agreement=payload["date_of_agreement"],
                    start_of_credit=payload["start_of_credit"],
                    start_of_payment=payload["start_of_payment"],
                    payment_day=payload["payment_day"],
                    provision=payload["provision"],
                    credited_provision=payload["credited_provision"],
                    tranches_in_credit=payload["tranches_in_credit"],
                    collateral_required=payload["collateral_required"],
                    collateral_rate=payload["collateral_rate"],
                    access_granted=payload["access_granted"],
                    access_granted_for_schedule=payload["access_granted_for_schedule"],
                )

    def test_unique_constraint_for_credit_name(self):
        """Test if user can only have credits with unique names."""

        # Unique together (only unique name fields for single user)
        with self.assertRaises(ValidationError):
            Credit.objects.create(user=self.user, name="Setup name")
        self.assertEqual(Credit.objects.count(), 1)

        # Different users can have the same field name
        new_user = User.objects.create_user(
            username="newuser123", email="new@example.com", password="testpass123"
        )
        CreditFactory(user=new_user, name="Setup name")
        self.assertEqual(Credit.objects.count(), 2)

    def slug_len_test(self):
        """Test if length of slug is correct."""
        slug = self.credit.slug
        username = self.user.username
        max_length = (len(str(datetime.date.today()))
                      + len(username[::-2])
                      + 22)
        assert len(slug) == max(max_length, 50)

    @parameterized.expand(
        [
            ("Real user instance", "johndoe123"),
            ("Latin characters in username",
             "śżźćąłóęńŚĄŻŹĆŃÓŁĘ"),
            ("Forbidden characters in username",
             "!@#$%^&*<>?.,+=[]{}:;'|\\\""),
        ]
    )
    def test_slug_field_with_no_forbidden_characters(
            self, name: str, username: str):
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
        """Test if there can only be unique field slug for model
        (for all users)."""
        slug_test = self.credit.slug
        new_credit = CreditFactory(
            user=self.user, name="new credit", slug=slug_test
        )
        self.assertNotEqual(slug_test, new_credit.slug)

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.credit), "setup name")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        credit = self.credit
        number = 0
        credit_fields = list(self.field_names.values())
        credit_values = list(credit.__dict__.values())
        for field, value in credit:
            # print("🖥️", field, value)
            self.assertEqual(field, credit_fields[number])
            number += 1
            if isinstance(credit_values[number], uuid.UUID):
                self.assertEqual(value, str(credit_values[number]))
            elif isinstance(credit_values[number], list):
                self.assertEqual(value, str(credit_values[number][0]))
            elif isinstance(credit_values[number], datetime.date):
                self.assertEqual(value, str(credit_values[number]))
            else:
                self.assertEqual(value, str(credit_values[number]))

    def test_total_loan_value_method(self):
        """Test that total_loan_value method returns correct value of loan."""
        loan_value = self.credit.credit_amount
        provision = 0
        life_insurance_first_year = 0
        property_insurance_first_year = 0
        if self.credit.life_insurance_first_year:
            life_insurance_first_year = self.credit.life_insurance_first_year
        if self.credit.property_insurance_first_year:
            property_insurance_first_year = self.credit.property_insurance_first_year
        if self.credit.credited_provision == _("Tak"):
            provision = self.credit.provision
        result = (loan_value + life_insurance_first_year
                  + property_insurance_first_year + provision)
        self.assertEqual(self.credit.total_loan_value(), result)

    def test_full_rate_method(self):
        """Test that full_rate method returns correct value of interest rate
        for floating rate with bank margin."""
        floating_rate = self.credit.floating_interest_rate
        bank_margin = self.credit.bank_margin
        result = floating_rate + bank_margin
        self.assertEqual(self.credit.full_rate(), result)

    def test_validate_choices(self):
        """Test if clean method validates choices before saving instance in database."""
        # test correct access_granted
        self.credit.access_granted = "Brak dostępu"
        self.credit.save()
        self.assertEqual(self.credit.access_granted, "Brak dostępu")
        # test correct access_granted_for_schedule
        self.credit.access_granted_for_schedule = "Brak dostępu"
        self.credit.save()
        self.assertEqual(self.credit.access_granted_for_schedule, "Brak dostępu")
        # test correct installment_type
        self.credit.installment_type = "Raty równe"
        self.credit.save()
        self.assertEqual(self.credit.installment_type, "Raty równe")
        # test correct installment_frequency
        self.credit.installment_frequency = "Miesięczne"
        self.credit.save()
        self.assertEqual(self.credit.installment_frequency, "Miesięczne")
        # test correct type_of_interest
        self.credit.access_granttype_of_interested = "Stałe"
        self.credit.save()
        self.assertEqual(self.credit.type_of_interest, "Stałe")

        # test incorrect access_granted
        self.credit.access_granted = "Brak"
        with self.assertRaises(ValidationError):
            self.credit.save()
        # test incorrect access_granted_for_schedule
        self.credit.access_granted_for_schedule = "Brak"
        with self.assertRaises(ValidationError):
            self.credit.save()
        # test incorrect installment_type
        self.credit.installment_type = "Brak"
        with self.assertRaises(ValidationError):
            self.credit.save()
        # test incorrect installment_frequency
        self.credit.installment_frequency = "Brak"
        with self.assertRaises(ValidationError):
            self.credit.save()
        # test incorrect type_of_interest
        self.credit.type_of_interest = "Brak"
        with self.assertRaises(ValidationError):
            self.credit.save()


class CreditTrancheModelTests(TestCase):
    """Test model CreditTranche."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456",
        )
        self.credit = CreditFactory(user=self.user)
        self.credit_tranche = CreditTrancheFactory(
            user=self.user, credit=self.credit
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "credit": "Kredyt",
            "tranche_amount": "Kwota transzy",
            "tranche_date": "Data wypłaty transzy",
            "total_installment": "Wysokość raty całkowitej (dla rat stałych)",
            "capital_installment": "Wysokość raty kapitałowej (dla rat malejących)",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_credit_tranche_successful(self):
        """Test if creating a credit tranche with valid data is successful."""
        credit_tranche = CreditTranche.objects.all()
        self.assertEqual(credit_tranche.count(), 1)
        self.assertTrue(credit_tranche[0].user, self.user)
        self.assertTrue(credit_tranche[0].credit, self.credit)
        self.assertTrue(credit_tranche[0].tranche_amount,
                        self.credit_tranche.tranche_amount)
        # All required fields are given
        CreditTranche.objects.create(
            user=self.user,
            credit=self.credit,
            tranche_amount=50000,
            tranche_date=datetime.date(2020, 11, 1),
            total_installment=None,
            capital_installment=None,
        )
        self.assertEqual(CreditTranche.objects.count(), 2)

    def test_credit_tranche_id_is_uuid(self):
        """Test if id is represented as uuid."""
        credit_tranche = self.credit_tranche
        uuid_value = credit_tranche.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        credit_tranche = self.credit_tranche
        number = 0
        tranche_fields = list(self.field_names.values())
        tranche_values = list(credit_tranche.__dict__.values())
        for field, value in credit_tranche:
            # print("🖥️", field, value)
            self.assertEqual(field, tranche_fields[number])
            number += 1
            if isinstance(tranche_values[number], uuid.UUID):
                self.assertEqual(value, str(tranche_values[number]))
            elif isinstance(tranche_values[number], list):
                self.assertEqual(value, str(tranche_values[number][0]))
            elif isinstance(tranche_values[number], datetime.date):
                self.assertEqual(value, str(tranche_values[number]))
            else:
                self.assertEqual(value, str(tranche_values[number]))

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        instance_str = str(str(self.credit_tranche.tranche_amount)
                           + " - "
                           + str(self.credit_tranche.tranche_date))
        self.assertEqual(instance_str, str(self.credit_tranche))

    def test_error_for_empty_required_fields(self):
        """Test if model without required fields cannot be saved in database."""
        # Empty tranche_amount field
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                CreditTranche.objects.create(
                    user=self.user, credit=self.credit, tranche_date="2020-9-1"
                )
        self.assertEqual(CreditTranche.objects.count(), 1)
        # Empty tranche_date field
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                CreditTranche.objects.create(
                    user=self.user, credit=self.credit, tranche_amount=111
                )
        self.assertEqual(CreditTranche.objects.count(), 1)

    def test_total_tranche_method(self):
        """Sum_of_costs method calculates all tranches amount of given credit correctly."""
        second_tranche = CreditTranche.objects.create(
            user=self.user, credit=self.credit, tranche_amount=20000,
            tranche_date=datetime.date(2020, 9, 1))
        second_credit = CreditFactory(user=self.user, name="Second")
        tranche_for_second_credit = CreditTranche.objects.create(
            user=self.user, credit=second_credit, tranche_amount=123456,
            tranche_date=datetime.date(2021, 4, 1))
        # Queryset of all credits in database
        queryset = CreditTranche.objects.all()
        self.assertEqual(
            self.credit_tranche.total_tranche(queryset),
            round(self.credit_tranche.tranche_amount
                  + second_tranche.tranche_amount
                  + tranche_for_second_credit.tranche_amount, 2)
        )
        # Queryset of self.credit tranches
        queryset = CreditTranche.objects.filter(credit=self.credit)
        self.assertEqual(
            self.credit_tranche.total_tranche(queryset),
            round(self.credit_tranche.tranche_amount
                  + second_tranche.tranche_amount, 2)
        )


class CreditInterestRateModelTests(TestCase):
    """Test model CreditInterestRate."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456",
        )
        self.credit = CreditFactory(user=self.user)
        self.interest_rate = CreditInterestRateFactory(
            user=self.user, credit=self.credit
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "credit": "Kredyt",
            "interest_rate": "Wysokość oprocentowania",
            "interest_rate_start_date": "Data rozpoczęcia obowiązywania oprocentowania",
            "note": "Informacja dodatkowa",
            "total_installment": "Wysokość raty całkowitej (dla rat stałych)",
            "capital_installment": "Wysokość raty kapitałowej (dla rat malejących)",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_interest_rate_successful(self):
        """Test if creating a interest rate with valid data is successful."""
        interest_rate = CreditInterestRate.objects.all()
        self.assertEqual(interest_rate.count(), 1)
        self.assertTrue(interest_rate[0].user, self.user)
        self.assertTrue(interest_rate[0].credit, self.interest_rate)
        self.assertTrue(interest_rate[0].interest_rate,
                        self.interest_rate.interest_rate)
        # Create an instance when required fields are given
        CreditInterestRate.objects.create(
            user=self.user,
            credit=self.credit,
            interest_rate=4,
            interest_rate_start_date=datetime.date(2020, 1, 10),
        )
        self.assertEqual(CreditInterestRate.objects.count(), 2)

    def test_interest_rate_id_is_uuid(self):
        """Test if id is represented as uuid."""
        interest_rate = self.interest_rate
        uuid_value = interest_rate.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        interest_rate = self.interest_rate
        number = 0
        rate_fields = list(self.field_names.values())
        rate_values = list(interest_rate.__dict__.values())
        for field, value in interest_rate:
            # print("🖥️", field, value)
            self.assertEqual(field, rate_fields[number])
            number += 1
            if isinstance(rate_values[number], uuid.UUID):
                self.assertEqual(value, str(rate_values[number]))
            elif isinstance(rate_values[number], list):
                self.assertEqual(value, str(rate_values[number][0]))
            elif isinstance(rate_values[number], datetime.date):
                self.assertEqual(value, str(rate_values[number]))
            else:
                self.assertEqual(value, str(rate_values[number]))

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        interest_rate = (str(self.interest_rate.interest_rate)
                         + " - "
                         + str(self.interest_rate.interest_rate_start_date))
        self.assertEqual(str(self.interest_rate),  interest_rate)

    def test_error_for_empty_required_fields(self):
        """Test if model without required fields cannot be saved in database."""
        # Empty interest_rate field
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                CreditInterestRate.objects.create(
                    user=self.user, credit=self.credit,
                    interest_rate_start_date=datetime.date(2020, 12, 1)
                )
        # Empty interest_rate_start_date field
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                CreditInterestRate.objects.create(
                    user=self.user, credit=self.credit, interest_rate=7
                )


class CreditInsuranceModelTests(TestCase):
    """Test model CreditInsurance."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456",
        )
        self.credit = CreditFactory(user=self.user)
        self.credit_insurance = CreditInsuranceFactory(
            user=self.user, credit=self.credit
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "credit": "Kredyt",
            "type": "Rodzaj ubezpieczenia",
            "amount": "Wysokość składki",
            "frequency": "Częstotliwość płatności",
            "start_date": "Rozpoczęcie płatności",
            "end_date": "Zakończenie płatności",
            "payment_period": "Liczba okresów płatności",
            "notes": "Uwagi",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_credit_insurance_successful(self):
        """Test if creating credit insurance with valid data is successful."""
        credit_insurance = CreditInsurance.objects.all()
        self.assertEqual(credit_insurance.count(), 1)
        self.assertTrue(credit_insurance[0].user, self.user)
        self.assertTrue(credit_insurance[0].credit, self.credit)
        self.assertTrue(credit_insurance[0].amount,
                        self.credit_insurance.amount)
        self.assertEqual(CreditInsurance.objects.count(), 1)

    def test_credit_insurance_id_is_uuid(self):
        """Test if id is represented as uuid."""
        credit_insurance = self.credit_insurance
        uuid_value = credit_insurance.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        credit_insurance = self.credit_insurance
        number = 0
        insurance_fields = list(self.field_names.values())
        insurance_values = list(credit_insurance.__dict__.values())
        for field, value in credit_insurance:
            self.assertEqual(field, insurance_fields[number])
            number += 1
            if isinstance(insurance_values[number], uuid.UUID):
                self.assertEqual(value, str(insurance_values[number]))
            elif isinstance(insurance_values[number], list):
                self.assertEqual(value, str(insurance_values[number][0]))
            elif isinstance(insurance_values[number], datetime.date):
                self.assertEqual(value, str(insurance_values[number]))
            elif insurance_values[number] is None:
                continue
            else:
                self.assertEqual(value, str(insurance_values[number]))

    def test_validate_choices(self):
        """Test if clean method validates choices before saving instance in database."""
        # test correct type
        self.credit_insurance.type = "Ubezpieczenie na życie"
        self.credit_insurance.save()
        self.assertEqual(self.credit_insurance.type, "Ubezpieczenie na życie")
        # test correct frequency
        self.credit_insurance.frequency = "Półroczne"
        self.credit_insurance.save()
        self.assertEqual(self.credit_insurance.frequency, "Półroczne")

        # test incorrect type
        self.credit_insurance.type = "Brak"
        with self.assertRaises(ValidationError):
            self.credit_insurance.save()
        # test incorrect frequency
        self.credit_insurance.frequency = "Brak"
        with self.assertRaises(ValidationError):
            self.credit_insurance.save()


class CreditCollateralModelTests(TestCase):
    """Test model CreditCollateral."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456",
        )
        self.credit = CreditFactory(user=self.user)
        self.credit_collateral = CreditCollateralFactory(
            user=self.user, credit=self.credit
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "credit": "Kredyt",
            "description": "Nazwa/opis zabezpieczenia",
            "collateral_value": "Wartość zabezpieczenia",
            "collateral_set_date": "Data ustanowienia zabezpieczenia",
            "total_installment": "Wysokość raty całkowitej (dla rat stałych)",
            "capital_installment": "Wysokość raty kapitałowej (dla rat malejących)",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_credit_collateral_successful(self):
        """Test if creating credit collateral with valid data is successful."""
        credit_collateral = CreditCollateral.objects.all()
        self.assertEqual(credit_collateral.count(), 1)
        self.assertTrue(credit_collateral[0].user, self.user)
        self.assertTrue(credit_collateral[0].credit, self.credit)
        self.assertTrue(credit_collateral[0].description,
                        self.credit_collateral.description)
        # All required fields are given
        CreditCollateral.objects.create(
            user=self.user,
            credit=self.credit,
            collateral_set_date=datetime.date(2021, 12, 1),
        )
        self.assertEqual(CreditCollateral.objects.count(), 2)

    def test_credit_collateral_id_is_uuid(self):
        """Test if id is represented as uuid."""
        credit_collateral = self.credit_collateral
        uuid_value = credit_collateral.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        result = (str(self.credit_collateral.collateral_value)
                  + " - "
                  + str(self.credit_collateral.collateral_set_date))
        self.assertEqual(str(self.credit_collateral), result)

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        credit_collateral = self.credit_collateral
        number = 0
        collateral_fields = list(self.field_names.values())
        collateral_values = list(credit_collateral.__dict__.values())
        for field, value in credit_collateral:
            self.assertEqual(field, collateral_fields[number])
            number += 1
            if isinstance(collateral_values[number], uuid.UUID):
                self.assertEqual(value, str(collateral_values[number]))
            elif isinstance(collateral_values[number], list):
                self.assertEqual(value, str(collateral_values[number][0]))
            elif isinstance(collateral_values[number], datetime.date):
                self.assertEqual(value, str(collateral_values[number]))
            else:
                self.assertEqual(value, str(collateral_values[number]))


class CreditAdditionalCostModelTests(TestCase):
    """Test model CreditAdditionalCost."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456",
        )
        self.credit = CreditFactory(user=self.user)
        self.credit_cost = CreditAdditionalCostFactory(
            user=self.user, credit=self.credit
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "credit": "Kredyt",
            "name": "Nazwa",
            "cost_amount": "Wysokość kosztu",
            "cost_payment_date": "Data płatności",
            "notes": "Uwagi",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_credit_cost_successful(self):
        """Test if creating credit cost with valid data is successful."""
        credit_cost = CreditAdditionalCost.objects.all()
        self.assertEqual(credit_cost.count(), 1)
        self.assertTrue(credit_cost[0].user, self.user)
        self.assertTrue(credit_cost[0].credit, self.credit)
        self.assertTrue(credit_cost[0].cost_amount,
                        self.credit_cost.cost_amount)
        # All required fields are given
        CreditAdditionalCost.objects.create(
            user=self.user,
            credit=self.credit,
            name="Koszt notariusza",
            cost_amount=567,
            cost_payment_date=datetime.date(2021, 8, 1),
        )
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)

    def test_credit_cost_id_is_uuid(self):
        """Test if id is represented as uuid."""
        credit_cost = self.credit_cost
        uuid_value = credit_cost.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.credit_cost), "Lawyer")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        credit_cost = self.credit_cost
        number = 0
        cost_fields = list(self.field_names.values())
        cost_values = list(credit_cost.__dict__.values())
        for field, value in credit_cost:
            self.assertEqual(field, cost_fields[number])
            number += 1
            if isinstance(cost_values[number], uuid.UUID):
                self.assertEqual(value, str(cost_values[number]))
            elif isinstance(cost_values[number], list):
                self.assertEqual(value, str(cost_values[number][0]))
            elif isinstance(cost_values[number], datetime.date):
                self.assertEqual(value, str(cost_values[number]))
            else:
                self.assertEqual(value, str(cost_values[number]))


class CreditEarlyRepaymentModelTests(TestCase):
    """Test model CreditEarlyRepayment."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456",
        )
        self.credit = CreditFactory(user=self.user)
        self.credit_repayment = CreditEarlyRepaymentFactory(
            user=self.user, credit=self.credit
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "credit": "Kredyt",
            "repayment_amount": "Wartość wcześniejszej spłaty",
            "repayment_date": "Data nadpłaty",
            "repayment_action": "Efekt nadpłaty",
            "total_installment": "Wysokość raty całkowitej (dla rat stałych)",
            "capital_installment": "Wysokość raty kapitałowej (dla rat malejących)",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_credit_repayment_successful(self):
        """Test if creating credit repayment with valid data is successful."""
        credit_repayment = CreditEarlyRepayment.objects.all()
        self.assertEqual(credit_repayment.count(), 1)
        self.assertTrue(credit_repayment[0].user, self.user)
        self.assertTrue(credit_repayment[0].credit, self.credit)
        self.assertTrue(credit_repayment[0].repayment_amount,
                        self.credit_repayment.repayment_amount)
        # All required fields are given
        CreditEarlyRepayment.objects.create(
            user=self.user,
            credit=self.credit,
            repayment_amount=2000,
            repayment_date=datetime.date(2022, 8, 1),
            repayment_action=RepaymentAction.SHORTER_PAYMENT,
        )
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)

    def test_credit_repayment_id_is_uuid(self):
        """Test if id is represented as uuid."""
        credit_repayment = self.credit_repayment
        uuid_value = credit_repayment.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        result = (str(self.credit_repayment.repayment_amount)
                  + " - "
                  + str(self.credit_repayment.repayment_date))
        self.assertEqual(str(self.credit_repayment), result)

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        credit_repayment = self.credit_repayment
        number = 0
        repayment_fields = list(self.field_names.values())
        repayment_values = list(credit_repayment.__dict__.values())
        for field, value in credit_repayment:
            self.assertEqual(field, repayment_fields[number])
            number += 1
            if isinstance(repayment_values[number], uuid.UUID):
                self.assertEqual(value, str(repayment_values[number]))
            elif isinstance(repayment_values[number], list):
                self.assertEqual(value, str(repayment_values[number][0]))
            elif isinstance(repayment_values[number], datetime.date):
                self.assertEqual(value, str(repayment_values[number]))
            else:
                self.assertEqual(value, str(repayment_values[number]))

    def test_total_repayment_method(self):
        """Test that total_repayment method returns correct value of loan repayment."""
        second_repayment = CreditEarlyRepaymentFactory(
            user=self.user, credit=self.credit, repayment_amount=5000,
            repayment_date=datetime.date(2022, 9, 1)
        )
        second_credit = CreditFactory(user=self.user, name="Second")
        repayment_for_second_credit = CreditEarlyRepaymentFactory(
            user=self.user, credit=second_credit, repayment_amount=33000,
            repayment_date=datetime.date(2022, 9, 1)
        )
        queryset = CreditEarlyRepayment.objects.filter(credit=self.credit)
        result = self.credit_repayment.repayment_amount + second_repayment.repayment_amount
        self.assertEqual(self.credit_repayment.total_repayment(queryset), result)

    def test_validate_choices(self):
        """Test if clean method validates choices before saving instance in database."""
        # test correct repayment_action
        self.credit_repayment.repayment_action = "Skrócenie kredytowania"
        self.credit_repayment.save()
        self.assertEqual(self.credit_repayment.repayment_action, "Skrócenie kredytowania")
        # test incorrect repayment_action
        self.credit_repayment.repayment_action = "Brak"
        with self.assertRaises(ValidationError):
            self.credit_repayment.save()
