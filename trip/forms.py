import datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from .enums import (
    TripChoices,
    BasicChecklist,
    KeysChecklist,
    CosmeticsChecklist,
    ElectronicsChecklist,
    UsefulStaffChecklist,
    TrekkingChecklist,
    HikingChecklist,
    CyclingChecklist,
    CampingChecklist,
    FishingChecklist,
    SunbathingChecklist,
    BusinessChecklist,
    CostGroup,
)
from .models import (Trip, TripReport, TripCost, TripPersonalChecklist,
                     TripBasicChecklist, TripAdvancedChecklist,
                     TripAdditionalInfo)


class TripForm(forms.ModelForm):
    type = forms.MultipleChoiceField(
        label=_("Rodzaj podróży"),
        required=False,
        choices=TripChoices.choices,
        widget=forms.CheckboxSelectMultiple()
        )

    class Meta:
        model = Trip
        fields = [
            "name",
            "type",
            "destination",
            "start_date",
            "end_date",
            "transport",
            "estimated_cost",
            "participants_number",
            "participants",
            "reservations",
            "notes",
            "access_granted",
        ]
        widgets = {
            "participants_number": forms.NumberInput(),
            "participants": forms.Textarea(attrs={"class": "textarea_field"}),
            "reservations": forms.Textarea(attrs={"class": "textarea_field"}),
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def __init__(self, *args, **kwargs):
        self.trip_names = kwargs.pop("trip_names")
        self.trip_names = list(name.lower() for name in self.trip_names)
        super(TripForm, self).__init__(*args, **kwargs)

    def clean_type(self):
        return ",".join(self.cleaned_data["type"])

    # def clean_type(self):
    #     print("*********** FORM", self.cleaned_data['type'])
    #     print("*********** FORM", list(self.cleaned_data['type']))
    #     print("*********** FORM", type(list(self.cleaned_data['type'])))
    #     print("*********** FORM", type(self.cleaned_data['type']))
    #     return self.cleaned_data['type']

    def clean_name(self):
        clean_name = self.cleaned_data.get("name", None)
        if not clean_name:
            self.add_error("name", {"required": _("To pole jest wymagane.")})
        elif clean_name.lower() in self.trip_names:
            self.add_error(
                "name",
                _("Istnieje już podróż o podanej nazwie w bazie danych. "
                  "Podaj inną nazwę.")
            )
        else:
            return clean_name

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date", None)
        if start_date and not isinstance(start_date, datetime.date):
            self.add_error(
                "start_date",
                {"invalid":
                     _("Poprawny format to rok-miesiąc-dzień (np. 2020-3-22).")
                 }
            )
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date", None)
        if end_date and not isinstance(end_date, datetime.date):
            self.add_error(
                "end_date",
                {"invalid":
                     _("Poprawny format to rok-miesiąc-dzień (np. 2020-3-22).")
                 }
            )
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date", None)
        end_date = cleaned_data.get("end_date", None)
        if start_date and end_date and start_date > end_date:
            self.add_error(
                "end_date",
                _("Data zakończenia podróży nie może przypadać wcześniej "
                  "niż data jej rozpoczęcia.")
            )
        return cleaned_data

###############################################################################


class TripReportForm(forms.ModelForm):
    class Meta:
        model = TripReport
        fields = [
            # "trip",
            "start_date",
            "end_date",
            "description",
            "notes",
            "facebook",
            "youtube",
            "instagram",
            "pinterest",
            "link",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"class": "textarea_field"}),
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date", None)
        if start_date and not isinstance(start_date, datetime.date):
            self.add_error(
                "start_date",
                {"invalid":
                     _("Poprawny format to rok-miesiąc-dzień (np. 2020-3-22).")
                 }
            )
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date", None)
        if end_date and not isinstance(end_date, datetime.date):
            self.add_error(
                "end_date",
                {"invalid":
                     _("Poprawny format to rok-miesiąc-dzień (np. 2020-3-22).")
                 }
            )
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date", None)
        end_date = cleaned_data.get("end_date", None)
        if start_date and end_date and start_date > end_date:
            self.add_error(
                "end_date",
                _("Data zakończenia relacji nie może przypadać wcześniej "
                  "niż data jej rozpoczęcia."),
            )
        return cleaned_data

###############################################################################


class TripBasicChecklistForm(forms.ModelForm):
    wallet = forms.MultipleChoiceField(
        label=_("Portfel"),
        required=False,
        choices=BasicChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )
    keys = forms.MultipleChoiceField(
        label=_("Klucze"),
        required=False,
        choices=KeysChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )
    cosmetics = forms.MultipleChoiceField(
        label=_("Kosmetyki"),
        required=False,
        choices=CosmeticsChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )
    electronics = forms.MultipleChoiceField(
        label=_("Elektronika"),
        required=False,
        choices=ElectronicsChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )
    useful_stuff = forms.MultipleChoiceField(
        label=_("Użyteczne rzeczy"),
        required=False,
        choices=UsefulStaffChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )

    class Meta:
        model = TripBasicChecklist
        fields = [
            # "trip",
            "name",
            "wallet",
            "keys",
            "cosmetics",
            "electronics",
            "useful_stuff",
            "basic_drugs",
            "additional_drugs",
        ]

    def __init__(self, *args, **kwargs):
        self.trip_names = kwargs.pop("trip_names")
        self.trip_names = list(name.lower() for name in self.trip_names)
        super(TripBasicChecklistForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in [
                "basic_drugs",
                "additional_drugs",
            ]:
                field.widget.attrs.update(
                    {"class": "textarea_field"}
                )

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name or name is None:
            self.add_error("name", _("To pole jest wymagane."))
        elif name.lower() in self.trip_names:
            self.add_error(
                "name",
                _("Istnieje już wyposażenie o podanej nazwie w bazie danych. "
                  "Podaj inną nazwę.")
            )
        return name

    def clean_wallet(self):
        return ",".join(self.cleaned_data["wallet"])

    def clean_keys(self):
        return ",".join(self.cleaned_data["keys"])

    def clean_cosmetics(self):
        return ",".join(self.cleaned_data["cosmetics"])

    def clean_electronics(self):
        return ",".join(self.cleaned_data["electronics"])

    def clean_useful_stuff(self):
        return ",".join(self.cleaned_data["useful_stuff"])

###############################################################################


class TripAdvancedChecklistForm(forms.ModelForm):
    trekking = forms.MultipleChoiceField(
        label=_("Trekking"),
        required=False,
        choices=TrekkingChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )
    hiking = forms.MultipleChoiceField(
        label=_("Wspinaczka"),
        required=False,
        choices=HikingChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )
    cycling = forms.MultipleChoiceField(
        label=_("Rower"),
        required=False,
        choices=CyclingChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )
    camping = forms.MultipleChoiceField(
        label=_("Camping"),
        required=False,
        choices=CampingChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )
    fishing = forms.MultipleChoiceField(
        label=_("Wędkarstwo"),
        required=False,
        choices=FishingChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )
    sunbathing = forms.MultipleChoiceField(
        label=_("Plażowanie"),
        required=False,
        choices=SunbathingChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )
    business = forms.MultipleChoiceField(
        label=_("Wyjazd służbowy"),
        required=False,
        choices=BusinessChecklist.choices,
        widget=forms.CheckboxSelectMultiple()
        )

    class Meta:
        model = TripAdvancedChecklist
        fields = [
            # "trip",
            "name",
            "trekking",
            "hiking",
            "cycling",
            "camping",
            "fishing",
            "sunbathing",
            "business",
        ]

    def __init__(self, *args, **kwargs):
        self.trip_names = kwargs.pop("trip_names")
        self.trip_names = list(name.lower() for name in self.trip_names)
        super(TripAdvancedChecklistForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name or name is None:
            self.add_error("name", _("To pole jest wymagane."))
        elif name.lower() in self.trip_names:
            self.add_error(
                "name",
                _("Istnieje już wyposażenie o podanej nazwie w bazie danych. "
                  "Podaj inną nazwę.")
            )
        return name

    def clean_trekking(self):
        return ",".join(self.cleaned_data["trekking"])

    def clean_hiking(self):
        return ",".join(self.cleaned_data["hiking"])

    def clean_cycling(self):
        return ",".join(self.cleaned_data["cycling"])

    def clean_business(self):
        return ",".join(self.cleaned_data["business"])

    def clean_camping(self):
        return ",".join(self.cleaned_data["camping"])

    def clean_fishing(self):
        return ",".join(self.cleaned_data["fishing"])

    def clean_sunbathing(self):
        return ",".join(self.cleaned_data["sunbathing"])

###############################################################################


class TripPersonalChecklistForm(forms.ModelForm):
    class Meta:
        model = TripPersonalChecklist
        fields = [
            # "trip",
            "name",
            "checklist",
        ]
        widgets = {
            "checklist": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def __init__(self, *args, **kwargs):
        self.trip_names = kwargs.pop("trip_names")
        self.trip_names = list(name.lower() for name in self.trip_names)
        super(TripPersonalChecklistForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name:
            self.add_error("name", _("Pole 'Nazwa' nie może być puste."))
        elif name.lower() in self.trip_names:
            self.add_error(
                "name",
                _("Istnieje już lista o podanej nazwie w bazie danych. "
                  "Podaj inną nazwę.")
            )
        return name

###############################################################################


class TripAdditionalInfoForm(forms.ModelForm):
    class Meta:
        model = TripAdditionalInfo
        fields = [
            # "trip",
            "name",
            "info",
            "notes",
        ]
        widgets = {
            "info": forms.Textarea(attrs={"class": "textarea_field"}),
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def __init__(self, *args, **kwargs):
        self.trip_names = kwargs.pop("trip_names")
        self.trip_names = list(name.lower() for name in self.trip_names)
        super(TripAdditionalInfoForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name:
            self.add_error("name", _("Pole 'Nazwa' nie może być puste."))
        elif name.lower() in self.trip_names:
            self.add_error(
                "name",
                _("Istnieje już element o podanej nazwie w bazie danych. "
                  "Podaj inną nazwę.")
            )
        return name

###############################################################################


class TripCostForm(forms.ModelForm):
    class Meta:
        model = TripCost
        fields = [
            # "trip",
            "name",
            "cost_group",
            "cost_paid",
            "currency",
            "exchange_rate",
            "notes",
        ]
        widgets = {
            "cost_group": forms.Select(),
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
        }
        error_messages = {
            "exchange_rate":
                {"invalid_value": _("Wartość kursu walutowego nie może być ujemna.")}
        }

    def clean_exchange_rate(self):
        exchange_rate = self.cleaned_data["exchange_rate"]
        if exchange_rate < 0:
            self.add_error("exchange_rate", _("Wartość kursu walutowego nie może być ujemna."))
        return exchange_rate

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name:
            self.add_error("name", _("Pole 'Nazwa' nie może być puste."))
        return name
