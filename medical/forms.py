import datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from .enums import MedicationDays
from .models import MedCard, Medicine, MedicalVisit, HealthTestResult, med_hours


class MedCardForm(forms.ModelForm):
    class Meta:
        model = MedCard
        fields = [
            # "name", # currently, user can only have one medcard
            "age",
            "weight",
            "height",
            "blood_type",
            "allergies",
            "diseases",
            "permanent_medications",
            "additional_medications",
            "main_doctor",
            "other_doctors",
            "emergency_contact",
            "notes",
            "access_granted",
            "access_granted_medicines",
            "access_granted_test_results",
            "access_granted_visits",
        ]

    def __init__(self, *args, **kwargs):
        super(MedCardForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in [
                "allergies",
                "diseases",
                "permanent_medications",
                "additional_medications",
                "other_doctors",
                "emergency_contact",
                "notes",
            ]:
                field.widget.attrs.update(
                    {"class": "textarea_field"}
                )

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504

###############################################################################


class MedicineForm(forms.ModelForm):
    medication_days = forms.MultipleChoiceField(
        label=_("Dni przyjmowania leków"),
        required=False,
        choices=MedicationDays.choices,
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Uzupełnij, jeśli leki przyjmowane są w konkretne dni tygodnia.")
        )
    medication_hours = forms.MultipleChoiceField(
        label=_("Godziny przyjmowania leków"),
        required=False,
        choices=med_hours(),
        widget=forms.CheckboxSelectMultiple(),
        )

    class Meta:
        model = Medicine
        fields = [
            "drug_name_and_dose",
            "daily_quantity",
            "disease",
            "medication_frequency",
            "medication_days",
            "exact_frequency",
            "medication_hours",
            "start_date",
            "end_date",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def __init__(self, *args, **kwargs):
        self.drug_names = kwargs.pop("drug_names")
        self.drug_names = list(name.lower() for name in self.drug_names)
        super(MedicineForm, self).__init__(*args, **kwargs)

    def clean_medication_days(self):
        medication_days = self.cleaned_data.get("medication_days", None)
        if medication_days:
            return ",".join(medication_days)
        # return ",".join(self.cleaned_data["medication_days"])

    def clean_medication_hours(self):
        medication_hours = self.cleaned_data.get("medication_hours", None)
        if medication_hours:
            return ",".join(medication_hours)

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

    def clean_drug_name_and_dose(self):
        drug = self.cleaned_data["drug_name_and_dose"]
        if not drug:
            self.add_error(
                "drug_name_and_dose",
                _("Pole 'Nazwa leku' nie może być puste.")
            )
        elif drug.lower() in self.drug_names:
            self.add_error(
                "drug_name_and_dose",
                _("Istnieje już lek o podanej nazwie w bazie danych. "
                  "Podaj inną nazwę.")
            )
        return drug

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date", None)
        end_date = cleaned_data.get("end_date", None)
        if start_date and end_date and start_date > end_date:
            self.add_error(
                "end_date",
                _("Data zakończenia przyjmowania leku nie może przypadać "
                  "wcześniej niż data rozpoczęcia przyjmowania leku.")
            )
        return cleaned_data

###############################################################################


class MedicalVisitForm(forms.ModelForm):
    class Meta:
        model = MedicalVisit
        fields = [
            "specialization",
            "doctor",
            "visit_date",
            "visit_time",
            "visit_location",
            "notes",
        ]
        widgets = {
            "visit_time": forms.TimeInput(attrs={'type': 'time'}),
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop("queryset")
        super(MedicalVisitForm, self).__init__(*args, **kwargs)

    def clean_visit_date(self):
        visit_date = self.cleaned_data.get("visit_date", None)
        if visit_date and not isinstance(visit_date, datetime.date):
            self.add_error(
                "visit_date",
                {"invalid": _("Poprawny format to rok-miesiąc-dzień "
                              "(np. 2020-3-22).")
                 }
            )
        return visit_date

    def clean(self):
        cleaned_data = super().clean()
        specialization = cleaned_data.get("specialization", None)
        visit_date = cleaned_data.get("visit_date", None)
        visit_time = cleaned_data.get("visit_time", None)
        if specialization and visit_date and visit_time:
            unique_together = (
                cleaned_data["specialization"].lower(),
                cleaned_data["visit_date"],
                cleaned_data["visit_time"]
            )
            queryset = []
            for element in self.queryset:
                queryset.append(
                    (element["specialization"].lower(),
                     element["visit_date"],
                     element["visit_time"])
                )
            if not cleaned_data["specialization"]:
                self.add_error(
                    "specialization",
                    _("Pole 'Specjalizacja' nie może być puste.")
                )
            elif unique_together in queryset:
                self.add_error(
                    "specialization",
                    _("Istnieje już wizyta u tego specjalisty w danym dniu "
                      "i o wskazanej godzinie.")
                )
            return cleaned_data

###############################################################################


class HealthTestResultForm(forms.ModelForm):
    class Meta:
        model = HealthTestResult
        fields = [
            "name",
            "test_result",
            "test_date",
            "disease",
            "notes",
        ]
        widgets = {
            "test_result": forms.Textarea(attrs={"class": "textarea_field"}),
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
        }

    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop("queryset")
        super(HealthTestResultForm, self).__init__(*args, **kwargs)

    def clean_test_date(self):
        test_date = self.cleaned_data.get("test_date", None)
        if test_date and not isinstance(test_date, datetime.date):
            self.add_error(
                "test_date",
                {"invalid": _("Poprawny format to rok-miesiąc-dzień "
                              "(np. 2020-3-22).")
                 }
            )
        return test_date

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name", None)
        test_date = cleaned_data.get("test_date", None)
        if name and test_date:
            unique_together = (cleaned_data["name"].lower(), cleaned_data["test_date"])
            queryset = []
            for element in self.queryset:
                queryset.append((element["name"].lower(), element["test_date"]))

            if unique_together in queryset:
                self.add_error(
                    "name",
                    _("Istnieje już test o tej nazwie wykonany w danym dniu.")
                )
        return cleaned_data
