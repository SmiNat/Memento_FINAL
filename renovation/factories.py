import datetime

from factory.django import DjangoModelFactory
from factory import Faker, SubFactory

from access.enums import Access
from renovation.models import Renovation, RenovationCost
from user.factories import UserFactory


class RenovationFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    name = "Test name"
    description = "Test description"
    estimated_cost = 1000
    start_date = datetime.date(2020, 10, 10)
    end_date = datetime.date(2020, 10, 18)
    access_granted = Access.ACCESS_GRANTED
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = Renovation


class RenovationCostFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    renovation = SubFactory(RenovationFactory)
    name = "Renovation cost 1"
    unit_price = 100
    units = 5
    description = "Renovation first item cost"
    order = "Deliver to work address"
    created = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 11, 1, 4, 1, 1, 1)

    class Meta:
        model = RenovationCost
