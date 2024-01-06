import datetime

from factory.django import DjangoModelFactory
from factory import Faker, SubFactory

from access.enums import Access
from user.factories import UserFactory
from .enums import RequirementStatus, ValidityStatus, ExecutionStatus
from .models import ExpenseList, ExpenseItem, ToDoList, ToDoItem


class ExpenseListFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    name = "List name"
    access_granted = Access.NO_ACCESS_GRANTED
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = ExpenseList


class ExpenseItemFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    expense_list = SubFactory(ExpenseListFactory)
    name = "Item name 4 expense"
    description = "Test expense item"
    estimated_cost = 100
    execution_status = ExecutionStatus.PLANNED
    requirement_status = RequirementStatus.OPTIONAL
    validity_status = ValidityStatus.URGENT
    cost_paid = 80
    purchase_date = datetime.date(2021, 1, 1)
    created = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)

    class Meta:
        model = ExpenseItem


class ToDoListFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    name = "List name"
    access_granted = Access.NO_ACCESS_GRANTED
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = ToDoList


class ToDoItemFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    todo_list = SubFactory(ToDoListFactory)
    name = "To do item name"
    description = "Test item"
    execution_status = ExecutionStatus.PLANNED
    requirement_status = RequirementStatus.OPTIONAL
    validity_status = ValidityStatus.URGENT
    link = Faker("url")
    notes = Faker("sentence", nb_words=6)
    due_date = datetime.date(2021, 1, 1)
    created = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)

    class Meta:
        model = ToDoItem
