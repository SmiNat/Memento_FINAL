import datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Payment
from .enums import PaymentMonth

class PaymentForm(forms.ModelForm):
    payment_months = forms.MultipleChoiceField(
        label=_("Miesiące płatności"),
        required=False,
        choices=PaymentMonth.choices,
        widget=forms.CheckboxSelectMultiple()
        )

    class Meta:
        model = Payment
        fields = [
            "name",
            "payment_type",
            "payment_method",
            "payment_status",
            "payment_frequency",
            "payment_months",
            "payment_day",
            "payment_value",
            "notes",
            "start_of_agreement",
            "end_of_agreement",
            "access_granted",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def __init__(self, *args, **kwargs):
        self.payment_names = kwargs.pop("payment_names")
        self.payment_names = list(element.lower() for element in self.payment_names)
        super(PaymentForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in [
                "payment_type",
                "payment_method",
                "payment_status",
                "payment_frequency",
                "payment_day",
            ]:
                field.widget.attrs.update(
                    {"class": "input_field"}
                )

    def clean_payment_months(self):
        return ','.join(self.cleaned_data['payment_months'])

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name:
            self.add_error("name", _("Pole 'Nazwa' nie może być puste."))
        elif name.lower() in self.payment_names:
            self.add_error(
                "name", _("Istnieje już płatność o podanej nazwie w bazie danych. "
                          "Podaj inną nazwę.")
            )
        return name

    def clean_start_of_agreement(self):
        start_date = self.cleaned_data.get("start_of_agreement", None)
        if start_date and not isinstance(start_date, datetime.date):
            self.add_error(
                "start_of_agreement",
                "Poprawny format to rok-miesiąc-dzień (np. 2020-3-22)."
            )
        return start_date

    def clean_end_of_agreement(self):
        end_date = self.cleaned_data.get("end_of_agreement", None)
        if end_date and not isinstance(end_date, datetime.date):
            self.add_error(
                "end_of_agreement",
                "Poprawny format to rok-miesiąc-dzień (np. 2020-3-22)."
            )
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_of_agreement", None)
        end_date = cleaned_data.get("end_of_agreement", None)
        if start_date and end_date and start_date > end_date:
            self.add_error(
                "end_of_agreement",
                _("Data wygaśnięcia umowy nie może przypadać wcześniej "
                  "niż data jej zawarcia."),)
        return cleaned_data
