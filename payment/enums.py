from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentMethod(models.TextChoices):
    TRANSFER_DIRECT_DEBIT = _("Przelew - polecenie zapłaty"), \
                            _("Przelew - polecenie zapłaty")
    TRANSFER_STANDING_ORDER = _("Przelew - zlecenie stałe"), \
                              _("Przelew - zlecenie stałe")
    TRANSFER_REGULAR = _("Przelew - zwykły przelew"), \
                       _("Przelew - zwykły przelew")
    TRANSFER_OTHER = _("Przelew - inny (blik, karta kredytowa)"), \
                     _("Przelew - inny (blik, karta kredytowa)")
    PAYMENT_AT_THE_POST_OFFICE = _("Płatność na poczcie"), \
                                 _("Płatność na poczcie")
    CASH_PAYMENT = _("Płatność gotówką"), _("Płatność gotówką")
    OTHER_PAYMENT = _("Inny rodzaj płatności"), _("Inny rodzaj płatności")


class PaymentType(models.TextChoices):
    UTILITY = _("Media"), _("Media")
    RENT = _("Czynsz"), _("Czynsz")
    TAX = _("Podatki"), _("Podatki")
    INSURANCE = _("Ubezpieczenie"), _("Ubezpieczenie")
    TELECOMMUNICATION = _("Telekomunikacja"), _("Telekomunikacja")
    TRANSPORT = _("Komunikacja"), _("Komunikacja")
    SAVINGS = _("Oszczędności"), _("Oszczędności")
    HEALTH = _("Zdrowie"), _("Zdrowie")
    ENTERTAINMENT = _("Rozrywka"), _("Rozrywka")
    EDUCATION = _("Edukacja"), _("Edukacja")
    DEBT = _("Kredyt/leasing"), _("Kredyt/leasing")
    OTHER = _("Inne"), _("Inne")


class PaymentStatus(models.TextChoices):
    PAID = _("Zapłacone"), _("Zapłacone")
    OVERDUE = _("Zaległe"), _("Zaległe")
    UNKNOWN = _("Brak informacji"), _("Brak informacji")


class PaymentFrequency(models.TextChoices):
    MONTHLY = _("Miesięcznie"), _("Miesięcznie")
    QUARTERLY = _("Kwartalnie"), _("Kwartalnie")
    SEMI_ANNUALLY = _("Półrocznie"), _("Półrocznie")
    ANNUALLY = _("Rocznie"), _("Rocznie")
    OTHER = _("Inne"), _("Inne")


class PaymentMonth(models.IntegerChoices):
    JANUARY = 1, _("Styczeń")
    FEBRUARY = 2, _("Luty")
    MARCH = 3, _("Marzec")
    APRIL = 4, _("Kwiecień")
    MAY = 5, _("Maj")
    JUNE = 6, _("Czerwiec")
    JULY = 7, _("Lipiec")
    AUGUST = 8, _("Sierpień")
    SEPTEMBER = 9, _("Wrzesień")
    OCTOBER = 10, _("Październik")
    NOVEMBER = 11, _("Listopad")
    DECEMBER = 12, _("Grudzień")
