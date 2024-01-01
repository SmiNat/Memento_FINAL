import datetime
import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.test import TestCase
from parameterized import parameterized

from planner.forms import ExpenseListForm, ExpenseItemForm, ToDoListForm, ToDoItemForm
from planner.factories import (ExpenseListFactory, ExpenseItemFactory,
                               ToDoListFactory, ToDoItemFactory)


User = get_user_model()
logger = logging.getLogger("test")


class ExpenseListFormTests(TestCase):
    """Tests for ExpenseListForm class."""

    def setUp(self):
        self.expense_list = ExpenseListFactory()
        self.form = ExpenseListForm(list_names=["Test name"])
        self.fields = [
            "name",
            "access_granted",
        ]

    def test_expense_list_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            assert field in self.form.fields

    def test_expense_list_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["access_granted"].label,
                         _("Dostęp do danych"))

    def test_expense_list_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Pole wymagane.",
                ))
            elif field == "access_granted":
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Użytkownik upoważniony do dostępu do danych "
                                   "może przeglądać listę wraz z wydatkami."))

    def test_expense_list_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "access_granted":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid_choice": "Wybierz poprawną wartość. %(value)s nie "
                                      "jest żadną z dostępnych opcji.",
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_expense_list_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
        ]
        for charfield in charfields:
            self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "TextInput")
        self.assertEqual(self.form.fields[
                             "access_granted"].widget.__class__.__name__,
                         "Select")

    def test_expense_list_clean_method_not_unique_list_title(self):
        """Test if clean method validates if list title field is always
        unique for one user."""
        payload = {
            "name": "New test name",
            "access_granted": "Brak dostępu",
        }
        form = ExpenseListForm(data=payload, list_names=["New test name"])
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już lista o podanej nazwie w bazie danych. "
                      "Podaj inną nazwę.", form.errors["name"])

    def test_expense_list_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "name": "Test of unique name",
            "access_granted": "Udostępnij dane",
        }
        form = ExpenseListForm(data=payload, list_names=["Test name"])
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Not unique field: name", "name",
             {"name": "Test name", "access_granted": "Udostępnij dane"},
             "Istnieje już lista o podanej nazwie w bazie danych. "
             "Podaj inną nazwę."),
        ]
    )
    def test_expense_list_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = ExpenseListForm(data=payload, list_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])


class ExpenseItemFormTests(TestCase):
    """Tests for ExpenseItemForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="some_user",
            email="su@example.com",
            password="testpass123"
        )
        self.expense_list = ExpenseListFactory(user=self.user)
        self.expense_item = ExpenseItemFactory(user=self.user)
        self.form = ExpenseItemForm()
        self.fields = [
            "name",
            "description",
            "estimated_cost",
            "execution_status",
            "requirement_status",
            "validity_status",
            "cost_paid",
            "purchase_date",
        ]

    def test_expense_item_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_expense_item_form_field_labels(self):
        """Test if fields have correct labels."""
        # assert self.form.fields["expense_list"].label == _("Tytuł listy")
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["description"].label, _("Opis"))
        self.assertEqual(self.form.fields["estimated_cost"].label,
                         _("Szacunkowy koszt"))
        self.assertEqual(self.form.fields["execution_status"].label,
                         _("Status wykonania"))
        self.assertEqual(self.form.fields["requirement_status"].label,
                         _("Status wymagania"))
        self.assertEqual(self.form.fields["validity_status"].label,
                         _("Status ważności"))
        self.assertEqual(self.form.fields["cost_paid"].label,
                         _("Poniesiony koszt"))
        self.assertEqual(self.form.fields["purchase_date"].label,
                         _("Data poniesienia wydatku"))

    def test_expense_item_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field in ["name"]:
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_expense_item_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })
            elif field == "estimated_cost" or field == "cost_paid":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz liczbę."
                })
            elif field == "purchase_date":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz poprawną datę."
                })
            elif field == "execution_status" \
                    or field == "requirement_status" \
                    or field == "validity_status":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid_choice": "Wybierz poprawną wartość. "
                                      "%(value)s nie jest żadną z dostępnych opcji.",
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_expense_item_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
            "description",
        ]
        decimalfields = [
            "estimated_cost",
            "cost_paid"
        ]
        choicefields = [
            "validity_status",
            "requirement_status",
            "execution_status",
        ]
        for charfield in charfields:
            if charfield == "name":
                self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "TextInput")
            else:
                self.assertEqual(self.form.fields[
                           charfield].widget.__class__.__name__, "Textarea")
        for decimalfield in decimalfields:
            self.assertEqual(self.form.fields[
                   decimalfield].widget.__class__.__name__, "NumberInput")
        for choicefield in choicefields:
            self.assertEqual(self.form.fields[
                   choicefield].widget.__class__.__name__, "Select")
        self.assertEqual(self.form.fields["purchase_date"].widget.__class__.__name__,
                         "SelectDateWidget")

    def test_expense_item_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "name": "New item name",
            "description": "New description 4 item",
            "estimated_cost": 100,
            "execution_status": "Planowane",
            "requirement_status": "Opcjonalne",
            "validity_status": "Pilne",
            "cost_paid": 20,
            "purchase_date": datetime.date(2022, 10, 20),
        }
        form = ExpenseItemForm(data=payload)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Negative estimated cost value", "estimated_cost",
             {"name": "New name", "estimated_cost": -10},
             "Wartość nie może być liczbą ujemną."),
            ("Negative cost paid value", "cost_paid",
             {"name": "New name", "cost_paid": -10},
             "Wartość nie może być liczbą ujemną."),
            ("Invalid status", "execution_status",
             {"name": "Some name", "execution_status": "sth"},
             "Wybierz poprawną wartość. sth nie jest żadną z dostępnych opcji."),
            ("Invalid date format", "purchase_date",
             {"name": "Some name", "purchase_date": "2020,10,10"},
             "Wpisz poprawną datę."),
        ]
    )
    def test_expense_item_form_is_not_valid(
            self, name: str, field: str, invalid_data: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        payload = invalid_data
        payload["expense_list"] = self.expense_list
        form = ExpenseItemForm(data=payload)
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])

###############################################################################


class ToDoListFormTests(TestCase):
    """Tests for ToDoListForm class."""

    def setUp(self):
        self.todo_list = ToDoListFactory()
        self.form = ToDoListForm(list_names=["Test name"])
        self.fields = [
            "name",
            "access_granted",
        ]

    def test_todo_list_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_todo_list_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["access_granted"].label,
                         _("Dostęp do danych"))

    def test_todo_list_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Pole wymagane.",
                ))
            elif field == "access_granted":
                self.assertEqual(self.form.fields[field].help_text, _(
                    "Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać listę wraz z zadaniami."))

    def test_todo_list_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "access_granted":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid_choice": "Wybierz poprawną wartość. %(value)s nie "
                                      "jest żadną z dostępnych opcji.",
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_todo_list_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
        ]
        for charfield in charfields:
            self.assertEqual(self.form.fields[
                       charfield].widget.__class__.__name__, "TextInput")
        self.assertEqual(self.form.fields["access_granted"].widget.__class__.__name__, "Select")

    def test_todo_list_clean_method_not_unique_list_title(self):
        """Test if clean method validates if list title field is always
        unique for one user."""
        payload = {
            "name": "New test name",
            "access_granted": "Brak dostępu",
        }
        form = ToDoListForm(
            data=payload, list_names=["New test name"]
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Istnieje już lista o podanej nazwie w bazie danych. "
                      "Podaj inną nazwę.", form.errors["name"])

    def test_todo_list_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "name": "Test of unique name",
            "access_granted": "Udostępnij dane",
        }
        form = ToDoListForm(data=payload, list_names=["Test name"])
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Not unique field: name", "name",
             {"name": "Test name", "access_granted": "Udostępnij dane"},
             "Istnieje już lista o podanej nazwie w bazie danych. "
             "Podaj inną nazwę."),
        ]
    )
    def test_todo_list_form_is_not_valid(
            self, name: str, field: str, payload: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        form = ToDoListForm(data=payload, list_names=["Test name"])
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])


class ToDoItemFormTests(TestCase):
    """Tests for ToDoItemForm class."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="some_user",
            email="su@example.com",
            password="testpass123"
        )
        self.todo_list = ToDoListFactory(user=self.user)
        self.todo_item = ToDoItemFactory(user=self.user)
        self.form = ToDoItemForm()
        self.fields = [
            "name",
            "description",
            "execution_status",
            "requirement_status",
            "validity_status",
            "due_date",
        ]

    def test_todo_item_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_todo_item_form_field_labels(self):
        """Test if fields have correct labels."""
        # assert self.form.fields["todo_list"].label == _("Tytuł listy")
        self.assertEqual(self.form.fields["name"].label, _("Nazwa"))
        self.assertEqual(self.form.fields["description"].label, _("Opis"))
        self.assertEqual(self.form.fields["execution_status"].label,
                         _("Status wykonania"))
        self.assertEqual(self.form.fields["requirement_status"].label,
                         _("Status wymagania"))
        self.assertEqual(self.form.fields["validity_status"].label,
                         _("Status ważności"))
        self.assertEqual(self.form.fields["due_date"].label,
                         _("Termin wykonania"))

    def test_todo_item_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field in ["name"]:
                self.assertEqual(self.form.fields[field].help_text,
                                 _("Pole wymagane."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_todo_item_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "name":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })
            elif field == "due_date":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid": "Wpisz poprawną datę."
                })
            elif field == "execution_status" \
                    or field == "requirement_status" \
                    or field == "validity_status":
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                    "invalid_choice": "Wybierz poprawną wartość. "
                                      "%(value)s nie jest żadną z dostępnych opcji.",
                })
            else:
                self.assertEqual(self.form.fields[field].error_messages, {
                    "required": "To pole jest wymagane.",
                })

    def test_todo_item_form_widgets(self):
        """Test if fields have correct widgets."""
        charfields = [
            "name",
            "description",
        ]
        choicefields = [
            "validity_status",
            "requirement_status",
            "execution_status",
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
                   choicefield].widget.__class__.__name__, "Select")
        self.assertEqual(self.form.fields["due_date"].widget.__class__.__name__,
                         "SelectDateWidget")

    def test_todo_item_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            # "todo_list": self.todo_list,
            "name": "New item name",
            "description": "New description 4 item",
            "execution_status": "Planowane",
            "requirement_status": "Opcjonalne",
            "validity_status": "Pilne",
            "due_date": datetime.date(2022, 10, 20),
        }
        form = ToDoItemForm(data=payload)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("Invalid status", "execution_status",
             {"name": "Some name", "execution_status": "sth"},
             "Wybierz poprawną wartość. sth nie jest żadną z dostępnych opcji."),
            ("Invalid date format", "due_date",
             {"name": "Some name", "due_date": "2020,10,10"},
             "Wpisz poprawną datę."),
        ]
    )
    def test_todo_item_form_is_not_valid(
            self, name: str, field: str, invalid_data: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        payload = invalid_data
        payload["todo_list"] = self.todo_list
        form = ToDoItemForm(data=payload)
        self.assertFalse(form.is_valid())
        self.assertIn(error_msg, form.errors[field])
