import datetime
import logging
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase

from planner.models import ExpenseList, ExpenseItem, ToDoList, ToDoItem
from planner.factories import (ExpenseListFactory, ExpenseItemFactory,
                               ToDoListFactory, ToDoItemFactory)

User = get_user_model()
logger = logging.getLogger("test")


class ExpenseListModelTests(TestCase):
    """Test model ExpenseList."""

    def setUp(self):
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "name": "Nazwa",
            "access_granted": "Dostęp do danych",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }
        self.expense_list = ExpenseListFactory()
        self.user = self.expense_list.user
        self.cost1 = ExpenseItem.objects.create(
            user=self.user, expense_list=self.expense_list, name="cost1",
            estimated_cost=10, cost_paid=100
        )
        self.cost2 = ExpenseItem.objects.create(
            user=self.user, expense_list=self.expense_list, name="cost2",
            estimated_cost=20, cost_paid=200
        )
        self.cost3 = ExpenseItem.objects.create(
            user=self.user, expense_list=self.expense_list, name="cost3",
            estimated_cost=30, cost_paid=300
        )

    def test_create_expense_list_successful(self):
        """Test if creating a list with valid data is successful."""
        expense_list = ExpenseList.objects.all()
        self.assertEqual(expense_list.count(), 1)
        self.assertTrue(expense_list[0].user, self.user)
        self.assertTrue(expense_list[0].name, self.expense_list.name)

    def test_expense_list_id_is_uuid(self):
        """Test if id is represented as uuid."""
        expense_list = self.expense_list
        uuid_value = expense_list.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_error_for_empty_list_title(self):
        """Test if model without required fields cannot be saved in database."""
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                ExpenseList.objects.create(
                  user=self.user,
                )

    def test_unique_constraint_for_name_field(self):
        """Test if user can only have lists with unique names."""
        ExpenseList.objects.create(user=self.user, name="Some list title")
        self.assertEqual(ExpenseList.objects.count(), 2)
        with self.assertRaises(ValidationError):
            ExpenseList.objects.create(user=self.user, name="Some list title")

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.expense_list), "List name")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        expense_list_fields = list(self.field_names.values())
        expense_list_values = list(self.expense_list.__dict__.values())
        for field, value in self.expense_list:
            self.assertEqual(field, expense_list_fields[number])
            number += 1
            if isinstance(expense_list_values[number], uuid.UUID):
                self.assertEqual(value, str(expense_list_values[number]))
            elif isinstance(expense_list_values[number], list):
                self.assertEqual(value, str(expense_list_values[number][0]))
            elif isinstance(expense_list_values[number], datetime.date):
                self.assertEqual(value, str(expense_list_values[number]))
            else:
                self.assertEqual(value, str(expense_list_values[number]))

    def test_get_all_estimated_costs_method(self):
        """Test if get_all_estimated_costs method returns correct
        sum of all estimated costs."""
        expense_list = ExpenseList.objects.get(user=self.user)
        sum_of_costs = (self.cost1.estimated_cost
                        + self.cost2.estimated_cost
                        + self.cost3.estimated_cost)
        self.assertEqual(expense_list.get_all_estimated_costs(), sum_of_costs)

    def test_get_all_estimated_costs_method_return_zero(self):
        """Test if get_all_estimated_costs method return zero
        if no costs are associated to the expense list
        (no expense items with estimated costs)."""
        new_user = get_user_model().objects.create_user(
            username="New_user_123",
            email="new@example.com",
            password="testpass456"
        )
        expense_list = ExpenseList.objects.create(
            user=new_user, name="New expense list"
        )
        self.assertEqual(expense_list.get_all_estimated_costs(), None)

    def test_get_all_paid_costs_method(self):
        """Test if get_all_paid_costs method returns correct
        sum of all paid costs."""
        expense_list = ExpenseList.objects.get(user=self.user)
        sum_of_costs = (self.cost1.cost_paid
                        + self.cost2.cost_paid
                        + self.cost3.cost_paid)
        self.assertEqual(expense_list.get_all_paid_costs(), sum_of_costs)

    def test_get_all_paid_costs_method_return_zero(self):
        """Test if get_all_paid_costs method return zero
        if no costs are associated to the expense list
        (no expense items with paid costs)."""
        new_user = get_user_model().objects.create_user(
            username="New_user_123",
            email="new@example.com",
            password="testpass456"
        )
        expense_list = ExpenseList.objects.create(
            user=new_user, name="New expense list"
        )
        self.assertEqual(expense_list.get_all_paid_costs(), None)


    def test_validate_choices(self):
        """Test if clean method validates choices before saving instance in database."""
        # test correct access_granted
        self.expense_list.access_granted = "Brak dostępu"
        self.expense_list.save()
        self.assertEqual(self.expense_list.access_granted, "Brak dostępu")
        # test incorrect access_granted
        self.expense_list.access_granted = "Brak"
        with self.assertRaises(ValidationError):
            self.expense_list.save()


class ExpenseItemModelTests(TestCase):
    """Test model ExpenseItem."""

    def setUp(self):
        self.expense_list = ExpenseListFactory()
        self.user = self.expense_list.user
        self.expense_item = ExpenseItemFactory(
            user=self.user, expense_list=self.expense_list
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "expense_list": "Tytuł listy",
            "name": "Nazwa",
            "description": "Opis",
            "estimated_cost": "Szacunkowy koszt",
            "execution_status": "Status wykonania",
            "requirement_status": "Status wymagania",
            "validity_status": "Status ważności",
            "cost_paid": "Poniesiony koszt",
            "purchase_date": "Data poniesienia wydatku",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_expense_item_successful(self):
        """Test if creating a list item with valid data is successful."""
        expense_item = ExpenseItem.objects.all()
        self.assertEqual(expense_item.count(), 1)
        self.assertTrue(expense_item[0].user, self.user)
        self.assertTrue(expense_item[0].expense_list, self.expense_list)
        self.assertTrue(expense_item[0].description, "Test expense item")

    def test_expense_item_id_is_uuid(self):
        """Test if id is represented as uuid."""
        expense_item = self.expense_item
        uuid_value = expense_item.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        expense_item = self.expense_item
        number = 0
        item_fields = list(self.field_names.values())
        item_values = list(expense_item.__dict__.values())
        for field, value in expense_item:
            self.assertEqual(field, item_fields[number])
            number += 1
            if isinstance(item_values[number], uuid.UUID):
                self.assertEqual(value, str(item_values[number]))
            elif isinstance(item_values[number], list):
                self.assertEqual(value, str(item_values[number][0]))
            elif isinstance(item_values[number], datetime.date):
                self.assertEqual(value, str(item_values[number]))
            else:
                self.assertEqual(value, str(item_values[number]))

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.expense_item),  ExpenseItemFactory.name)

    def test_error_for_empty_required_fields(self):
        """Test if model without required fields cannot be saved in database."""
        # Empty name field
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                ExpenseItem.objects.create(
                  user=self.user, expense_list=self.expense_list,
                )

    def test_validate_choices(self):
        """Test if clean method validates choices before saving instance in database."""
        # test correct execution_status
        self.expense_item.execution_status = "Planowane"
        self.expense_item.save()
        self.assertEqual(self.expense_item.execution_status, "Planowane")
        # test correct requirement_status
        self.expense_item.requirement_status = "Opcjonalne"
        self.expense_item.save()
        self.assertEqual(self.expense_item.requirement_status, "Opcjonalne")

        # test incorrect execution_status
        self.expense_item.execution_status = "Inny"
        with self.assertRaises(ValidationError):
            self.expense_item.save()
        # test incorrect requirement_status
        self.expense_item.requirement_status = ["Inny"]
        with self.assertRaises(ValidationError):
            self.expense_item.save()


class ToDoListModelTests(TestCase):
    """Test model ToDoList."""

    def setUp(self):
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "name": "Nazwa",
            "access_granted": "Dostęp do danych",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }
        self.todo_list = ToDoListFactory()
        self.user = self.todo_list.user

    def test_create_todo_list_successful(self):
        """Test if creating a list with valid data is successful."""
        todo_list = ToDoList.objects.all()
        self.assertEqual(todo_list.count(), 1)
        self.assertTrue(todo_list[0].user, self.user)
        self.assertTrue(todo_list[0].name, self.todo_list.name)

    def test_todo_list_id_is_uuid(self):
        """Test if id is represented as uuid."""
        todo_list = self.todo_list
        uuid_value = todo_list.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_error_for_empty_name(self):
        """Test if model without required fields cannot be saved in database."""
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                ToDoList.objects.create(
                  user=self.user,
                )

    def test_unique_constraint_for_name_field(self):
        """Test if user can only have lists with unique names."""
        ToDoList.objects.create(user=self.user, name="Some list title")
        self.assertEqual(ToDoList.objects.count(), 2)
        with self.assertRaises(ValidationError):
            ToDoList.objects.create(user=self.user, name="Some list title")

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.todo_list), "List name")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        todo_list_fields = list(self.field_names.values())
        todo_list_values = list(self.todo_list.__dict__.values())
        for field, value in self.todo_list:
            self.assertEqual(field, todo_list_fields[number])
            number += 1
            if isinstance(todo_list_values[number], uuid.UUID):
                self.assertEqual(value, str(todo_list_values[number]))
            elif isinstance(todo_list_values[number], list):
                self.assertEqual(value, str(todo_list_values[number][0]))
            elif isinstance(todo_list_values[number], datetime.date):
                self.assertEqual(value, str(todo_list_values[number]))
            else:
                self.assertEqual(value, str(todo_list_values[number]))

    def test_validate_choices(self):
        """Test if clean method validates choices before saving instance in database."""
        # test correct access_granted
        self.todo_list.access_granted = "Brak dostępu"
        self.todo_list.save()
        self.assertEqual(self.todo_list.access_granted, "Brak dostępu")
        # test incorrect access_granted
        self.todo_list.access_granted = "Brak"
        with self.assertRaises(ValidationError):
            self.todo_list.save()


class ToDoItemModelTests(TestCase):
    """Test model ToDoItem."""

    def setUp(self):
        self.todo_list = ToDoListFactory()
        self.user = self.todo_list.user
        self.todo_item = ToDoItemFactory(
            user=self.user, todo_list=self.todo_list
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "todo_list": "Tytuł listy",
            "name": "Nazwa",
            "description": "Opis",
            "execution_status": "Status wykonania",
            "requirement_status": "Status wymagania",
            "validity_status": "Status ważności",
            "due_date": "Termin wykonania",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_todo_item_successful(self):
        """Test if creating a list item with valid data is successful."""
        todo_item = ToDoItem.objects.all()
        self.assertEqual(todo_item.count(), 1)
        self.assertTrue(todo_item[0].user, self.user)
        self.assertTrue(todo_item[0].todo_list, self.todo_list)
        self.assertTrue(todo_item[0].description, "Test item")

    def test_todo_item_id_is_uuid(self):
        """Test if id is represented as uuid."""
        todo_item = self.todo_item
        uuid_value = todo_item.id
        self.assertTrue(isinstance(uuid_value, uuid.UUID))

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        todo_item = self.todo_item
        number = 0
        item_fields = list(self.field_names.values())
        item_values = list(todo_item.__dict__.values())
        for field, value in todo_item:
            self.assertEqual(field, item_fields[number])
            number += 1
            if isinstance(item_values[number], uuid.UUID):
                self.assertEqual(value, str(item_values[number]))
            elif isinstance(item_values[number], list):
                self.assertEqual(value, str(item_values[number][0]))
            elif isinstance(item_values[number], datetime.date):
                self.assertEqual(value, str(item_values[number]))
            else:
                self.assertEqual(value, str(item_values[number]))

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.todo_item),  ToDoItemFactory.name)

    def test_error_for_empty_required_fields(self):
        """Test if model without required fields cannot be saved in database."""
        # Empty name field
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                ToDoItem.objects.create(
                  user=self.user, todo_list=self.todo_list,
                )

    def test_validate_choices(self):
        """Test if clean method validates choices before saving instance in database."""
        # test correct execution_status
        self.todo_item.execution_status = "Planowane"
        self.todo_item.save()
        self.assertEqual(self.todo_item.execution_status, "Planowane")
        # test correct requirement_status
        self.todo_item.requirement_status = "Opcjonalne"
        self.todo_item.save()
        self.assertEqual(self.todo_item.requirement_status, "Opcjonalne")

        # test incorrect execution_status
        self.todo_item.execution_status = "Inny"
        with self.assertRaises(ValidationError):
            self.todo_item.save()
        # test incorrect requirement_status
        self.todo_item.requirement_status = ["Inny"]
        with self.assertRaises(ValidationError):
            self.todo_item.save()
