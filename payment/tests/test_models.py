import datetime
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.db import transaction
from django.test import TestCase, TransactionTestCase

from payment.models import Payment
from payment.factories import PaymentFactory

User = get_user_model()


class BasicTests(TransactionTestCase):
    """Test Payment Model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456"
        )
        self.payment = PaymentFactory(
            user=self.user,
            name="setup payment",
        )
        self.test_payment = PaymentFactory(
            user=self.user,
            name="test payment",
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "name": "Nazwa",
            "payment_type": "Grupa opłat",
            "payment_method": "Sposób płatności",
            "payment_status": "Status płatności",
            "payment_frequency": "Częstotliwość płatności",
            "payment_months": "Miesiące płatności",
            "payment_day": "Dzień płatności",
            "payment_value": "Wysokość płatności",
            "notes": "Uwagi",
            "start_of_agreement": "Data zawarcia umowy",
            "end_of_agreement": "Data wygaśnięcia umowy",
            "access_granted": "Dostęp do danych",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }

    def test_create_payment_successful(self):
        """Test if creating payment instance with valid data is successful."""
        payment = Payment.objects.all()
        self.assertEqual(payment.count(), 2)
        self.assertTrue(payment[0].user, self.user)
        self.assertTrue(payment[0].name, self.payment.name)

    def test_payment_id_is_uuid(self):
        """Test if id is represented as uuid"""
        self.assertTrue(isinstance(self.payment.id, uuid.UUID))
        self.assertEqual(self.payment.id, uuid.UUID(str(self.payment.id)))
        # self.assertTrue(isinstance(uuid.UUID(self.payment.id), uuid.UUID))

    def test_unique_constraint_for_payment_name(self):
        """Test if user can only have payment with unique names."""
        self.test_user= User.objects.create_user(
            username="testuser123",
            email="test@example.com",
            password="testpass456"
        )

        # Correct
        payment_test1 = PaymentFactory(
            user=self.test_user,
            name="setup payment",
        )
        payment_test2 = PaymentFactory(
            user=self.user,
            name="new payment",
        )
        self.assertNotEqual(payment_test1.id, payment_test2.id, self.payment.id)

        # Incorrect
        with self.assertRaises(ValidationError):
            PaymentFactory(
                    user=self.user,
                    name="setup payment",
                )

    def test_field_is_not_none(self):
        """Test if creating an instance without required fields raises Error."""
        self.assertEqual(Payment.objects.all().count(), 2)
        # Payment without user field
        with self.assertRaises(ValidationError):
            Payment.objects.create(name="testname",)
        self.assertEqual(Payment.objects.all().count(), 2)
        # Payment without name field    --> for some reason instance is created (ERROR)
        with self.assertRaises(ValidationError):
            Payment.objects.create(user=self.user)
        self.assertEqual(Payment.objects.all().count(), 2)

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.payment), "setup payment")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        all_fields = list(self.field_names.values())
        all_values = list(self.payment.__dict__.values())
        for field, value in self.payment:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                if len(all_values[number]) > 1:
                    self.assertEqual(
                        value.replace(",", " "), " ".join(all_values[number])
                    )
                else:
                    self.assertEqual(value.split(), (all_values[number]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            elif all_values[number]:
                self.assertEqual(value, str(all_values[number]))

    def test_payment_months_to_list_method(self):
        """Test if payment_months_to_list returns list of months represented by string numbers."""
        new_payment = Payment.objects.create(user=self.user, name="new pmt", payment_months="2,5,9")
        self.assertEqual(new_payment.payment_months, "2,5,9")
        self.assertEqual(new_payment.payment_months_to_list(), ["2", "5", "9"])
        self.assertNotEqual(new_payment.payment_months_to_list(), ["2, 5, 9"])

    def test_payment_months_to_list_of_names_method(self):
        """Test if payment_months_to_list_of_names returns list of names of months represented."""
        new_payment = Payment.objects.create(user=self.user, name="new pmt", payment_months="2,5,9")
        self.assertEqual(new_payment.payment_months, "2,5,9")
        self.assertEqual(new_payment.payment_months_to_list_of_names(), ["Luty", "Maj", "Wrzesień"])

    def test_validate_choices(self):
        """Test if clean method validates choices before saving instance in database."""
        # test correct payment_frequency
        self.payment.payment_frequency = "Kwartalnie"
        self.payment.save()
        self.assertEqual(self.payment.payment_frequency, "Kwartalnie")
        # test correct payment_months
        self.payment.payment_months = "1,3,5"
        self.payment.save()
        self.assertEqual(self.payment.payment_months, "1,3,5")
        # test correct access_granted
        self.payment.access_granted = "Brak dostępu"
        self.payment.save()
        self.assertEqual(self.payment.access_granted, "Brak dostępu")
        # test correct payment_status
        self.payment.payment_status = "Zapłacone"
        self.payment.save()
        self.assertEqual(self.payment.payment_status, "Zapłacone")
        # test correct payment_type
        self.payment.payment_type = "Komunikacja"
        self.payment.save()
        self.assertEqual(self.payment.payment_type, "Komunikacja")

        # test incorrect payment_frequency
        self.payment.payment_frequency = "Inny"
        with self.assertRaises(ValidationError):
            self.payment.save()
        # test incorrect payment_months
        self.payment.payment_months = ["Styczeń"]
        with self.assertRaises(ValidationError):
            self.payment.save()
        self.payment.payment_months = "Styczeń,Maj"
        with self.assertRaises(ValidationError):
            self.payment.save()
        # test incorrect access_granted
        self.payment.access_granted = "Inny"
        with self.assertRaises(ValidationError):
            self.payment.save()
        # test incorrect payment_status
        self.payment.payment_status = "Inny"
        with self.assertRaises(ValidationError):
            self.payment.save()
        # test incorrect payment_type
        self.payment.payment_type = "Inny"
        with self.assertRaises(ValidationError):
            self.payment.save()
