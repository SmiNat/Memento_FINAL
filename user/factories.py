import datetime

from factory import Faker, SubFactory
from factory.django import DjangoModelFactory
from django.utils.translation import gettext_lazy as _

from .models import User, Profile


class UserFactory(DjangoModelFactory):
    id = Faker("uuid4")
    username = "testuser"
    email = "test@example.com"
    password = "testpass456"

    class Meta:
        model = User


class ProfileFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    username = UserFactory.username
    email = UserFactory.email
    slug = Faker("slug")
    first_name = "Test"
    last_name = "Name"
    phone_number = "123-456-789"
    city = "New York"
    street = "Wall Street"
    building_number = "9"
    apartment_number = "11"
    post_code = "10001"
    country = "USA"
    access_granted_to = None
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = Profile
