import datetime

from factory import Faker, SubFactory
from factory.django import DjangoModelFactory, FileField, ImageField

from access.enums import Access
from user.factories import UserFactory
from .models import Counterparty, Attachment


class CounterpartyFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    name = "Test name"
    phone_number = "123 456 789"
    email = "test@example.com"
    address = "Backer Str."
    www = "https://stackoverflow.com/"
    bank_account = "PL 3210-0834-0000-9098-1000-5678"
    payment_app = None
    client_number = "KH2345"
    primary_contact_name = None
    primary_contact_phone_number = None
    primary_contact_email = "some_random@example.com"   # Faker("email")
    notes = Faker("sentence", nb_words=4)
    access_granted = Access.NO_ACCESS_GRANTED
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = Counterparty


class AttachmentFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    slug = Faker("slug")
    attachment_name = "Test name for attachment"
    attachment_path = ImageField()  # FileField but only for .pdf, .png, .jpg
    file_date = datetime.date(2020, 1, 1)
    file_info = Faker("text", max_nb_chars=10)
    access_granted = Access.NO_ACCESS_GRANTED
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = Attachment
