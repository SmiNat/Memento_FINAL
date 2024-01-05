from datetime import date
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (Credit, CreditInsurance, CreditCollateral,
                     CreditTranche, CreditAdditionalCost, CreditInterestRate,
                     CreditEarlyRepayment)


class CreditForm(forms.ModelForm):
    class Meta:
        model = Credit
        fields = [
            "name",
            "credit_number",
            "type",
            "currency",
            "credit_amount",
            "own_contribution",
            "market_value",
            "credit_period",
            "grace_period",
            "installment_type",
            "installment_frequency",
            "total_installment",
            "capital_installment",
            "type_of_interest",
            "fixed_interest_rate",
            "floating_interest_rate",
            "bank_margin",
            "interest_rate_benchmark",
            "date_of_agreement",
            "start_of_credit",
            "start_of_payment",
            "payment_day",
            "provision",
            "credited_provision",
            "tranches_in_credit",
            "life_insurance_first_year",
            "property_insurance_first_year",
            "collateral_required",
            "collateral_rate",
            "notes",
            "access_granted",
            "access_granted_for_schedule",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def __init__(self, *args, **kwargs):
        self.credit_names = kwargs.pop("credit_names")
        self.credit_names = list(name.lower() for name in self.credit_names)
        super(CreditForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        clean_name = self.cleaned_data.get("name", None)
        if not clean_name:
            self.add_error("name", {"required": _("To pole jest wymagane.")})
        elif clean_name.lower() in self.credit_names:
            self.add_error("name",
                           _("Istnieje już kredyt o podanej nazwie w bazie "
                             "danych. Podaj inną nazwę."))
        else:
            return clean_name

    def clean_credit_amount(self):
        credit_amount = self.cleaned_data.get("credit_amount", None)
        if not credit_amount:
            self.add_error("credit_amount",
                           {"required": _("To pole jest wymagane.")})
        elif credit_amount < 0:
            self.add_error("credit_amount",
                           _("Wartość nie może być liczbą ujemną."))
        else:
            return credit_amount

    def clean_own_contribution(self):
        own_contribution = self.cleaned_data.get("own_contribution", None)
        if own_contribution and own_contribution < 0:
            self.add_error("own_contribution",
                           _("Wartość nie może być liczbą ujemną."))
        else:
            return own_contribution

    def clean_market_value(self):
        market_value = self.cleaned_data.get("market_value", None)
        if market_value and market_value < 0:
            self.add_error("market_value",
                           _("Wartość nie może być liczbą ujemną."))
        else:
            return market_value

    def clean_collateral_rate(self):
        collateral_rate = self.cleaned_data.get("collateral_rate", None)
        if collateral_rate and collateral_rate < 0:
            self.add_error("collateral_rate",
                           _("Wartość nie może być liczbą ujemną."))
        else:
            return collateral_rate

    def clean_date_of_agreement(self):
        date_of_agreement = self.cleaned_data.get("date_of_agreement", None)
        if not date_of_agreement:
            self.add_error("date_of_agreement",
                           {"required": _("To pole jest wymagane.")})
        elif (date_of_agreement and isinstance(date_of_agreement, date)
                and date_of_agreement > date.today()):
            self.add_error("date_of_agreement",
                           _("Data zawarcia umowy nie może być późniejsza "
                             "niż bieżąca data."))
        else:
            return date_of_agreement

    def clean_start_of_credit(self):
        start_of_credit = self.cleaned_data.get("start_of_credit", None)
        if not start_of_credit:
            self.add_error("start_of_credit",
                           {"required": _("To pole jest wymagane.")})
        else:
            return start_of_credit

    def clean_start_of_payment(self):
        start_of_payment = self.cleaned_data.get("start_of_payment", None)
        if not start_of_payment:
            self.add_error("start_of_payment",
                           {"required": _("To pole jest wymagane.")})
        else:
            return start_of_payment

    def clean_provision(self):
        provision = self.cleaned_data.get("provision", None)
        if provision and provision < 0:
            self.add_error("provision",
                           _("Wartość nie może być liczbą ujemną."))
        else:
            return provision

    def clean_total_installment(self):
        installment_type = self.cleaned_data.get("installment_type", None)
        total_installment = self.cleaned_data.get("total_installment", None)
        if total_installment < 0:
            self.add_error(
                "total_installment", _("Wartość nie może być liczbą ujemną.")
            )
        elif installment_type == _("Raty równe") and float(total_installment) <= 0:
            self.add_error("total_installment",
                           _("Podaj wartość raty całkowitej dla kredytu."))
        else:
            return total_installment

    def clean_capital_installment(self):
        installment_type = self.cleaned_data.get("installment_type", None)
        capital_installment = self.cleaned_data.get("capital_installment", None)
        if capital_installment < 0:
            self.add_error(
                "capital_installment", _("Wartość nie może być liczbą ujemną.")
            )
        elif installment_type == _("Raty malejące") and float(capital_installment) <= 0:
            self.add_error("capital_installment",
                           _("Podaj wartość raty kapitałowej dla kredytu."))
        else:
            return capital_installment

    def clean_fixed_interest_rate(self):
        fixed_interest_rate = self.cleaned_data.get("fixed_interest_rate", None)
        type_of_interest = self.cleaned_data.get("type_of_interest", None)
        if fixed_interest_rate < 0:
            self.add_error(
                "fixed_interest_rate", _("Wartość nie może być liczbą ujemną.")
            )
        # credit 0%
        # elif type_of_interest == _("Stałe") and float(fixed_interest_rate) == 0:
        #     self.add_error("fixed_interest_rate",
        #                    {"required": _("Podaj wartość oprocentowania "
        #                                   "stałego dla kredytu.")})
        elif type_of_interest == _("Zmienne") and float(fixed_interest_rate) > 0:
            self.add_error("fixed_interest_rate",
                           _("Przy wyborze zmiennego oprocentowania wysokość "
                             "oprocentowania stałego powinna wynosić zero."))
        else:
            return fixed_interest_rate

    def clean_floating_interest_rate(self):
        type_of_interest = self.cleaned_data.get("type_of_interest", None)
        floating_interest_rate = self.cleaned_data.get("floating_interest_rate", None)
        if floating_interest_rate < 0:
            self.add_error(
                "floating_interest_rate", _("Wartość nie może być liczbą ujemną.")
            )
        # credit 0%
        # elif type_of_interest == _("Zmienne") and float(floating_interest_rate) == 0:
        #     self.add_error("floating_interest_rate",
        #                    {"required": _("Podaj wartość oprocentowania "
        #                                   "zmiennego dla kredytu.")})
        elif (type_of_interest == _("Stałe") and floating_interest_rate
              and float(floating_interest_rate) > 0):
            self.add_error("floating_interest_rate",
                           _("Przy wyborze stałego oprocentowania wysokość "
                             "oprocentowania zmiennego powinna wynosić zero."))
        else:
            return floating_interest_rate

    def clean_bank_margin(self):
        bank_margin = self.cleaned_data.get("bank_margin", None)
        type_of_interest = self.cleaned_data.get("type_of_interest", None)
        if bank_margin < 0:
            self.add_error("bank_margin", _("Wartość nie może być liczbą ujemną."))
        elif type_of_interest == _("Stałe") and float(bank_margin) > 0:
            self.add_error("bank_margin",
                           _("Przy wyborze stałego oprocentowania wysokość "
                             "marży banku powinna wynosić zero."))
        else:
            return bank_margin

    def clean(self):
        cleaned_data = super().clean()
        date_of_agreement = cleaned_data.get("date_of_agreement", None)
        start_of_credit = cleaned_data.get("start_of_credit", None)
        start_of_payment = cleaned_data.get("start_of_payment", None)
        provision = self.cleaned_data.get("provision", None)
        credited_provision = self.cleaned_data.get("credited_provision", None)
        collateral_rate = self.cleaned_data.get("collateral_rate", None)
        collateral_required = self.cleaned_data.get("collateral_required", None)
        access_granted_for_schedule = self.cleaned_data.get(
            "access_granted_for_schedule", None)
        access_granted = self.cleaned_data.get("access_granted", None)
        if (access_granted and access_granted == _("Brak dostępu") and
                access_granted_for_schedule == _("Udostępnij dane")):
            self.add_error("access_granted_for_schedule",
                           _("Nie można udzielić dostępu do harmonogramu "
                             "kredytu bez dostępu do danych kredytu."))
        if collateral_rate and float(collateral_rate) > 0:
            if collateral_required == _("Nie"):
                self.add_error(
                    "collateral_required",
                    _("Nie można ustanowić oprocentowania dodatkowego "
                      "(pomostowego) bez wymaganego zabezpieczenia kredytu. "
                      "Zmień warunki kredytowe.")
                )
        if credited_provision == _("Tak"):
            if not provision or provision < 0:
                self.add_error("provision",
                               _("Nie można wskazać kredytowania prowizji bez "
                                 "podania kwoty prowizji. Uzupełnij kwotę lub "
                                 "zmień warunki kredytowe."))

        if date_of_agreement and date_of_agreement > date.today():
            self.add_error(
                "date_of_agreement",
                _("Data zawarcia umowy nie może być późniejsza niż bieżąca data.")
            )
        if start_of_credit and date_of_agreement:
            if start_of_credit < date_of_agreement:
                self.add_error(
                    "start_of_credit",
                    _("Data uruchomienia kredytu nie może przypadać wcześniej "
                      "niż data zawarcia umowy kredytu.")
                )
        if start_of_payment and start_of_credit:
            if start_of_payment < start_of_credit:
                self.add_error(
                    "start_of_payment",
                    _("Data rozpoczęcia spłaty kredytu nie może przypadać "
                      "wcześniej niż data uruchomienia kredytu.")
                )
        if start_of_credit and start_of_credit:
            if start_of_payment == start_of_credit:
                self.add_error(
                    "start_of_payment",
                    _("Data uruchomienia kredytu i data rozpoczęcia spłaty nie "
                      "mogą być sobie równe. Spłata kredytu następuje po jego "
                      "uruchomieniu.")
                )
        if date_of_agreement and start_of_payment:
            if date_of_agreement > start_of_payment:
                self.add_error(
                    "start_of_payment",
                    _("Data rozpoczęcia spłaty nie może przypadać wcześniej "
                      "niż data zawarcia umowy.")
                )
        return cleaned_data

###############################################################################


class CreditTrancheForm(forms.ModelForm):

    class Meta:
        model = CreditTranche
        fields = [
            "tranche_amount",
            "tranche_date",
            "total_installment",
            "capital_installment",
        ]

    def __init__(self, *args, **kwargs):
        self.credit = kwargs.pop("credit")
        self.queryset = kwargs.pop("queryset")
        self.sum_of_tranches = kwargs.pop("sum_of_tranches")
        self.dates_of_tranches = kwargs.pop("dates_of_tranches")
        super(CreditTrancheForm, self).__init__(*args, **kwargs)

    def clean_tranche_date(self):
        tranche_date = self.cleaned_data.get("tranche_date", None)
        self.dates_of_tranches.append(tranche_date)
        if tranche_date and not isinstance(tranche_date, date):
            self.add_error("tranche_date",
                           _("Poprawny format to rok-miesiąc-dzień "
                             "(np. 2020-3-22)."))
        if not self.queryset:
            if tranche_date != self.credit.start_of_credit:
                self.add_error(
                    "tranche_date",
                    _("Data wypłaty pierwszej transzy musi być zgodna z datą "
                      "uruchomienia kredytu (%s)." % self.credit.start_of_credit)
                )
        if self.queryset:
            if self.credit.start_of_credit not in self.dates_of_tranches:
                self.add_error(
                    "tranche_date",
                    _("Nie można zmienić daty dla transzy inicjalnej. Jedna z "
                      "transz musi mieć datę zgodną z datą uruchomienia kredytu "
                      "(%s)." % self.credit.start_of_credit)
                )
        if tranche_date < self.credit.start_of_credit:
            self.add_error(
                "tranche_date",
                _("Data transzy nie może przypadać wcześniej niż data "
                  "uruchomienia kredytu.")
            )
        else:
            return tranche_date

    def clean_tranche_amount(self):
        tranche_amount = self.cleaned_data.get("tranche_amount", None)
        if (self.sum_of_tranches + tranche_amount) > (self.credit.credit_amount + 1):  # + 1 as a margin error
            self.add_error(
                "tranche_amount",
                _("Łączna wartość transz nie może przekraczać wartości kredytu wraz "
                  "z kredytowanym ubezpieczeniem czy prowizją"
                  "(%s). Suma dotychczasowych transz: %s. Sprawdź czy kwoty "
                  "transz obejmują wyłącznie wartość kredytu (bez kredytowanej "
                  "prowizji czy ubezpieczenia)."
                  % (self.credit.credit_amount(), self.sum_of_tranches))
            )
        else:
            return tranche_amount

    def clean_capital_installment(self):
        capital_installment = self.cleaned_data.get("capital_installment", None)
        if (capital_installment
                and self.credit.installment_type == _("Raty równe")
                and float(capital_installment) > 0):
            self.add_error(
                "capital_installment",
                _("W kredycie o ratach stałych (równych) nie można zmieniać rat "
                  "kapitałowych. Wprowadź raty całkowite lub zmień warunki kredytu.")
            )
        else:
            return capital_installment

    def clean_total_installment(self):
        total_installment = self.cleaned_data.get("total_installment", None)
        if (total_installment
                and self.credit.installment_type == _("Raty malejące")
                and float(total_installment) > 0):
            self.add_error(
                "total_installment",
                _("W kredycie o ratach malejących nie można zmieniać rat "
                  "całkowitych. Wprowadź raty kapitałowe lub zmień warunki kredytu.")
            )
        else:
            return total_installment

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504

###############################################################################


class CreditInterestRateForm(forms.ModelForm):

    class Meta:
        model = CreditInterestRate
        fields = [
            "interest_rate",
            "interest_rate_start_date",
            "note",
            "total_installment",
            "capital_installment",
        ]

    def __init__(self, *args, **kwargs):
        self.credit_id = kwargs.pop("credit_id")
        self.installment_type = kwargs.pop("installment_type")
        self.start_of_payment = kwargs.pop("start_of_payment")
        self.payment_day = kwargs.pop("payment_day")
        super(CreditInterestRateForm, self).__init__(*args, **kwargs)

    def clean_capital_installment(self):
        capital_installment = self.cleaned_data.get("capital_installment", None)
        if (capital_installment
                and self.installment_type == _("Raty równe")
                and float(capital_installment) > 0):
            self.add_error(
                "capital_installment",
                _("W kredycie o ratach stałych (równych) nie można zmieniać rat "
                  "kapitałowych. Wprowadź raty całkowite lub zmień warunki kredytu.")
            )
        else:
            return capital_installment

    def clean_total_installment(self):
        total_installment = self.cleaned_data.get("total_installment", None)
        if (total_installment
                and self.installment_type == _("Raty malejące")
                and float(total_installment) > 0):
            self.add_error(
                "total_installment",
                _("W kredycie o ratach malejących nie można zmieniać rat "
                  "całkowitych. Wprowadź raty kapitałowe lub zmień warunki kredytu.")
            )
        else:
            return total_installment

    def clean_interest_rate_start_date(self):
        interest_rate_start_date = self.cleaned_data.get("interest_rate_start_date", None)
        if self.start_of_payment > interest_rate_start_date:
            self.add_error(
                "interest_rate_start_date",
                _("Data benchmarku oprocentowania nie może przypadać wcześniej "
                  "niż data rozpoczęcia spłaty kredytu.")
            )
        elif interest_rate_start_date.day != self.payment_day:
            self.add_error(
                "interest_rate_start_date",
                _("Dzień w dacie rozpoczęcia naliczania nowego oprocentowania "
                  "musi być zgodny z dniem płatności raty (wybrany dzień: %s)."
                  % self.payment_day)
            )
        else:
            return interest_rate_start_date

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504

###############################################################################


class CreditInsuranceForm(forms.ModelForm):

    class Meta:
        model = CreditInsurance
        fields = [
            "type",
            "frequency",
            "amount",
            "start_date",
            "end_date",
            "payment_period",
            "notes"
        ]
        widgets = {
            "type": forms.Select(attrs={"class": "select_field"}),
            "frequency": forms.Select(attrs={"class": "select_field"}),
            "notes": forms.Textarea(attrs={"class": "textarea_field"})
        }

    def __init__(self, *args, **kwargs):
        self.start_of_credit = kwargs.pop("start_of_credit")
        super(CreditInsuranceForm, self).__init__(*args, **kwargs)

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date", None)
        if start_date and self.start_of_credit > start_date:
            self.add_error(
                "start_date",
                _("Data rozpoczęcia płatności ubezpieczenia nie może przypadać "
                  "wcześniej niż data udzielenia kredytu.")
            )
        else:
            return start_date

    def clean_end_date(self):
        start_date = self.cleaned_data.get("start_date", None)
        end_date = self.cleaned_data.get("end_date", None)
        if start_date and end_date and start_date > end_date:
            self.add_error(
               "end_date",
               _("Data zakończenia płatności ubezpieczenia nie może przypadać "
                 "wcześniej niż data rozpoczęcia płatności.")
            )
        else:
            return end_date

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504

###############################################################################


class CreditCollateralForm(forms.ModelForm):
    class Meta:
        model = CreditCollateral
        fields = [
            "description",
            "collateral_value",
            "collateral_set_date",
            "total_installment",
            "capital_installment",
        ]

    def __init__(self, *args, **kwargs):
        self.credit = kwargs.pop("credit")
        super(CreditCollateralForm, self).__init__(*args, **kwargs)

    # Technically, collateral_set_date can be set before date_of_agreement
    # def clean_collateral_set_date(self):
    #     collateral_set_date = self.cleaned_data.get("collateral_set_date", None)
    #     if self.credit.date_of_agreement > collateral_set_date:
    #         self.add_error(
    #             "collateral_set_date",
    #             _("Data ustanowienia zabezpieczenia nie może przypadać wcześniej "
    #               "niż data zawarcia umowy kredytu (%s)."
    #               % self.credit.date_of_agreement)
    #         )
    #     else:
    #         return collateral_set_date

    def clean_capital_installment(self):
        capital_installment = self.cleaned_data.get("capital_installment", None)
        if (capital_installment
                and self.credit.installment_type == _("Raty równe")
                and float(capital_installment) > 0):
            self.add_error(
                "capital_installment",
                _("W kredycie o ratach stałych (równych) nie można zmieniać rat "
                  "kapitałowych. Wprowadź raty całkowite lub zmień warunki kredytu.")
            )
        else:
            return capital_installment

    def clean_total_installment(self):
        total_installment = self.cleaned_data.get("total_installment", None)
        if (total_installment
                and self.credit.installment_type == _("Raty malejące")
                and float(total_installment) > 0):
            self.add_error(
                "total_installment",
                _("W kredycie o ratach malejących nie można zmieniać rat "
                  "całkowitych. Wprowadź raty kapitałowe lub zmień warunki kredytu.")
            )
        else:
            return total_installment

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504

###############################################################################


class CreditAdditionalCostForm(forms.ModelForm):
    class Meta:
        model = CreditAdditionalCost
        fields = [
            "name",
            "cost_amount",
            "cost_payment_date",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"class": "textarea_field"})
        }

    def __init__(self, *args, **kwargs):
        self.credit = kwargs.pop("credit")
        super(CreditAdditionalCostForm, self).__init__(*args, **kwargs)

    # In theory, user can pay additional costs of credit before credit agreement
    # (like cost of lawyer), but it will result in errors in credit schedule
    # (can be fixed in future)
    def clean_cost_payment_date(self):
        cost_payment_date = self.cleaned_data.get("cost_payment_date", None)
        if self.credit.date_of_agreement > cost_payment_date:
            self.add_error(
                "cost_payment_date",
                _("Data płatności (zwrotu) kosztu nie może przypadać wcześniej "
                  "niż data zawarcia umowy kredytu (%s)."
                  % self.credit.date_of_agreement)
            )
        else:
            return cost_payment_date

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504

###############################################################################


class CreditEarlyRepaymentForm(forms.ModelForm):

    class Meta:
        model = CreditEarlyRepayment
        fields = [
            "repayment_amount",
            "repayment_date",
            "repayment_action",
            "total_installment",
            "capital_installment",
        ]

    def __init__(self, *args, **kwargs):
        self.credit = kwargs.pop("credit")
        super(CreditEarlyRepaymentForm, self).__init__(*args, **kwargs)

    def clean_repayment_date(self):
        repayment_date = self.cleaned_data.get("repayment_date", None)
        if self.credit.start_of_payment > repayment_date:
            self.add_error(
                "repayment_date",
                _("Data nadpłaty nie może przypadać wcześniej niż data pierwszej "
                  "płatności raty (%s)." % self.credit.start_of_payment)
            )
        else:
            return repayment_date

    def clean_capital_installment(self):
        capital_installment = self.cleaned_data.get("capital_installment", None)
        if (capital_installment
                and self.credit.installment_type == _("Raty równe")
                and float(capital_installment) > 0):
            self.add_error(
                "capital_installment",
                _("W kredycie o ratach stałych (równych) nie można zmieniać rat "
                  "kapitałowych. Wprowadź raty całkowite lub zmień warunki kredytu.")
            )
        else:
            return capital_installment

    def clean_total_installment(self):
        total_installment = self.cleaned_data.get("total_installment", None)
        if (total_installment
                and self.credit.installment_type == _("Raty malejące")
                and float(total_installment) > 0):
            self.add_error(
                "total_installment",
                _("W kredycie o ratach malejących nie można zmieniać rat "
                  "całkowitych. Wprowadź raty kapitałowe lub zmień warunki kredytu.")
            )
        else:
            return total_installment

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504
