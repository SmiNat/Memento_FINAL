from django.db import models
from django.utils.translation import gettext_lazy as _


class YesNo(models.TextChoices):
    YES = _("Tak"), _("Tak")
    NO = _("Nie"), _("Nie")


class CreditType(models.TextChoices):
    HOME_LOAN = _("Mieszkaniowy"), _("Mieszkaniowy")
    CAR_LOAN = _("Samochodowy"), _("Samochodowy")
    CONSUMER_LOAN = _("Konsumpcyjny"), _("Konsumpcyjny")
    CONSOLIDATION_LOAN = _("Konsolidacyjny"), _("Konsolidacyjny")
    OTHER = _("Inny"), _("Inny")


class InstallmentType(models.TextChoices):
    EQUAL_INSTALLMENTS = _("Raty równe"), _("Raty równe")
    DECREASING_INSTALLMENTS = _("Raty malejące"), _("Raty malejące")


class TypeOfInterest(models.TextChoices):
    FIXED = _("Stałe"), _("Stałe")
    VARIABLE = _("Zmienne"), _("Zmienne")
    MIXED = _("Mieszane"), _("Mieszane")


class Currency(models.TextChoices):
    PLN = "PLN", "PLN"
    EUR = "EUR", "EUR"
    USD = "USD", "USD"
    CHF = "CHF", "CHF"
    GBP = "GBP", "GBP"
    OTHER = _("Inna"), _("Inna")


class Frequency(models.TextChoices):
    MONTHLY = _("Miesięczne"), _("Miesięczne")
    QUARTERLY = _("Kwartalne"), _("Kwartalne")
    SEMI_ANNUALLY = _("Półroczne"), _("Półroczne")
    ANNUALLY = _("Roczne"), _("Roczne")
    ONE_TIME = _("Jednorazowo"), _("Jednorazowo")


class InsuranceType(models.TextChoices):
    LIFE_INSURANCE = _("Ubezpieczenie na życie"), _("Ubezpieczenie na życie")
    PROPERTY_INSURANCE = _("Ubezpieczenie rzeczy/nieruchomości"), _("Ubezpieczenie rzeczy/nieruchomości")


class RepaymentAction(models.TextChoices):
    SHORTER_PAYMENT = _("Skrócenie kredytowania"), _("Skrócenie kredytowania")
    LOWER_PAYMENT = _("Zmniejszenie raty"), _("Zmniejszenie raty")