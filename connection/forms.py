import datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Attachment, Counterparty
from payment.models import Payment
from credit.models import Credit
from renovation.models import Renovation
from trip.models import Trip
from medical.models import HealthTestResult, MedicalVisit


class CounterpartyForm(forms.ModelForm):
    payments = forms.ModelMultipleChoiceField(
        Payment.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz płatności"),
        required=False,
        help_text=_("Jeśli kontrahent dotyczy płatności, której nie ma na liście, "
                    "dodaj wpierw płatność."),
    )
    credits = forms.ModelMultipleChoiceField(
        Credit.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz kredyty"),
        blank=True,
        required=False,
        help_text=_("Jeśli kontrahent dotyczy kredytu, którego nie ma na liście, "
                    "dodaj wpierw kredyt."),
    )
    renovations = forms.ModelMultipleChoiceField(
        Renovation.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz remonty"),
        blank=True,
        required=False,
        help_text=_("Jeśli kontrahent dotyczy remontu, którego nie ma na liście, "
                    "dodaj wpierw remont."),
    )
    trips = forms.ModelMultipleChoiceField(
        Trip.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz podróże"),
        blank=True,
        required=False,
        help_text=_("Jeśli kontrahent dotyczy podróży, której nie ma na liście, "
                    "dodaj wpierw podróż."),
    )

    class Meta:
        model = Counterparty
        fields = [
            "payments",
            "credits",
            "renovations",
            "trips",
            "name",
            "phone_number",
            "email",
            "address",
            "www",
            "bank_account",
            "payment_app",
            "client_number",
            "primary_contact_name",
            "primary_contact_phone_number",
            "primary_contact_email",
            "notes",
            "access_granted",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def __init__(self, *args, **kwargs):
        self.cp_names = kwargs.pop("cp_names")
        self.cp_names = list(element.lower() for element in self.cp_names)
        super(CounterpartyForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        cp_name = self.cleaned_data["name"]
        if not cp_name:
            self.add_error("name", _("Pole 'Nazwa' nie może być puste."))
        elif cp_name.lower() in self.cp_names:
            self.add_error(
                "name",
                _("Istnieje już kontrahent o podanej nazwie w bazie danych.")
            )
        return cp_name

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504

###############################################################################


class AttachmentForm(forms.ModelForm):
    counterparties = forms.ModelMultipleChoiceField(
        Counterparty.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz kontrahenta"),
        blank=True,
        required=False,
        help_text=_("Jeśli załącznik dotyczy kontrahenta, "
                    "którego nie ma na liście, dodaj wpierw kontrahenta."),
    )
    payments = forms.ModelMultipleChoiceField(
        Payment.objects.all(),
        blank=True,
        # widget=forms.CheckboxSelectMultiple(attrs={"class":"multiple_select_field"}),
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz płatność"),
        required=False,
        help_text=_("Jeśli załącznik dotyczy płatności, której nie ma na liście, "
                    "dodaj wpierw płatność."),
    )
    renovations = forms.ModelMultipleChoiceField(
        Renovation.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz remont"),
        blank=True,
        required=False,
        help_text=_("Jeśli załącznik dotyczy remontu, którego nie ma na liście, "
                    "dodaj wpierw remont."),
    )
    credits = forms.ModelMultipleChoiceField(
        Credit.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz kredyt"),
        blank=True,
        required=False,
        help_text=_("Jeśli załącznik dotyczy kredytu, którego nie ma na liście, "
                    "dodaj wpierw kredyt."),
    )
    trips = forms.ModelMultipleChoiceField(
        Trip.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz podróż"),
        blank=True,
        required=False,
        help_text=_("Jeśli załącznik dotyczy wyjazdu, którego nie ma na liście, "
                    "dodaj wpierw wyjazd."),
    )
    health_results = forms.ModelMultipleChoiceField(
        HealthTestResult.objects.all(),
        blank=True,
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz badania"),
        required=False,
        help_text=_("Jeśli załącznik dotyczy badania, którego nie ma na liście, "
                    "dodaj wpierw badanie."),
    )
    medical_visits = forms.ModelMultipleChoiceField(
        MedicalVisit.objects.all(),
        blank=True,
        widget=forms.SelectMultiple(attrs={"class": "multiple_select_field"}),
        label=_("Wybierz wizytę"),
        required=False,
        help_text=_("Jeśli załącznik dotyczy wizyty, której nie ma na liście, "
                    "dodaj wpierw wizytę."),
    )

    class Meta:
        model = Attachment
        fields = [
            "payments",
            "counterparties",
            "renovations",
            "credits",
            "trips",
            "health_results",
            "medical_visits",
            "attachment_name",
            "attachment_path",
            "file_date",
            "file_info",
            "access_granted",
        ]
        widgets = {
            "file_info": forms.Textarea(attrs={"class": "textarea_field"})
        }

    def __init__(self, *args, **kwargs):
        self.attachment_names = kwargs.pop("attachment_names")
        self.attachment_names = list(element.lower() for element in self.attachment_names)
        super(AttachmentForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in [
                "attachment_path",
            ]:
                field.widget.attrs.update(
                    {"class": "attach_field"}
                )

    def clean_attachment_name(self):
        attachment_name = self.cleaned_data["attachment_name"]
        if not attachment_name:
            self.add_error(
                "attachment_name", _("Wprowadź nazwę dla dokumentu."))
        elif attachment_name.lower() in self.attachment_names:
            self.add_error(
                "attachment_name",
                _("Istnieje już załącznik o podanej nazwie w bazie danych.")
            )
        return attachment_name

    def clean_attachment_path(self):
        attachment_path = self.cleaned_data["attachment_path"]
        allowed_extensions = ["pdf", "png", "jpg"]
        if not any(str(attachment_path).endswith(extension) for extension in allowed_extensions):
            self.add_error(
                "attachment_path",
                _("Niedopuszczalny format pliku (plik: %s). Dozwolone pliki wyłącznie w formacie: %s."
                  % (str(attachment_path), allowed_extensions))
            )
        return attachment_path

    def clean_file_date(self):
        file_date = self.cleaned_data.get("file_date", None)
        if file_date and not isinstance(file_date, datetime.date):
            self.add_error(
                "file_date",
                {"invalid":
                     _("Poprawny format to rok-miesiąc-dzień (np. 2020-3-22).")
                 }
            )
        return file_date

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504
