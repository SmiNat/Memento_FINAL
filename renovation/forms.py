import datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Renovation, RenovationCost


class RenovationForm(forms.ModelForm):
    class Meta:
        model = Renovation
        fields = [
            "name",
            "description",
            "estimated_cost",
            "start_date",
            "end_date",
            "access_granted",
        ]
        widgets = {
            "start_date": forms.SelectDateWidget(
                years=range(
                    datetime.date.today().year-2, datetime.date.today().year+4
                )
            ),
            "end_date": forms.SelectDateWidget(
                years=range(
                    datetime.date.today().year-2, datetime.date.today().year+4
                )
            ),
            "description": forms.Textarea(attrs={"class": "textarea_field"}),
            "access_granted": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        self.renovation_names = kwargs.pop("renovation_names")
        self.renovation_names = list(name.lower() for name in self.renovation_names)
        super(RenovationForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        clean_name = self.cleaned_data.get("name", None)
        if not clean_name:
            self.add_error("required",
                           "To pole jest wymagane.")
        elif clean_name.lower() in self.renovation_names:
            self.add_error(
                "name",
                _("Istnieje już remont o podanej nazwie w bazie danych. "
                  "Podaj inną nazwę.")
            )
        else:
            return clean_name

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date", None)
        if start_date and not isinstance(start_date, datetime.date):
            self.add_error(
                "start_date",
                {"invalid": _("Poprawny format to rok-miesiąc-dzień "
                              "(np. 2020-3-22).")
                 }
            )
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date", None)
        if end_date and not isinstance(end_date, datetime.date):
            self.add_error(
                "end_date",
                {"invalid": _("Poprawny format to rok-miesiąc-dzień "
                              "(np. 2020-3-22).")
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
                _("Data zakończenia remontu nie może przypadać wcześniej "
                  "niż data jego rozpoczęcia."),
            )
        return cleaned_data

###############################################################################


class RenovationCostForm(forms.ModelForm):
    class Meta:
        model = RenovationCost
        fields = [
            "name",
            "unit_price",
            "units",
            "description",
            "order",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"class": "textarea_field"}),
            "order": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def clean_unit_price(self):
        unit_price = self.cleaned_data["unit_price"]
        if unit_price < 0:
            self.add_error("unit_price",
                           _("Wartość pola nie może być liczbą ujemną."))
        return unit_price

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name:
            self.add_error("name", _("Pole 'Nazwa' nie może być puste."))
        return name
