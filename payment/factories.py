import datetime

from factory.django import DjangoModelFactory
from factory import Faker, SubFactory

from access.enums import Access
from user.factories import UserFactory
from .enums import (PaymentStatus, PaymentFrequency, PaymentMonth, PaymentType,
                    PaymentMethod)
from .models import Payment


class PaymentFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    name = "Test name"
    payment_type = "Media"
    payment_method = "Płatność gotówką"
    payment_status = "Brak informacji"
    payment_frequency = "Rocznie"
    payment_months = "2,4"
    payment_day = 15
    payment_value = round(1111.11, 2)
    notes = "Some payment notes"
    start_of_agreement = datetime.date(2020, 1, 1)
    end_of_agreement = datetime.date(2021, 1, 1)
    access_granted = Access.NO_ACCESS_GRANTED
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = Payment
