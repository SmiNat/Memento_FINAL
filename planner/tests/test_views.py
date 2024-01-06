import datetime
import logging

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from access.enums import Access
from planner.enums import RequirementStatus, ValidityStatus, ExecutionStatus
from planner.factories import (ExpenseListFactory, ExpenseItemFactory,
                               ToDoListFactory, ToDoItemFactory)
from planner.forms import (ExpenseListForm, ExpenseItemForm,
                           ToDoListForm, ToDoItemForm)
from planner.models import ExpenseList, ExpenseItem, ToDoList, ToDoItem
from user.factories import UserFactory, ProfileFactory

User = get_user_model()
logger = logging.getLogger("test")


class PlannerBasicUrlsTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.expense_list = ExpenseListFactory(user=self.user)
        self.expense_item = ExpenseItemFactory(user=self.user, expense_list=self.expense_list)
        self.todo_list = ToDoListFactory(user=self.user)
        self.todo_item = ToDoItemFactory(user=self.user, todo_list=self.todo_list)

        self.planner_pages = [
            {"page": "planner:planner", "args": [1],
             "template": "planner/planner.html"},
            {"page": "planner:expense-lists", "args": [],
             "template": "planner/planner_lists.html"},
            {"page": "planner:single-expense-list",
             "args": [str(self.expense_list.id)],
             "template": "planner/single_list.html"},
            {"page": "planner:todo-lists", "args": [],
             "template": "planner/planner_lists.html"},
            {"page": "planner:single-todo-list",
             "args": [str(self.todo_list.id)],
             "template": "planner/single_list.html"},

            {"page": "planner:add-expense-list", "args": [],
             "template": "planner/planner_form.html"},
            {"page": "planner:edit-expense-list",
             "args": [str(self.expense_list.id)],
             "template": "planner/planner_form.html"},
            {"page": "planner:delete-expense-list",
             "args": [str(self.expense_list.id)],
             "template": "planner/planner_delete_form.html"},

            {"page": "planner:add-expense-item",
             "args": [str(self.expense_list.id)],
             "template": "planner/planner_form.html"},
            {"page": "planner:edit-expense-item",
             "args": [str(self.expense_item.id)],
             "template": "planner/planner_form.html"},
            {"page": "planner:delete-expense-item",
             "args": [str(self.expense_item.id)],
             "template": "planner/planner_delete_form.html"},

            {"page": "planner:add-todo-list", "args": [],
             "template": "planner/planner_form.html"},
            {"page": "planner:edit-todo-list",
             "args": [str(self.todo_list.id)],
             "template": "planner/planner_form.html"},
            {"page": "planner:delete-todo-list",
             "args": [str(self.todo_list.id)],
             "template": "planner/planner_delete_form.html"},

            {"page": "planner:add-todo-item",
             "args": [str(self.todo_list.id)],
             "template": "planner/planner_form.html"},
            {"page": "planner:edit-todo-item",
             "args": [str(self.todo_item.id)],
             "template": "planner/planner_form.html"},
            {"page": "planner:delete-todo-item",
             "args": [str(self.todo_item.id)],
             "template": "planner/planner_delete_form.html"},
        ]

    def test_view_url_accessible_by_name_for_unauthenticated_user(self):
        """Test if view url is accessible by its name
        and returns redirect (302) for unauthenticated user."""
        for page in self.planner_pages:
            response_page = self.client.get(
                reverse(page["page"], args=page["args"]))
            self.assertEqual(response_page.status_code, 302)
            self.assertIn("login", response_page.url)

    def test_view_url_accessible_by_name_for_authenticated_user(self):
        """Test if view url is accessible by its name
         and returns desired page (200) for authenticated user."""
        self.client.force_login(self.user)
        for page in self.planner_pages:
            response_page = self.client.get(
                reverse(page["page"], args=page["args"]))
            self.assertEqual(response_page.status_code, 200)
            self.assertEqual(str(response_page.context["user"]), "testuser")

    def test_view_uses_correct_template(self):
        """Test if response returns correct page template."""
        # Test for authenticated user
        self.client.force_login(self.user)
        for page in self.planner_pages:
            response = self.client.get(reverse(page["page"], args=page["args"]))
            self.assertTemplateUsed(response, page["template"])


class PlannerViewTest(TestCase):
    """Test planner page views"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass456")
        self.expense_list = ExpenseListFactory(
            user=self.user, name="expense setup name")
        self.test_expense_list = ExpenseListFactory(
            user=self.test_user, name="expense test name")
        self.todo_list = ToDoListFactory(
            user=self.user, name="todo setup name")
        self.test_todo_list = ToDoListFactory(
            user=self.test_user, name="todo test name")

    def test_all_setup_instances_created(self):
        """Test if user account and trip model was created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(ExpenseList.objects.count(), 2)
        self.assertEqual(ToDoList.objects.count(), 2)

    def test_planner_302_redirect_if_unauthorized(self):
        """Test if planner page is unavailable for unauthorized users."""
        response = self.client.get(reverse("planner:planner", args=[1]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_planner_200_if_logged_in(self):
        """Test if planner page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:planner", args=[1]))
        self.assertEqual(response_get.status_code, 200)

    def test_planner_correct_template_if_logged_in(self):
        """Test if planner page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:planner", args=[1]))
        self.assertTemplateUsed(response_get, "planner/planner.html")

    def test_planner_initial_values_set_context_data(self):
        """Test if planner page displays correct context data."""
        expense_list = ExpenseList.objects.filter(user=self.user).order_by("updated")
        todo_list = ToDoList.objects.filter(user=self.user).order_by("updated")
        paginator_expense = Paginator(expense_list, per_page=10)
        paginator_todo = Paginator(todo_list, per_page=10)
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("planner:planner", args=[1]))
        self.assertEqual(response_get.context["page_obj_expense"].number, 1)
        self.assertEqual(response_get.context["page_obj_todo"].number, 1)
        self.assertQuerysetEqual(response_get.context["expense_list"], expense_list)
        self.assertQuerysetEqual(response_get.context["todo_list"], todo_list)

    def test_planner_initial_values_set_expense_data(self):
        """Test if logged user can see data for expense without seeing
        data of other users."""
        new_expense_list = ExpenseListFactory(user=self.user, name="new expense list")

        # Test content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("planner:planner", args=[1]))

        user = User.objects.get(id=self.client.session["_auth_user_id"])
        self.assertEqual(user, self.user)

        self.assertIn("johndoe123", response_get.content.decode())
        self.assertIn(self.todo_list.name, response_get.content.decode())
        self.assertIn(self.expense_list.name, response_get.content.decode())
        self.assertIn(new_expense_list.name, response_get.content.decode())
        self.assertNotIn("testuser", response_get.content.decode())
        self.assertNotIn(self.test_expense_list.name, response_get.content.decode())
        self.assertNotIn(self.test_todo_list.name, response_get.content.decode())

        self.client.logout()

        # Test content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("planner:planner", args=[1]))

        user = User.objects.get(id=self.client.session["_auth_user_id"])
        self.assertEqual(user, self.test_user)

        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertNotIn(self.todo_list.name, response_get.content.decode())
        self.assertNotIn(self.expense_list.name, response_get.content.decode())
        self.assertNotIn(new_expense_list.name, response_get.content.decode())
        self.assertIn("testuser", response_get.content.decode())
        self.assertIn(self.test_expense_list.name, response_get.content.decode())
        self.assertIn(self.test_todo_list.name, response_get.content.decode())

    def test_planner_lists_first_page_expense_lists(self):
        # Get first page and confirm it has (exactly) 10 items
        for expense_list_number in range(11):
            ExpenseListFactory(user=self.user, name=str(expense_list_number))
        self.assertEqual(ExpenseList.objects.filter(user=self.user).count(), 12)

        expense_list = ExpenseList.objects.filter(user=self.user).order_by(
            "updated")
        todo_list = ToDoList.objects.filter(user=self.user).order_by("updated")
        paginator_expense = Paginator(expense_list, per_page=10)
        paginator_todo = Paginator(todo_list, per_page=10)
        first_page = paginator_expense.page(1)

        self.assertEqual(paginator_expense.count, 12)
        self.assertEqual(paginator_expense.num_pages, 2)
        self.assertFalse(first_page.has_previous())
        self.assertTrue(first_page.has_next())
        self.assertEqual(first_page.start_index(), 1)
        self.assertEqual(first_page.end_index(), 10)
        # self.assertEqual(paginator_expense.get_page(1), first_page)

        self.client.force_login(self.user)
        response_get = self.client.get(reverse("planner:planner", args=[1]))
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(response_get.context["page_obj_expense"], paginator_expense.page(1))

    def test_planner_lists_second_page_expense_lists(self):
        # Get second page and confirm it has (exactly) remaining 2 items
        for expense_list_number in range(11):
            ExpenseListFactory(user=self.user, name=str(expense_list_number))
        self.assertEqual(ExpenseList.objects.filter(user=self.user).count(), 12)

        expense_list = ExpenseList.objects.filter(user=self.user).order_by(
            "updated")
        todo_list = ToDoList.objects.filter(user=self.user).order_by("updated")
        paginator_expense = Paginator(expense_list, per_page=10)
        paginator_todo = Paginator(todo_list, per_page=10)
        second_page = paginator_expense.page(2)

        self.assertEqual(paginator_expense.count, 12)
        self.assertEqual(paginator_expense.num_pages, 2)
        self.assertTrue(second_page.has_previous())
        self.assertFalse(second_page.has_next())
        self.assertEqual(second_page.start_index(), 11)
        self.assertEqual(second_page.end_index(), 12)
        # self.assertEqual(paginator_expense.get_page(2), second_page)

        self.client.force_login(self.user)
        response_get = self.client.get(reverse("planner:planner", args=[2]))
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(response_get.context["page_obj_expense"], paginator_expense.page(2))

    def test_expense_lists_302_redirect_if_unauthorized(self):
        """Test if expense lists page is unavailable for unauthorized users."""
        response = self.client.get(reverse("planner:expense-lists", args=[]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_expense_lists_200_if_logged_in(self):
        """Test if expense lists page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:expense-lists", args=[]))
        self.assertEqual(response_get.status_code, 200)

    def test_expense_lists_correct_template_if_logged_in(self):
        """Test if expense lists page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:expense-lists", args=[]))
        self.assertTemplateUsed(response_get, "planner/planner_lists.html")

    def test_expense_lists_initial_values_set_context_data(self):
        """Test if expense lists page displays correct context data."""
        full_expense_list = ExpenseList.objects.filter(
            user=self.user).order_by("-updated")
        search_query = "john"
        if search_query:
            expense_list = ExpenseList.objects.filter(
                user=self.user).filter(
                name__icontains=search_query).order_by("-updated")
        else:
            expense_list = full_expense_list
        page_number = 1
        paginator_expense = Paginator(expense_list, per_page=10)
        page_object_expense = paginator_expense.get_page(page_number)
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("planner:expense-lists"))
        self.assertEqual(response_get.context["page_name"], "expense-lists")
        # self.assertEqual(response_get.context["paginator"], paginator_expense)
        self.assertEqual(response_get.context["page_obj"], page_object_expense)
        self.assertEqual(response_get.context["search_query"], search_query)
        self.assertQuerysetEqual(response_get.context["expense_list"],
                                 expense_list)
        self.assertQuerysetEqual(response_get.context["full_expense_list"],
                                 full_expense_list)

    def test_expense_lists_initial_values_set_expense_data(self):
        """Test if logged user can see data for expense without seeing
        data of other users."""
        new_expense_list = ExpenseListFactory(user=self.user, name="new expense list")

        # Test content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("planner:expense-lists", args=[]))

        user = User.objects.get(id=self.client.session["_auth_user_id"])
        self.assertEqual(user, self.user)

        self.assertIn("johndoe123", response_get.content.decode())
        self.assertIn(self.expense_list.name, response_get.content.decode())
        self.assertIn(new_expense_list.name, response_get.content.decode())
        self.assertNotIn("testuser", response_get.content.decode())
        self.assertNotIn(self.test_expense_list.name, response_get.content.decode())

        self.client.logout()

        # Test content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("planner:planner", args=[1]))

        user = User.objects.get(id=self.client.session["_auth_user_id"])
        self.assertEqual(user, self.test_user)

        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertNotIn(self.expense_list.name, response_get.content.decode())
        self.assertNotIn(new_expense_list.name, response_get.content.decode())
        self.assertIn("testuser", response_get.content.decode())
        self.assertIn(self.test_expense_list.name, response_get.content.decode())

    def test_expense_lists_pages(self):
        """Test if paginator is working correctly."""
        # Get first page and confirm it has (exactly) 10 items
        for expense_list_number in range(11):
            ExpenseListFactory(user=self.user, name=str(expense_list_number))
        self.assertEqual(ExpenseList.objects.filter(user=self.user).count(), 12)

        expense_list = ExpenseList.objects.filter(user=self.user).order_by(
            "updated")
        paginator_expense = Paginator(expense_list, per_page=10)
        first_page = paginator_expense.page(1)

        self.assertEqual(paginator_expense.count, 12)
        self.assertEqual(paginator_expense.num_pages, 2)
        self.assertFalse(first_page.has_previous())
        self.assertTrue(first_page.has_next())
        self.assertEqual(first_page.start_index(), 1)
        self.assertEqual(first_page.end_index(), 10)
        # self.assertEqual(paginator_expense.get_page(1), first_page)

        self.client.force_login(self.user)
        response_get = self.client.get(reverse("planner:expense-lists"))
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(response_get.context["page_obj"], paginator_expense.page(1))

    def test_expense_lists_search_engine(self):
        """Test if filtering queryset by search engine is working correctly."""
        for expense_list_number in range(12):
            ExpenseListFactory(user=self.user, name=str(expense_list_number))
        self.assertEqual(ExpenseList.objects.filter(user=self.user).count(), 13)

        search_query = "1"  # expense_lists = [1, 10, 11]
        expense_list = ExpenseList.objects.filter(
            user=self.user).filter(
            name__icontains=search_query).order_by(
            "updated")
        paginator_expense = Paginator(expense_list, per_page=10)

        self.assertEqual(expense_list.count(), 3)
        self.assertEqual(paginator_expense.count, 3)
        self.assertEqual(paginator_expense.num_pages, 1)

    def test_todo_lists_302_redirect_if_unauthorized(self):
        """Test if todo_lists page is unavailable for unauthorized users."""
        response = self.client.get(reverse("planner:todo-lists", args=[]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_todo_lists_200_if_logged_in(self):
        """Test if todo_lists page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:todo-lists", args=[]))
        self.assertEqual(response_get.status_code, 200)

    def test_todo_lists_correct_template_if_logged_in(self):
        """Test if todo_lists page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:todo-lists", args=[]))
        self.assertTemplateUsed(response_get, "planner/planner_lists.html")

    def test_todo_lists_initial_values_set_context_data(self):
        """Test if todo_lists page displays correct context data."""
        full_todo_list = ToDoList.objects.filter(user=self.user).order_by("-updated")
        search_query = "john"
        if search_query:
            todo_list = ToDoList.objects.filter(user=self.user).filter(
                name__icontains=search_query).order_by("-updated")
        else:
            todo_list = full_todo_list
        page_number = 1
        paginator_todo = Paginator(todo_list, per_page=10)
        page_object_todo = paginator_todo.get_page(page_number)

        self.client.force_login(self.user)
        response_get = self.client.get(reverse("planner:todo-lists", args=[]))
        self.assertEqual(response_get.context["page_name"], "todo-lists")
        # self.assertEqual(response_get.context["paginator"], paginator_todo)
        self.assertEqual(response_get.context["page_obj"], page_object_todo)
        self.assertQuerysetEqual(response_get.context["todo_list"], todo_list)
        self.assertQuerysetEqual(response_get.context["full_todo_list"], full_todo_list)
        self.assertEqual(response_get.context["search_query"], search_query)

    def test_todo_lists_initial_values_set_todo_data(self):
        """Test if logged user can see data for todo_lists without seeing
        data of other users."""
        new_todo_list = ToDoListFactory(user=self.user, name="new todo list")

        # Test content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("planner:todo-lists", args=[]))

        user = User.objects.get(id=self.client.session["_auth_user_id"])
        self.assertEqual(user, self.user)

        self.assertIn("johndoe123", response_get.content.decode())
        self.assertIn(self.todo_list.name, response_get.content.decode())
        self.assertIn(new_todo_list.name, response_get.content.decode())
        self.assertNotIn("testuser", response_get.content.decode())
        self.assertNotIn(self.test_todo_list.name, response_get.content.decode())

        self.client.logout()

        # Test content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("planner:todo-lists", args=[]))

        user = User.objects.get(id=self.client.session["_auth_user_id"])
        self.assertEqual(user, self.test_user)

        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertNotIn(self.todo_list.name, response_get.content.decode())
        self.assertNotIn(new_todo_list.name, response_get.content.decode())
        self.assertIn("testuser", response_get.content.decode())
        self.assertIn(self.test_todo_list.name, response_get.content.decode())

    def test_todo_lists_pages(self):
        """Test if paginator is working correctly."""
        for todo_list_number in range(11):
            ToDoListFactory(user=self.user, name=str(todo_list_number))
        self.assertEqual(ToDoList.objects.filter(user=self.user).count(), 12)

        todo_list = ToDoList.objects.filter(user=self.user).order_by(
            "updated")
        paginator_todo = Paginator(todo_list, per_page=10)
        first_page = paginator_todo.page(1)

        self.assertEqual(paginator_todo.count, 12)
        self.assertEqual(paginator_todo.num_pages, 2)
        self.assertFalse(first_page.has_previous())
        self.assertTrue(first_page.has_next())
        self.assertEqual(first_page.start_index(), 1)
        self.assertEqual(first_page.end_index(), 10)
        # self.assertEqual(paginator_todo.get_page(1), first_page)

        self.client.force_login(self.user)
        response_get = self.client.get(reverse("planner:todo-lists", args=[]))
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(response_get.context["page_obj"], str(paginator_todo.page(1)))

    def test_todo_lists_search_engine(self):
        """Test if filtering queryset by search engine is working correctly."""
        for todo_list_number in range(12):
            ToDoListFactory(user=self.user, name=str(todo_list_number))
        self.assertEqual(ToDoList.objects.filter(user=self.user).count(), 13)

        search_query = "1"  # expense_lists_result = [1, 10, 11]
        todo_list = ToDoList.objects.filter(
            user=self.user).filter(
            name__icontains=search_query).order_by(
            "updated")
        paginator_expense = Paginator(todo_list, per_page=10)

        self.assertEqual(todo_list.count(), 3)
        self.assertEqual(paginator_expense.count, 3)
        self.assertEqual(paginator_expense.num_pages, 1)


class ExpenseListViewTest(TestCase):
    """Test ExpenseList views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass456")
        self.expense_list = ExpenseListFactory(user=self.user, name="setup list name")
        self.test_expense_list = ExpenseListFactory(user=self.test_user, name="test list name")
        self.expense_item = ExpenseItemFactory(
            user=self.user, expense_list=self.expense_list, name="setup item name")
        self.test_expense_item = ExpenseItemFactory(
            user=self.test_user, expense_list=self.test_expense_list, name="test item name")

        self.payload = {
            "name": "New setup expense list",
            "access_granted": Access.ACCESS_GRANTED
        }

    def test_all_setup_instances_created(self):
        """Test if user account and expense model was created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(ExpenseList.objects.count(), 2)
        self.assertEqual(ExpenseItem.objects.count(), 2)

    def test_single_expense_list_302_redirect_if_unauthorized(self):
        """ Test if single_expense_list page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("planner:single-expense-list", args=[self.expense_list.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    def test_single_expense_list_200_if_logged_in(self):
        """Test if single_expense_list page return status code 200 for
        authenticated user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:single-expense-list", args=[self.expense_list.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_single_expense_list_correct_template_if_logged_in(self):
        """Test if single_expense_list page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:single-expense-list", args=[self.expense_list.id]))
        self.assertTemplateUsed(
            response_get, "planner/single_list.html")

    def test_single_expense_list_initial_values_set_context_data(self):
        """Test if single_expense_list page displays correct context data."""
        list_title = ExpenseList.objects.get(user=self.user)
        expense_items = ExpenseItem.objects.filter(
            expense_list=list_title).order_by("name")
        estimated_costs = list_title.get_all_estimated_costs()
        paid_costs = list_title.get_all_paid_costs()

        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:single-expense-list", args=[str(self.expense_list.id)]))
        self.assertEqual(response_get.context["profile"], self.expense_list.user.profile)
        self.assertEqual(response_get.context["page"], "single-expense-list")
        self.assertQuerysetEqual(response_get.context["list_title"], list_title)
        self.assertQuerysetEqual(response_get.context["expense_items"], expense_items)
        self.assertEqual(round(response_get.context["estimated_costs"], 0), round(estimated_costs, 0))
        self.assertEqual(round(response_get.context["paid_costs"], 0), round(paid_costs, 0))

    def test_single_expense_list_initial_values_set_expense_list_data(self):
        """Test if single_expense_list page displays correct expense data
        and data associated to that list (only data of logged user)."""

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:single-expense-list", args=[self.expense_list.id]))

        self.assertIn(self.expense_list.name, response_get.content.decode())
        self.assertNotIn(self.test_expense_list.name, response_get.content.decode())
        self.assertIn(self.expense_item.name, response_get.content.decode())
        self.assertNotIn(self.test_expense_item.name, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("planner:single-expense-list", args=[self.test_expense_list.id]))

        self.assertNotIn(self.expense_list.name, response_get.content.decode())
        self.assertIn(self.test_expense_list.name, response_get.content.decode())
        self.assertNotIn(self.expense_item.name, response_get.content.decode())
        self.assertIn(self.test_expense_item.name, response_get.content.decode())

    def test_single_expense_list_forced_logout_if_security_breach(self):
        """Attempt to overview single expense list of another user is forbidden and
        triggers logout."""

        # Attempt to see self.test_user data by self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("planner:single-expense-list",
                    args=[self.test_expense_list.id]), follow=True)
        self.assertIn(self.test_expense_list.name, response_get.content.decode())
        self.client.logout()

        # Attempt to see self.test_user data by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:single-expense-list",
                    args=[self.test_expense_list.id]), follow=True)
        self.assertNotIn(self.test_expense_list.name, response_get.content.decode())
        self.assertRedirects(
            response_get,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_get.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do przeglądania tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

    def test_add_expense_list_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add expense list
        (user is redirected to login page)."""
        response = self.client.get(reverse("planner:add-expense-list"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_expense_list_200_if_logged_in(self):
        """Test if add_expense_list page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:add-expense-list"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_expense_list_correct_template_if_logged_in(self):
        """Test if add_expense_list page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:add-expense-list"))
        self.assertTemplateUsed(response_get, "planner/planner_form.html")

    def test_add_expense_list_form_initial_values_set_context_data(self):
        """Test if add_expense_list page displays correct context data."""
        list_names = list(ExpenseList.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:add-expense-list"))
        self.assertEqual(response_get.context["page"], "add-expense-list")
        self.assertQuerysetEqual(response_get.context["list_names"], list_names)
        self.assertIsInstance(response_get.context["form"], ExpenseListForm)

    def test_add_expense_list_form_initial_values_set_form_data(self):
        """Test if add_expense_list page displays correct form data."""
        list_fields = ["name", "access_granted"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:add-expense-list"))
        for field in list_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_expense_list_success_and_redirect(self):
        """Test if creating an expense list is successful (status code 200) and
        redirecting is successful (status code 302)."""
        list_names = list(ExpenseList.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.force_login(self.user)
        response_post = self.client.post(
            reverse("planner:add-expense-list"),
            data=self.payload,
            list_names=list_names,
            follow=True)
        self.assertEqual(response_post.status_code, 200)
        self.assertTemplateUsed(response_post, template_name="planner/planner_lists.html")

        self.assertRedirects(
            response_post,
            reverse("planner:expense-lists"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano listę wydatków.", str(messages[0]))
        self.assertInHTML("New setup expense list", response_post.content.decode())
        self.assertEqual(ExpenseList.objects.count(), 3)
        self.assertTrue(ExpenseList.objects.filter(
            user=self.user, name=self.payload["name"]).exists())

    def test_add_expense_list_successful_with_correct_user(self):
        """Test if creating an expense list successfully has correct user."""
        list_names = list(ExpenseList.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.force_login(self.user)
        self.client.post(reverse("planner:add-expense-list"),
                         data=self.payload,
                         list_names=list_names,
                         follow=True)
        expense_list = ExpenseList.objects.get(name=self.payload["name"])
        self.assertEqual(expense_list.user, self.user)

    @parameterized.expand(
        [
            ("Empty field: name",
             {"access_granted": Access.NO_ACCESS_GRANTED},
             "To pole jest wymagane."),
            ("Empty field: access_granted",
             {"name": "New name"},
             "To pole jest wymagane."),
            ("Not unique fields: name",
             {"name": "setup list name", "access_granted": Access.NO_ACCESS_GRANTED},
             "Istnieje już lista o podanej nazwie w bazie danych. Podaj inną nazwę."),
        ]
    )
    def test_add_expense_list_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating an expense list is not successful if data is incorrect."""
        self.client.force_login(self.user)
        list_names = list(ExpenseList.objects.filter(
            user=self.user).values_list("name", flat=True))
        response_post = self.client.post(
            reverse("planner:add-expense-list"),
            data=payload,
            list_names=list_names)
        self.assertEqual(ExpenseList.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_expense_list_302_redirect_if_unauthorized(self):
        """Test if edit_expense_list page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("planner:edit-expense-list", args=[self.expense_list.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_expense_list_200_if_logged_in(self):
        """Test if edit_expense_list page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:edit-expense-list", args=[self.expense_list.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_expense_list_correct_template_if_logged_in(self):
        """Test if edit_expense_list page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:edit-expense-list", args=[self.expense_list.id]))
        self.assertTemplateUsed(response_get, "planner/planner_form.html")

    def test_edit_expense_list_form_initial_values_set_context_data(self):
        """Test if edit_expense_list page displays correct context data."""
        list_names = list(ExpenseList.objects.filter(
            user=self.user).exclude(
            id=self.expense_list.id).values_list("name", flat=True))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:edit-expense-list", args=[str(self.expense_list.id)]))
        self.assertEqual(response_get.context["page"], "edit-expense-list")
        self.assertQuerysetEqual(response_get.context["list_title"], self.expense_list)
        self.assertQuerysetEqual(response_get.context["list_names"],
                                 list_names)
        self.assertIsInstance(response_get.context["form"], ExpenseListForm)

    def test_edit_expense_list_form_initial_values_set_form_data(self):
        """Test if edit_expense_list page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:edit-expense-list", args=[str(self.expense_list.id)]))
        self.assertIn(self.expense_list.name, response_get.content.decode())

    def test_edit_expense_list_success_and_redirect(self):
        """Test if updating an expense list is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        list_names = list(ExpenseList.objects.filter(
            user=self.user).exclude(
            id=self.expense_list.id).values_list("name", flat=True))

        payload = {
            "name": "yet another one",
            "access_granted": "Brak dostępu",
        }
        self.assertNotEqual(self.expense_list.name, payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("planner:edit-expense-list", args=[str(self.expense_list.id)]),
            data=payload,
            instance=self.expense_list,
            list_names=list_names,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("planner:single-expense-list",
                    args=[str(self.expense_list.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zmieniono nazwę listy wydatków.", str(messages[0]))
        self.expense_list.refresh_from_db()
        self.assertEqual(ExpenseList.objects.count(), 2)
        self.assertEqual(self.expense_list.access_granted, payload["access_granted"])
        self.assertEqual(self.expense_list.name, payload["name"])

    def test_edit_expense_list_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)
        list_names = list(ExpenseList.objects.filter(
            user=self.user).exclude(
            id=self.expense_list.id).values_list("name", flat=True))

        # PATCH
        payload = {
            "name": "yet another one",
        }
        response_patch = self.client.patch(
            reverse("planner:edit-expense-list", args=[str(self.expense_list.id)]),
            data=payload,
            instance=self.expense_list,
            list_names=list_names,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "name": "yet another one",
            "access_granted": Access.ACCESS_GRANTED,
        }
        response_put = self.client.put(
            reverse("planner:edit-expense-list",
                    args=[str(self.expense_list.id)]),
            data=payload,
            instance=self.expense_list,
            list_names=list_names,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("planner:edit-expense-list",
                    args=[str(self.expense_list.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_expense_list_logout_if_security_breach(self):
        """Editing expense list of another user is unsuccessful and triggers logout."""
        list_names = list(ExpenseList.objects.filter(
            user=self.user).exclude(
            id=self.expense_list.id).values_list("name", flat=True))

        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_expense_list.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "yet another one",
            "access_granted": Access.ACCESS_GRANTED,
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("planner:edit-expense-list",
                    args=[str(self.test_expense_list.id)]),
            data=payload,
            content_type="text/html",
            list_names=list_names,
            follow=True,
        )
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(ExpenseList.objects.count(), 2)
        self.assertNotIn(self.test_expense_list.name, payload["name"])

    def test_delete_expense_list_302_redirect_if_unauthorized(self):
        """Test if delete_expense_list page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("planner:delete-expense-list", args=[self.expense_list.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_expense_list_200_if_logged_in(self):
        """Test if delete_expense_list page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:delete-expense-list", args=[self.expense_list.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_expense_list_correct_template_if_logged_in(self):
        """Test if delete_expense_list page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:delete-expense-list", args=[self.expense_list.id]))
        self.assertTemplateUsed(response_get, "planner/planner_delete_form.html")

    def test_delete_expense_list_initial_values_set_context_data(self):
        """Test if delete_expense_list page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:delete-expense-list",
                    args=[str(self.expense_list.id)]))
        self.assertIn(str(self.expense_list), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-expense-list")
        self.assertQuerysetEqual(response_get.context["list_title"],
                                 self.expense_list)

    def test_delete_expense_list_successful_and_redirect(self):
        """Deleting expense list with all expense items is successful
        (status code 200) and redirect is successful (status code 302)."""
        self.client.force_login(self.user)
        response_delete = self.client.post(
            reverse("planner:delete-expense-list", args=[self.expense_list.id]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("planner:planner", args=[1]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto listę wydatków wraz z informacjami dodatkowymi.",
                      str(messages[0]))

        response = self.client.get(reverse("planner:planner", args=[1]))
        self.assertEqual(ExpenseList.objects.count(), 1)
        self.assertNotIn(self.expense_list.name, response.content.decode())
        self.assertNotIn(self.test_expense_list.name, response.content.decode())
        self.assertEqual(ExpenseItem.objects.count(), 1)

    def test_delete_expense_list_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("planner:delete-expense-list",
                    args=[str(self.expense_list.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("planner:delete-expense-list",
                    args=[str(self.expense_list.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("planner:delete-expense-list",
                    args=[str(self.expense_list.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_expense_list_logout_if_security_breach(self):
        """Deleting expense list of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(ExpenseList.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_expense_list.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("planner:delete-expense-list",
                    args=[str(self.test_expense_list.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do usunięcia tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(ExpenseList.objects.count(), 2)


class ExpenseItemViewTest(TestCase):
    """Test ExpenseItem views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com",
            password="testpass456")
        self.expense_list = ExpenseListFactory(user=self.user,
                                               name="setup list name")
        self.test_expense_list = ExpenseListFactory(user=self.test_user,
                                                    name="test list name")
        self.expense_item = ExpenseItemFactory(
            user=self.user, expense_list=self.expense_list,
            name="setup item name")
        self.test_expense_item = ExpenseItemFactory(
            user=self.test_user, expense_list=self.test_expense_list,
            name="test item name")

        self.payload = {
            # "expense_list": "",  # hidden form field scenario
            "name": "New setup expense item",
            "description": "Must have",
            "estimated_cost": 555.55,
            "execution_status": ExecutionStatus.PLANNED,
            "requirement_status": RequirementStatus.REQUIRED,
            "validity_status": ValidityStatus.URGENT,
            "cost_paid": 666.66,
            "purchase_date": datetime.date(2020, 11, 11)
        }

    def test_all_setup_instances_created(self):
        """Test if user account and expense model was created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(ExpenseList.objects.count(), 2)
        self.assertEqual(ExpenseItem.objects.count(), 2)

    def test_add_expense_item_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add expense item
        (user is redirected to login page)."""
        response = self.client.get(reverse("planner:add-expense-item",
                                           args=[str(self.expense_list.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_expense_item_result_200_if_logged_in(self):
        """Test if add_expense_item page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:add-expense-item", args=[str(self.expense_list.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_expense_item_correct_template_if_logged_in(self):
        """Test if add_expense_item page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:add-expense-item",
                                               args=[str(self.expense_list.id)]))
        self.assertTemplateUsed(response_get, "planner/planner_form.html")

    def test_add_expense_item_form_initial_values_set_context_data(self):
        """Test if add_expense_item page displays correct context data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:add-expense-item", args=[str(self.expense_list.id)]))
        self.assertEqual(response_get.context["page"], "add-expense-item")
        self.assertQuerysetEqual(response_get.context["list_title"], self.expense_list)
        self.assertIsInstance(response_get.context["form"], ExpenseItemForm)

    def test_add_expense_item_form_initial_values_set_form_data(self):
        """Test if add_expense_item page displays correct form data."""
        item_fields = [
            # "expense_list",
            "name", "description", "estimated_cost", "execution_status",
            "requirement_status", "validity_status", "cost_paid", "purchase_date"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:add-expense-item", args=[str(self.expense_list.id)]))
        for field in item_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_expense_item_success_and_redirect(self):
        """Test if creating expense item successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(ExpenseItem.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("planner:add-expense-item",
                    args=[str(self.expense_list.id)]),
            data=self.payload, follow=True)
        self.assertRedirects(
            response_post,
            reverse("planner:single-expense-list",
                    args=[str(self.expense_list.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano element do listy wydatków.",
                      str(messages[0]))
        self.assertInHTML(self.payload["description"],
                          response_post.content.decode())
        self.assertEqual(ExpenseItem.objects.count(), 3)
        self.assertTrue(ExpenseItem.objects.filter(
            user=self.user, cost_paid=self.payload["cost_paid"]).exists())

    def test_add_expense_item_successful_with_correct_user(self):
        """Test if creating expense item successfully has correct user."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("planner:add-expense-item",
                    args=[str(self.expense_list.id)]),
            self.payload, follow=True)

        expense = ExpenseItem.objects.get(description=self.payload["description"])
        self.assertEqual(expense.user, self.user)

    def test_add_expense_item_successful_with_correct_expense_list(self):
        """Test if creating expense item successfully has correct
        expense list as foreign key."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("planner:add-expense-item",
                    args=[str(self.expense_list.id)]),
            self.payload, follow=True)

        expense = ExpenseItem.objects.get(description=self.payload["description"])
        self.assertQuerysetEqual(expense.expense_list, self.expense_list)
        self.assertNotEqual(expense.expense_list, self.test_expense_list)

    @parameterized.expand(
        [
            ("Empty field: name",
             {"requirement_status": RequirementStatus.OPTIONAL},
             "To pole jest wymagane."),
            ("Incorrect date field",
             {"name": "some new item", "purchase_date": "2020/11/11"},
             "Wpisz poprawną datę."),
            ("Incorrect estimated_cost field (negative values are not allowed)",
             {"name": "some new item", "estimated_cost": -100},
             "Wartość nie może być liczbą ujemną."),
            ("Incorrect cost_paid field (negative values are not allowed)",
             {"name": "some new item", "cost_paid": -100},
             "Wartość nie może być liczbą ujemną."),
        ]
    )
    def test_add_expense_item_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating expense item is not successful if data is incorrect."""
        self.assertEqual(ExpenseItem.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("planner:add-expense-item",
                    args=[str(self.expense_list.id)]), data=payload)
        self.assertEqual(ExpenseItem.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_expense_item_302_redirect_if_unauthorized(self):
        """Test if edit_expense_item page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("planner:edit-expense-item", args=[self.expense_item.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_expense_item_200_if_logged_in(self):
        """Test if edit_expense_item page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:edit-expense-item", args=[self.expense_item.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_expense_item_correct_template_if_logged_in(self):
        """Test if edit_expense_item page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:edit-expense-item", args=[self.expense_item.id]))
        self.assertTemplateUsed(response_get, "planner/planner_form.html")

    def test_edit_expense_item_form_initial_values_set_context_data(self):
        """Test if edit_expense_item page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:edit-expense-item", args=[str(self.expense_item.id)]))
        self.assertEqual(response_get.context["page"], "edit-expense-item")
        # self.assertQuerysetEqual(response_get.context["expense_item"], self.expense_item)
        self.assertEqual(str(response_get.context["expense_item"]),
                         str(self.expense_item))
        self.assertEqual(str(response_get.context["list_title"]), str(self.expense_list))
        self.assertIsInstance(response_get.context["form"], ExpenseItemForm)

    def test_edit_expense_item_form_initial_values_set(self):
        """Test if edit_expense_item page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:edit-expense-item", args=[str(self.expense_item.id)]))
        self.assertIn(self.expense_item.description, response_get.content.decode())
        self.assertIn(self.expense_item.name, response_get.content.decode())

    def test_edit_expense_item_success_and_redirect(self):
        """Test if updating expense item is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        self.assertNotEqual(self.expense_item.description,
                            self.payload["description"])
        self.assertNotEqual(self.expense_item.name, self.payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("planner:edit-expense-item", args=[str(self.expense_item.id)]),
            data=self.payload,
            instance=self.expense_item,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("planner:single-expense-list", args=[str(self.expense_list.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zmieniono element listy wydatków.", str(messages[0]))
        self.expense_item.refresh_from_db()
        self.assertEqual(ExpenseItem.objects.count(), 2)
        self.assertEqual(self.expense_item.name, self.payload["name"])
        self.assertEqual(self.expense_item.description, self.payload["description"])

    def test_edit_expense_item_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "Some new name for expense item",
            "description": "Do I really need this?",
        }
        response_patch = self.client.patch(
            reverse("planner:edit-expense-item", args=[str(self.expense_item.id)]),
            data=payload,
            instance=self.expense_item,
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "name": "Some new name for expense item",
            "description": "Do I really need this?",
            "estimated_cost": 111.11,
            "execution_status": ExecutionStatus.PLANNED,
            "requirement_status": RequirementStatus.REQUIRED,
            "validity_status": ValidityStatus.URGENT,
            "cost_paid": 222.22,
            "purchase_date": datetime.date(2020, 10, 10),
        }
        response_put = self.client.put(
            reverse("planner:edit-expense-item", args=[str(self.expense_item.id)]),
            data=payload,
            instance=self.expense_item,
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("planner:edit-expense-item",
                    args=[str(self.expense_item.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_expense_item_logout_if_security_breach(self):
        """Editing expense_item of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_expense_item.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "description": "SECURITY BREACH",
            "estimated_cost": 111.11,
            "execution_status": ExecutionStatus.PLANNED,
            "requirement_status": RequirementStatus.REQUIRED,
            "validity_status": ValidityStatus.URGENT,
            "cost_paid": 222.22,
            "purchase_date": datetime.date(2020, 10, 10),
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("planner:edit-expense-item",
                    args=[str(self.test_expense_item.id)]),
            data=payload,
            content_type="text/html",
            follow=True, )
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(ExpenseItem.objects.count(), 2)
        self.assertNotIn(self.test_expense_item.name, payload["name"])

    def test_delete_expense_item_302_redirect_if_unauthorized(self):
        """Test if delete_expense_item page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("planner:delete-expense-item", args=[self.expense_item.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_expense_item_200_if_logged_in(self):
        """Test if delete_expense_item page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:delete-expense-item", args=[self.expense_item.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_expense_item_correct_template_if_logged_in(self):
        """Test if delete_expense_item page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:delete-expense-item", args=[self.expense_item.id]))
        self.assertTemplateUsed(response_get,
                                "planner/planner_delete_form.html")

    def test_delete_expense_item_initial_values_set_context_data(self):
        """Test if delete_expense_item page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:delete-expense-item", args=[str(self.expense_item.id)]))
        self.assertEqual(response_get.context["page"], "delete-expense-item")
        # self.assertQuerysetEqual(response_get.context["expense_item"], self.expense_item)
        self.assertEqual(str(response_get.context["expense_item"]), str(self.expense_item))
        self.assertEqual(response_get.context["expense_list_id"],
                         self.expense_list.id)

    def test_delete_expense_item_and_redirect(self):
        """Deleting expense item is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(ExpenseItem.objects.count(), 2)
        self.client.force_login(self.user)

        response_delete = self.client.post(
            reverse("planner:delete-expense-item", args=[str(self.expense_item.id)]),
            content_type="text/html", follow=True,)
        self.assertRedirects(
            response_delete,
            reverse("planner:single-expense-list", args=[self.expense_list.id]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto element z listy wydatków.", str(messages[0]))

        response = self.client.get(
            reverse("planner:single-expense-list", args=[str(self.expense_list.id)]))
        self.assertEqual(ExpenseItem.objects.count(), 1)
        self.assertNotIn(self.expense_item.name, response.content.decode())
        self.assertNotIn(self.test_expense_item.name, response.content.decode())

    def test_delete_expense_item_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("planner:delete-expense-item",
                    args=[str(self.expense_item.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("planner:delete-expense-item",
                    args=[str(self.expense_item.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("planner:delete-expense-item",
                    args=[str(self.expense_item.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_expense_item_logout_if_security_breach(self):
        """Deleting expense item of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(ExpenseItem.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_expense_item.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("planner:delete-expense-item",
                    args=[str(self.test_expense_item.id)]),
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_delete,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do usunięcia tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(ExpenseItem.objects.count(), 2)


class ToDoListViewTest(TestCase):
    """Test ToDoList views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass456")
        self.todo_list = ToDoListFactory(user=self.user, name="setup list name")
        self.test_todo_list = ToDoListFactory(user=self.test_user, name="test list name")
        self.todo_item = ToDoItemFactory(
            user=self.user, todo_list=self.todo_list, name="setup item name")
        self.test_todo_item = ToDoItemFactory(
            user=self.test_user, todo_list=self.test_todo_list, name="test item name")

        self.payload = {
            "name": "New setup todo list",
            "access_granted": Access.ACCESS_GRANTED
        }

    def test_all_setup_instances_created(self):
        """Test if user account and 'to do' model was created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(ToDoList.objects.count(), 2)
        self.assertEqual(ToDoItem.objects.count(), 2)

    def test_single_todo_list_302_redirect_if_unauthorized(self):
        """ Test if single_todo_list page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("planner:single-todo-list", args=[self.todo_list.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    def test_single_todo_list_200_if_logged_in(self):
        """Test if single_todo_list page return status code 200 for
        authenticated user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:single-todo-list", args=[self.todo_list.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_single_todo_list_correct_template_if_logged_in(self):
        """Test if todo page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:single-todo-list", args=[self.todo_list.id]))
        self.assertTemplateUsed(
            response_get, "planner/single_list.html")

    def test_single_todo_list_initial_values_set_context_data(self):
        """Test if single_todo_list page displays correct context data."""
        list_title = ToDoList.objects.get(user=self.user)
        todo_items = ToDoItem.objects.filter(
            todo_list=list_title).order_by("name")

        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:single-todo-list", args=[str(self.todo_list.id)]))
        self.assertEqual(response_get.context["profile"], self.todo_list.user.profile)
        self.assertEqual(response_get.context["page"], "single-todo-list")
        self.assertQuerysetEqual(response_get.context["list_title"], list_title)
        self.assertQuerysetEqual(response_get.context["todo_items"], todo_items)

    def test_single_todo_list_initial_values_set_todo_list_data(self):
        """Test if single_todo_list page displays correct 'to do' data
        and data associated to that list (only data of logged user)."""

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:single-todo-list", args=[self.todo_list.id]))

        self.assertIn(self.todo_list.name, response_get.content.decode())
        self.assertNotIn(self.test_todo_list.name, response_get.content.decode())
        self.assertIn(self.todo_item.name, response_get.content.decode())
        self.assertNotIn(self.test_todo_item.name, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("planner:single-todo-list", args=[self.test_todo_list.id]))

        self.assertNotIn(self.todo_list.name, response_get.content.decode())
        self.assertIn(self.test_todo_list.name, response_get.content.decode())
        self.assertNotIn(self.todo_item.name, response_get.content.decode())
        self.assertIn(self.test_todo_item.name, response_get.content.decode())

    def test_single_todo_list_forced_logout_if_security_breach(self):
        """Attempt to overview single 'to do' list of another user is forbidden and
        triggers logout."""

        # Attempt to see self.test_user data by self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("planner:single-todo-list",
                    args=[self.test_todo_list.id]), follow=True)
        self.assertIn(self.test_todo_list.name, response_get.content.decode())
        self.client.logout()

        # Attempt to see self.test_user data by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:single-todo-list",
                    args=[self.test_todo_list.id]), follow=True)
        self.assertNotIn(self.test_todo_list.name, response_get.content.decode())
        self.assertRedirects(
            response_get,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_get.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do przeglądania tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

    def test_add_todo_list_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add 'to do' list
        (user is redirected to login page)."""
        response = self.client.get(reverse("planner:add-todo-list"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_todo_list_200_if_logged_in(self):
        """Test if add_todo_list page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:add-todo-list"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_todo_list_correct_template_if_logged_in(self):
        """Test if add_todo_list page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:add-todo-list"))
        self.assertTemplateUsed(response_get, "planner/planner_form.html")

    def test_add_todo_list_form_initial_values_set_context_data(self):
        """Test if add_todo_list page displays correct context data."""
        list_names = list(ToDoList.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:add-todo-list"))
        self.assertEqual(response_get.context["page"], "add-todo-list")
        self.assertQuerysetEqual(response_get.context["list_names"], list_names)
        self.assertIsInstance(response_get.context["form"], ToDoListForm)

    def test_add_todo_list_form_initial_values_set_form_data(self):
        """Test if add_todo_list page displays correct form data."""
        list_fields = ["name", "access_granted"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:add-todo-list"))
        for field in list_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_todo_list_success_and_redirect(self):
        """Test if creating an 'to do' list is successful (status code 200) and
        redirecting is successful (status code 302)."""
        list_names = list(ToDoList.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.force_login(self.user)
        response_post = self.client.post(
            reverse("planner:add-todo-list"),
            data=self.payload,
            list_names=list_names,
            follow=True)
        self.assertEqual(response_post.status_code, 200)
        self.assertTemplateUsed(response_post,
                                template_name="planner/planner_lists.html")

        self.assertRedirects(
            response_post,
            reverse("planner:todo-lists"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano listę zadań.", str(messages[0]))
        self.assertInHTML("New setup todo list", response_post.content.decode())
        self.assertEqual(ToDoList.objects.count(), 3)
        self.assertTrue(ToDoList.objects.filter(
            user=self.user, name=self.payload["name"]).exists())

    def test_add_todo_list_successful_with_correct_user(self):
        """Test if creating 'to do' list successfully has correct user."""
        list_names = list(ToDoList.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.force_login(self.user)
        self.client.post(reverse("planner:add-todo-list"),
                         data=self.payload,
                         list_names=list_names,
                         follow=True)
        todo_list = ToDoList.objects.get(name=self.payload["name"])
        self.assertEqual(todo_list.user, self.user)

    @parameterized.expand(
        [
            ("Empty field: name",
             {"access_granted": "Brak dostępu"},
             "To pole jest wymagane."),
            ("Empty field: access_granted",
             {"name": "New name"},
             "To pole jest wymagane."),
            ("Not unique fields: name",
             {"name": "setup list name", "access_granted": "Brak dostępu"},
             "Istnieje już lista o podanej nazwie w bazie danych. Podaj inną nazwę."),
        ]
    )
    def test_add_todo_list_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating an 'to do' list is not successful if data is incorrect."""
        self.client.force_login(self.user)
        list_names = list(ToDoList.objects.filter(
            user=self.user).values_list("name", flat=True))
        response_post = self.client.post(
            reverse("planner:add-todo-list"),
            data=payload,
            list_names=list_names)
        self.assertEqual(ToDoList.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_todo_list_302_redirect_if_unauthorized(self):
        """Test if edit_todo_list page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("planner:edit-todo-list", args=[self.todo_list.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_todo_list_200_if_logged_in(self):
        """Test if edit_todo_list page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:edit-todo-list", args=[self.todo_list.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_todo_list_correct_template_if_logged_in(self):
        """Test if edit_todo_list page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:edit-todo-list", args=[self.todo_list.id]))
        self.assertTemplateUsed(response_get, "planner/planner_form.html")

    def test_edit_todo_list_form_initial_values_set_context_data(self):
        """Test if edit_todo_list page displays correct context data."""
        list_names = list(ToDoList.objects.filter(
            user=self.user).exclude(
            id=self.todo_list.id).values_list("name", flat=True))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:edit-todo-list", args=[str(self.todo_list.id)]))
        self.assertEqual(response_get.context["page"], "edit-todo-list")
        self.assertQuerysetEqual(response_get.context["list_title"], self.todo_list)
        self.assertQuerysetEqual(response_get.context["list_names"],
                                 list_names)
        self.assertIsInstance(response_get.context["form"], ToDoListForm)

    def test_edit_todo_list_form_initial_values_set_form_data(self):
        """Test if edit_etodo_list page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:edit-todo-list", args=[str(self.todo_list.id)]))
        self.assertIn(self.todo_list.name, response_get.content.decode())

    def test_edit_todo_list_success_and_redirect(self):
        """Test if updating an 'to do' list is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        list_names = list(ToDoList.objects.filter(
            user=self.user).exclude(
            id=self.todo_list.id).values_list("name", flat=True))

        payload = {
            "name": "yet another one",
            "access_granted": "Brak dostępu",
        }
        self.assertNotEqual(self.todo_list.name, payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("planner:edit-todo-list", args=[str(self.todo_list.id)]),
            data=payload,
            instance=self.todo_list,
            list_names=list_names,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("planner:single-todo-list",
                    args=[str(self.todo_list.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zmieniono nazwę listy zadań.", str(messages[0]))
        self.todo_list.refresh_from_db()
        self.assertEqual(ToDoList.objects.count(), 2)
        self.assertEqual(self.todo_list.access_granted, payload["access_granted"])
        self.assertEqual(self.todo_list.name, payload["name"])

    def test_edit_todo_list_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)
        list_names = list(ToDoList.objects.filter(
            user=self.user).exclude(
            id=self.todo_list.id).values_list("name", flat=True))

        # PATCH
        payload = {
            "name": "yet another one",
        }
        response_patch = self.client.patch(
            reverse("planner:edit-todo-list", args=[str(self.todo_list.id)]),
            data=payload,
            instance=self.todo_list,
            list_names=list_names,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "name": "yet another one",
            "access_granted": Access.ACCESS_GRANTED,
        }
        response_put = self.client.put(
            reverse("planner:edit-todo-list",
                    args=[str(self.todo_list.id)]),
            data=payload,
            instance=self.todo_list,
            list_names=list_names,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("planner:edit-todo-list",
                    args=[str(self.todo_list.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_todo_list_logout_if_security_breach(self):
        """Editing 'to do' list of another user is unsuccessful and triggers logout."""
        list_names = list(ToDoList.objects.filter(
            user=self.user).exclude(
            id=self.todo_list.id).values_list("name", flat=True))

        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_todo_list.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "yet another one",
            "access_granted": "Udostępnij dane",
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("planner:edit-todo-list",
                    args=[str(self.test_todo_list.id)]),
            data=payload,
            content_type="text/html",
            list_names=list_names,
            follow=True,
        )
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(ToDoList.objects.count(), 2)
        self.assertNotIn(self.test_todo_list.name, payload["name"])

    def test_delete_todo_list_302_redirect_if_unauthorized(self):
        """Test if delete_todo_list page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("planner:delete-todo-list", args=[self.todo_list.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_etodo_list_200_if_logged_in(self):
        """Test if delete_todo_list page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:delete-todo-list", args=[self.todo_list.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_todo_list_correct_template_if_logged_in(self):
        """Test if delete_todo_list page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:delete-todo-list", args=[self.todo_list.id]))
        self.assertTemplateUsed(response_get, "planner/planner_delete_form.html")

    def test_delete_todo_list_initial_values_set_context_data(self):
        """Test if delete_todo_list page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:delete-todo-list",
                    args=[str(self.todo_list.id)]))
        self.assertIn(str(self.todo_list), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-todo-list")
        self.assertQuerysetEqual(response_get.context["list_title"],
                                 self.todo_list)

    def test_delete_todo_list_successful_and_redirect(self):
        """Deleting 'to do' list with all 'to do' items is successful
        (status code 200) and redirect is successful (status code 302)."""
        self.client.force_login(self.user)
        response_delete = self.client.post(
            reverse("planner:delete-todo-list", args=[self.todo_list.id]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("planner:planner", args=[1]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto listę zadań wraz z informacjami dodatkowymi.",
                      str(messages[0]))

        response = self.client.get(reverse("planner:planner", args=[1]))
        self.assertEqual(ToDoList.objects.count(), 1)
        self.assertNotIn(self.todo_list.name, response.content.decode())
        self.assertNotIn(self.test_todo_list.name, response.content.decode())
        self.assertEqual(ToDoItem.objects.count(), 1)

    def test_delete_todo_list_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("planner:delete-todo-list",
                    args=[str(self.todo_list.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("planner:delete-todo-list",
                    args=[str(self.todo_list.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("planner:delete-todo-list",
                    args=[str(self.todo_list.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_todo_list_logout_if_security_breach(self):
        """Deleting 'to do' list of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(ToDoList.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_todo_list.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("planner:delete-todo-list",
                    args=[str(self.test_todo_list.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do usunięcia tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(ToDoList.objects.count(), 2)


class ToDoItemViewTest(TestCase):
    """Test ToDoItem views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com",
            password="testpass456")
        self.todo_list = ToDoListFactory(user=self.user,
                                         name="setup list name")
        self.test_todo_list = ToDoListFactory(user=self.test_user,
                                              name="test list name")
        self.todo_item = ToDoItemFactory(
            user=self.user, todo_list=self.todo_list,
            name="setup item name")
        self.test_todo_item = ToDoItemFactory(
            user=self.test_user, todo_list=self.test_todo_list,
            name="test item name")

        self.payload = {
            # "todo_list": self.todo_list,  # hidden form field scenario
            "name": "New setup todo item",
            "description": "Must do",
            "execution_status": ExecutionStatus.PLANNED,
            "requirement_status": RequirementStatus.REQUIRED,
            "validity_status": ValidityStatus.URGENT,
            "due_date": datetime.date(2020, 11, 11)
        }

    def test_all_setup_instances_created(self):
        """Test if user account and 'to do' model was created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(ToDoList.objects.count(), 2)
        self.assertEqual(ToDoItem.objects.count(), 2)

    def test_add_todo_item_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add 'to do' item
        (user is redirected to login page)."""
        response = self.client.get(reverse("planner:add-todo-item",
                                           args=[str(self.todo_list.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_todo_item_result_200_if_logged_in(self):
        """Test if add_todo_item page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:add-todo-item", args=[str(self.todo_list.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_todo_item_correct_template_if_logged_in(self):
        """Test if add_todo_item page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("planner:add-todo-item",
                                               args=[str(self.todo_list.id)]))
        self.assertTemplateUsed(response_get, "planner/planner_form.html")

    def test_add_todo_item_form_initial_values_set_context_data(self):
        """Test if add_todo_item page displays correct context data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:add-todo-item", args=[str(self.todo_list.id)]))
        self.assertEqual(response_get.context["page"], "add-todo-item")
        self.assertQuerysetEqual(response_get.context["list_title"], self.todo_list)
        self.assertIsInstance(response_get.context["form"], ToDoItemForm)

    def test_add_todo_item_form_initial_values_set_form_data(self):
        """Test if add_todo_item page displays correct form data."""
        item_fields = [
            # "todo_list",
            "name", "description", "execution_status", "requirement_status",
            "validity_status", "due_date"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:add-todo-item", args=[str(self.todo_list.id)]))
        for field in item_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_todo_item_success_and_redirect(self):
        """Test if creating 'to do' item successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(ToDoItem.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("planner:add-todo-item",
                    args=[str(self.todo_list.id)]),
            data=self.payload, follow=True)
        self.assertRedirects(
            response_post,
            reverse("planner:single-todo-list",
                    args=[str(self.todo_list.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano element do listy zadań.",
                      str(messages[0]))
        self.assertInHTML(self.payload["description"],
                          response_post.content.decode())
        self.assertEqual(ToDoItem.objects.count(), 3)
        self.assertTrue(ToDoItem.objects.filter(
            user=self.user, description=self.payload["description"]).exists())

    def test_add_todo_item_successful_with_correct_user(self):
        """Test if creating 'to do' item successfully has correct user."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("planner:add-todo-item",
                    args=[str(self.todo_list.id)]),
            self.payload, follow=True)

        todo = ToDoItem.objects.get(description=self.payload["description"])
        self.assertEqual(todo.user, self.user)

    def test_add_todo_item_successful_with_correct_todo_list(self):
        """Test if creating 'to do' item successfully has correct
        'to do' list as foreign key."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("planner:add-todo-item",
                    args=[str(self.todo_list.id)]),
            self.payload, follow=True)

        todo = ToDoItem.objects.get(description=self.payload["description"])
        self.assertQuerysetEqual(todo.todo_list, self.todo_list)
        self.assertNotEqual(todo.todo_list, self.test_todo_list)

    @parameterized.expand(
        [
            ("Empty field: name",
             {"requirement_status": RequirementStatus.OPTIONAL},
             "To pole jest wymagane."),
            ("Incorrect date field",
             {"name": "some new item", "due_date": "2020/11/11"},
             "Wpisz poprawną datę."),
        ]
    )
    def test_add_todo_item_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating 'to do' item is not successful if data is incorrect."""
        self.assertEqual(ToDoItem.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("planner:add-todo-item",
                    args=[str(self.todo_list.id)]), data=payload)
        self.assertEqual(ToDoItem.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_todo_item_302_redirect_if_unauthorized(self):
        """Test if edit_todo_item page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("planner:edit-todo-item", args=[self.todo_item.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_todo_item_200_if_logged_in(self):
        """Test if edit_todo_item page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:edit-todo-item", args=[self.todo_item.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_todo_item_correct_template_if_logged_in(self):
        """Test if edit_todo_item page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:edit-todo-item", args=[self.todo_item.id]))
        self.assertTemplateUsed(response_get, "planner/planner_form.html")

    def test_edit_todo_item_form_initial_values_set_context_data(self):
        """Test if edit_todo_item page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:edit-todo-item", args=[str(self.todo_item.id)]))
        self.assertEqual(response_get.context["page"], "edit-todo-item")
        # self.assertQuerysetEqual(response_get.context["todo_item"], self.todo_item)
        self.assertEqual(str(response_get.context["todo_item"]),
                         str(self.todo_item))
        self.assertEqual(str(response_get.context["list_title"]), str(self.todo_list))
        self.assertIsInstance(response_get.context["form"], ToDoItemForm)

    def test_edit_todo_item_form_initial_values_set(self):
        """Test if edit_todo_item page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:edit-todo-item", args=[str(self.todo_item.id)]))
        self.assertIn(self.todo_item.description, response_get.content.decode())
        self.assertIn(self.todo_item.name, response_get.content.decode())

    def test_edit_todo_item_success_and_redirect(self):
        """Test if updating 'to do' item is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        self.assertNotEqual(self.todo_item.description,
                            self.payload["description"])
        self.assertNotEqual(self.todo_item.name, self.payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("planner:edit-todo-item", args=[str(self.todo_item.id)]),
            data=self.payload,
            instance=self.todo_item,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("planner:single-todo-list", args=[str(self.todo_list.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zmieniono element listy zadań.", str(messages[0]))
        self.todo_item.refresh_from_db()
        self.assertEqual(ToDoItem.objects.count(), 2)
        self.assertEqual(self.todo_item.name, self.payload["name"])
        self.assertEqual(self.todo_item.description, self.payload["description"])

    def test_edit_todo_item_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "Some new name for todo item",
            "description": "Do I really need this?",
        }
        response_patch = self.client.patch(
            reverse("planner:edit-todo-item", args=[str(self.todo_item.id)]),
            data=payload,
            instance=self.todo_item,
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "name": "Some new name for todo item",
            "description": "Do I really need this?",
            "execution_status": ExecutionStatus.PLANNED,
            "requirement_status": RequirementStatus.REQUIRED,
            "validity_status": ValidityStatus.URGENT,
            "due_date": datetime.date(2020, 10, 10),
        }
        response_put = self.client.put(
            reverse("planner:edit-todo-item", args=[str(self.todo_item.id)]),
            data=payload,
            instance=self.todo_item,
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("planner:edit-todo-item",
                    args=[str(self.todo_item.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_todo_item_logout_if_security_breach(self):
        """Editing todo_item of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_todo_item.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "description": "SECURITY BREACH",
            "execution_status": ExecutionStatus.PLANNED,
            "requirement_status": RequirementStatus.REQUIRED,
            "validity_status": ValidityStatus.URGENT,
            "due_date": datetime.date(2020, 10, 10),
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("planner:edit-todo-item",
                    args=[str(self.test_todo_item.id)]),
            data=payload,
            content_type="text/html",
            follow=True, )
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(ToDoItem.objects.count(), 2)
        self.assertNotIn(self.test_todo_item.name, payload["name"])

    def test_delete_todo_item_302_redirect_if_unauthorized(self):
        """Test if delete_todo_item page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("planner:delete-todo-item", args=[self.todo_item.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_todo_item_200_if_logged_in(self):
        """Test if delete_etodo_item page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:delete-todo-item", args=[self.todo_item.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_todo_item_correct_template_if_logged_in(self):
        """Test if delete_todo_item page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("planner:delete-todo-item", args=[self.todo_item.id]))
        self.assertTemplateUsed(response_get,
                                "planner/planner_delete_form.html")

    def test_delete_todo_item_initial_values_set_context_data(self):
        """Test if delete_todo_item page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("planner:delete-todo-item", args=[str(self.todo_item.id)]))
        self.assertEqual(response_get.context["page"], "delete-todo-item")
        # self.assertQuerysetEqual(response_get.context["todo_item"], self.todo_item)
        self.assertEqual(str(response_get.context["todo_item"]), str(self.todo_item))
        self.assertEqual(response_get.context["todo_list_id"],
                         self.todo_list.id)

    def test_delete_todo_item_and_redirect(self):
        """Deleting 'to do' item is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(ToDoItem.objects.count(), 2)
        self.client.force_login(self.user)

        response_delete = self.client.post(
            reverse("planner:delete-todo-item", args=[str(self.todo_item.id)]),
            content_type="text/html", follow=True,)
        self.assertRedirects(
            response_delete,
            reverse("planner:single-todo-list", args=[self.todo_list.id]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto element z listy zadań.", str(messages[0]))

        response = self.client.get(
            reverse("planner:single-todo-list", args=[str(self.todo_list.id)]))
        self.assertEqual(ToDoItem.objects.count(), 1)
        self.assertNotIn(self.todo_item.name, response.content.decode())
        self.assertNotIn(self.test_todo_item.name, response.content.decode())

    def test_delete_todo_item_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("planner:delete-todo-item",
                    args=[str(self.todo_item.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("planner:delete-todo-item",
                    args=[str(self.todo_item.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("planner:delete-todo-item",
                    args=[str(self.todo_item.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_todo_item_logout_if_security_breach(self):
        """Deleting 'to do' item of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(ToDoItem.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_todo_item.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("planner:delete-todo-item",
                    args=[str(self.test_todo_item.id)]),
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_delete,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do usunięcia tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(ToDoItem.objects.count(), 2)
