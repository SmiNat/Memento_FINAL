import datetime
import logging
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase
from parameterized import parameterized

from renovation.models import Renovation, RenovationCost
from renovation.factories import RenovationFactory, RenovationCostFactory

User = get_user_model()
logger = logging.getLogger("test")


class RenovationModelTests(TestCase):
    """Test model Renovation."""

    def setUp(self):
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "name": "Nazwa",
            "description": "Opis",
            "estimated_cost": "Szacowany koszt",
            "start_date": "Data rozpoczęcia",
            "end_date": "Data zakończenia",
            "access_granted": "Dostęp do danych",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }
        self.renovation = RenovationFactory()
        self.user = self.renovation.user

    def test_create_renovation_successful(self):
        """Test if creating a renovation with valid data is successful."""
        renovations = Renovation.objects.all()
        self.assertEqual(renovations.count(), 1)
        self.assertTrue(renovations[0].user, self.user)
        self.assertTrue(renovations[0].name, self.renovation.name)

    def test_renovation_id_is_uuid(self):
        """Test if id is represented as uuid."""
        renovation = self.renovation
        uuid_value = renovation.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_error_for_empty_renovation_name(self):
        """Test if model without required fields cannot be saved in database."""
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                Renovation.objects.create(
                  user=self.user,
                )

    def test_unique_constraint_for_renovation_name(self):
        """Test if user can only have renovations with unique names."""
        Renovation.objects.create(user=self.user, name="Some renovation")
        self.assertEqual(Renovation.objects.count(), 2)

        # Unique together (only unique name fields for single user)
        with self.assertRaises(ValidationError):
            Renovation.objects.create(user=self.user, name="Some renovation")

        # Different users can have the same field name
        new_user = User.objects.create_user(
            username="newuser123", email="new@example.com", password="testpass123"
        )
        Renovation.objects.create(user=new_user, name="Some renovation")
        self.assertEqual(Renovation.objects.count(), 3)

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.renovation), "Test name")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        renovation = self.renovation
        number = 0
        renovation_fields = list(self.field_names.values())
        renovation_values = list(renovation.__dict__.values())
        for field, value in renovation:
            self.assertEqual(field, renovation_fields[number])
            number += 1
            if isinstance(renovation_values[number], uuid.UUID):
                self.assertEqual(value, str(renovation_values[number]))
            elif isinstance(renovation_values[number], list):
                self.assertEqual(value, str(renovation_values[number][0]))
            elif isinstance(renovation_values[number], datetime.date):
                self.assertEqual(value, str(renovation_values[number]))
            else:
                self.assertEqual(value, str(renovation_values[number]))

    def test_validate_choices(self):
        """Test if clean method validates choices before saving instance in database."""
        # test correct access_granted
        self.renovation.access_granted = "Brak dostępu"
        self.renovation.save()
        self.assertEqual(self.renovation.access_granted, "Brak dostępu")
        # test incorrect access_granted
        self.renovation.access_granted = "Brak"
        with self.assertRaises(ValidationError):
            self.renovation.save()

    @parameterized.expand(
        [
            ("both dates are set",
             datetime.date(2020, 10, 10),
             datetime.date(2020, 10, 15),
             6),
            ("start and end date has the same value",
             datetime.date(2020, 10, 10),
             datetime.date(2020, 10, 10),
             1),
            ("only start date is set",
             datetime.date(2020, 10, 10),
             None,
             None),
            ("only end date is set",
             None,
             datetime.date(2020, 10, 10),
             None)
        ]
    )
    def test_renovation_days_method(
            self, name: str,
            start_date: datetime,
            end_date: datetime,
            result: str
    ):
        """Test that get_renovation_time_in_days method returns correct number
        of days or string equal to '---' if dates are not set."""
        renovation = Renovation.objects.create(
            user=self.user,
            name="New renovation",
            start_date=start_date,
            end_date=end_date,
        )
        self.assertEqual(renovation.get_renovation_time_in_days(), result)

    def test_get_all_costs_method(self):
        """Test that method returns correct sum of all costs."""
        cost1 = RenovationCost.objects.create(
            user=self.user, renovation=self.renovation, name="cost1",
            units=10, unit_price=100
        )
        cost2 = RenovationCost.objects.create(
            user=self.user, renovation=self.renovation, name="cost2",
            units=20, unit_price=200
        )
        cost3 = RenovationCost.objects.create(
            user=self.user, renovation=self.renovation, name="cost3",
            units=3, unit_price=30
        )
        renovation = Renovation.objects.get(user=self.user)
        sum_of_costs = (cost1.units * cost1.unit_price
                        + cost2.units * cost2.unit_price
                        + cost3.units * cost3.unit_price)
        self.assertEqual(renovation.get_all_costs(), sum_of_costs)

    def test_get_all_costs_method_return_zero(self):
        """Test that get_all_costs method return zero
        if no costs are associated to the renovation."""
        renovation = Renovation.objects.get(user=self.user)
        self.assertEqual(renovation.get_all_costs(), None)


class RenovationCostModelTests(TestCase):
    """Test model RenovationCost."""

    def setUp(self):
        self.renovation = RenovationFactory()
        self.user = self.renovation.user
        self.renovation_cost = RenovationCostFactory(
            user=self.user, renovation=self.renovation
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "renovation": "Remont",
            "name": "Nazwa",
            "unit_price": "Cena jednostkowa",
            "units": "Liczba sztuk",
            "description": "Opis",
            "order": "Informacje dot. zamówienia",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_renovation_cost_successful(self):
        """Test if creating a renovation cost with valid data is successful."""
        renovation_cost = RenovationCost.objects.all()
        self.assertEqual(renovation_cost.count(), 1)
        self.assertTrue(renovation_cost[0].user, self.user)
        self.assertTrue(renovation_cost[0].renovation, self.renovation)
        self.assertTrue(renovation_cost[0].description, "Renovation first item cost")

    def test_renovation_cost_id_is_uuid(self):
        """Test if id is represented as uuid."""
        renovation_cost = self.renovation_cost
        uuid_value = renovation_cost.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        renovation_cost = self.renovation_cost
        number = 0
        cost_fields = list(self.field_names.values())
        cost_values = list(renovation_cost.__dict__.values())
        for field, value in renovation_cost:
            # print("🖥️", field, value)
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

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.renovation_cost),  RenovationCostFactory.name)

    def test_error_for_empty_required_fields(self):
        """Test if model without required fields cannot be saved in database."""
        # Empty name field
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                RenovationCost.objects.create(
                  user=self.user, renovation=self.renovation, unit_price=11
                )
        # Empty unit_price field
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                RenovationCost.objects.create(
                  user=self.user, renovation=self.renovation, name="Some name"
                )

    def test_sum_of_costs_method(self):
        """Test if sum_of_costs method calculates sum of all renovation costs."""
        renovation_cost = self.renovation_cost
        renovation_cost2 = RenovationCostFactory(
            user=self.user, renovation=self.renovation,
            name="Szafa", unit_price=200, units=1
        )
        renovation_cost3 = RenovationCostFactory(
            user=self.user, renovation=self.renovation,
            name="Łóżko", unit_price=300, units=5
        )
        self.assertEqual(
            renovation_cost.sum_of_costs(),
            round(RenovationCostFactory.unit_price * RenovationCostFactory.units
                  + renovation_cost2.unit_price * renovation_cost2.units
                  + renovation_cost3.unit_price * renovation_cost3.units, 2)
        )
