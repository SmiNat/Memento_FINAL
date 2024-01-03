import datetime

from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from access.enums import Access
from user.factories import UserFactory
from .enums import (CreditType, InstallmentType, TypeOfInterest, Currency,
                   Frequency, InsuranceType, RepaymentAction, YesNo)
from .models import (Credit, CreditAdditionalCost, CreditCollateral,
                     CreditInsurance, CreditInterestRate, CreditTranche,
                     CreditEarlyRepayment)


class CreditFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    slug = Faker("slug")
    name = "Some credit name"
    credit_number = "KH456789"
    type = CreditType.CAR_LOAN
    currency = Currency.PLN
    credit_amount = 60000
    own_contribution = 0
    market_value = 60000
    credit_period = 60
    grace_period = 0
    installment_type = "Raty malejące"
    installment_frequency = "Miesięczne"
    total_installment = 0
    capital_installment = 1000
    type_of_interest = "Stałe"
    fixed_interest_rate = 6
    floating_interest_rate = 0
    bank_margin = 0
    interest_rate_benchmark = "Brak"
    date_of_agreement = datetime.date(2020, 1, 1)
    start_of_credit = datetime.date(2020, 2, 1)
    start_of_payment = datetime.date(2020, 3, 1)
    payment_day = 1
    provision = 5000
    credited_provision = YesNo.YES
    tranches_in_credit = YesNo.YES
    life_insurance_first_year = 800
    property_insurance_first_year = None
    collateral_required = YesNo.YES
    collateral_rate = 1
    notes = None
    access_granted = Access.ACCESS_GRANTED
    access_granted_for_schedule = Access.ACCESS_GRANTED
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = Credit


class CreditTrancheFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    credit = SubFactory(CreditFactory)
    tranche_amount = 10000
    tranche_date = datetime.date(2020, 5, 1)
    total_installment = None
    capital_installment = None
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = CreditTranche


class CreditInterestRateFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    credit = SubFactory(CreditFactory)
    interest_rate = 5
    interest_rate_start_date = datetime.date(2020, 8, 1)
    note = Faker("sentence", nb_words=6)
    total_installment = None
    capital_installment = None
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = CreditInterestRate


class CreditInsuranceFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    credit = SubFactory(CreditFactory)
    type = InsuranceType.PROPERTY_INSURANCE
    amount = 777
    frequency = Frequency.ANNUALLY
    start_date = datetime.date(2021, 1, 1)
    end_date = datetime.date(2025, 1, 1)
    payment_period = 1
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = CreditInsurance


class CreditCollateralFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    credit = SubFactory(CreditFactory)
    description = "Additional collateral"
    collateral_value = 750000
    collateral_set_date = datetime.date(2020, 9, 1)
    total_installment = None
    capital_installment = None
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = CreditCollateral


class CreditAdditionalCostFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    credit = SubFactory(CreditFactory)
    name = "Lawyer"
    cost_amount = 5500
    cost_payment_date = datetime.date(2020, 4, 15)
    notes = Faker("sentence", nb_words=6)
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = CreditAdditionalCost


class CreditEarlyRepaymentFactory(DjangoModelFactory):
    id = Faker("uuid4")
    user = SubFactory(UserFactory)
    credit = SubFactory(CreditFactory)
    repayment_amount = 10000
    repayment_date = datetime.date(2021, 2, 1)
    repayment_action = RepaymentAction.SHORTER_PAYMENT
    total_installment = None
    capital_installment = None
    created = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)
    updated = datetime.datetime(2020, 1, 1, 4, 1, 1, 1)

    class Meta:
        model = CreditEarlyRepayment
