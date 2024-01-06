from datetime import date
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ExpenseList, ExpenseItem, ToDoList, ToDoItem


class ExpenseListForm(forms.ModelForm):
    class Meta:
        model = ExpenseList
        fields = [
            "name",
            "access_granted",
        ]

    def __init__(self, *args, **kwargs):
        self.list_names = kwargs.pop("list_names")
        super(ExpenseListForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name:
            self.add_error("name", _("Pole 'Nazwa' nie może być puste."))
        elif name in self.list_names:
            self.add_error(
                "name",
                _("Istnieje już lista o podanej nazwie w bazie danych. "
                  "Podaj inną nazwę.")
            )
        return name

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504


class ExpenseItemForm(forms.ModelForm):
    class Meta:
        model = ExpenseItem
        fields = [
            "name",
            "description",
            "estimated_cost",
            "execution_status",
            "requirement_status",
            "validity_status",
            "cost_paid",
            "purchase_date",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"class": "textarea_field"}),
            "purchase_date": forms.SelectDateWidget(
                years=range(date.today().year-2, date.today().year+3)),
        }

    def __init__(self, *args, **kwargs):
        super(ExpenseItemForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in [
                "execution_status",
                "requirement_status",
                "validity_status",
            ]:
                field.widget.attrs.update(
                    {"class": "select_field"}
                )

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name:
            self.add_error("name", _("Pole 'Nazwa' nie może być puste."))
        return name

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504


class ToDoListForm(forms.ModelForm):
    class Meta:
        model = ToDoList
        fields = [
            "name",
            "access_granted",
        ]

    def __init__(self, *args, **kwargs):
        self.list_names = kwargs.pop("list_names")
        super(ToDoListForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name:
            self.add_error("name", _("Pole 'Nazwa' nie może być puste."))
        elif name in self.list_names:
            self.add_error(
                "name",
                _("Istnieje już lista o podanej nazwie w bazie danych. Podaj inną nazwę.")
            )
        return name

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504

class ToDoItemForm(forms.ModelForm):
    class Meta:
        model = ToDoItem
        fields = [
            "name",
            "description",
            "due_date",
            "execution_status",
            "requirement_status",
            "validity_status",
            "link",
            "notes"
        ]
        widgets = {
            "description": forms.Textarea(attrs={"class": "textarea_field"}),
            "notes": forms.Textarea(attrs={"class": "textarea_field"}),
            "due_date": forms.SelectDateWidget(
                years=range(date.today().year-2, date.today().year+3)),
        }

    def __init__(self, *args, **kwargs):
        super(ToDoItemForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in [
                "execution_status",
                "requirement_status",
                "validity_status",
            ]:
                field.widget.attrs.update(
                    {"class": "select_field"}
                )

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504
