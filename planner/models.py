from __future__ import annotations
import uuid

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from access.enums import Access
from .enums import RequirementStatus, ValidityStatus, ExecutionStatus


class ExpenseList(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             verbose_name=_("Użytkownik"))
    name = models.CharField(_("Nazwa"), max_length=255,
                            help_text=_("Pole wymagane."))
    access_granted = models.CharField(
        _("Dostęp do danych"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać listę wraz z wydatkami.")
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def get_all_estimated_costs(self) -> float | None:
        """
        Return sum of all estimated costs for ExpenseItem queryset
        calculated on given ExpenseList instance.
        """
        queryset = ExpenseItem.objects.filter(expense_list=self.id)
        if not queryset:
            return None
        total_costs = 0
        for item in queryset:
            if item.estimated_cost:
                total_costs += item.estimated_cost
        return round(total_costs, 2)

    def get_all_paid_costs(self) -> float | None:
        """
        Return sum of all paid costs for ExpenseItem queryset
        calculated on given ExpenseList instance.
        """
        queryset = ExpenseItem.objects.filter(expense_list=self.id)
        if not queryset:
            return None
        total_costs = 0
        for item in queryset:
            if item.cost_paid:
                total_costs += item.cost_paid
        return round(total_costs, 2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_expense_list_title"
                )
            ]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class ExpenseItem(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    expense_list = models.ForeignKey(
        ExpenseList, on_delete=models.CASCADE, verbose_name=_("Tytuł listy")
    )
    name = models.CharField(
        _("Nazwa"), max_length=255,
        help_text=_("Pole wymagane.")
    )
    description = models.TextField(
        _("Opis"), max_length=500,
        null=True, blank=True,
    )
    estimated_cost = models.DecimalField(
        _("Szacunkowy koszt"), max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
    )
    execution_status = models.CharField(
        _("Status wykonania"), max_length=100,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PLANNED,
        null=True, blank=True
    )
    requirement_status = models.CharField(
        _("Status wymagania"), max_length=100,
        choices=RequirementStatus.choices,
        default=RequirementStatus.OPTIONAL,
        null=True, blank=True
    )
    validity_status = models.CharField(
        _("Status ważności"), max_length=100,
        choices=ValidityStatus.choices,
        default=ValidityStatus.NOT_URGENT,
        null=True, blank=True
    )
    cost_paid = models.DecimalField(
        _("Poniesiony koszt"), max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(
            0, message=_("Wartość nie może być liczbą ujemną."))],
    )
    purchase_date = models.DateField(
        _("Data poniesienia wydatku"), null=True, blank=True)
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################
# TO DO LIST
###############################################################################


class ToDoList(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    name = models.CharField(
        _("Nazwa"), max_length=255,
        help_text=_("Pole wymagane.")
    )
    access_granted = models.CharField(
        _("Dostęp do danych"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może przeglądać "
                    "listę wraz z zadaniami.")
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_todo_list_title"
                )
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

###############################################################################


class ToDoItem(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik")
    )
    todo_list = models.ForeignKey(
        ToDoList, on_delete=models.CASCADE, verbose_name=_("Tytuł listy")
    )
    name = models.CharField(
        _("Nazwa"), max_length=255,
        help_text=_("Pole wymagane.")
    )
    description = models.TextField(
        _("Opis"), max_length=500,
        null=True, blank=True,
    )
    execution_status = models.CharField(
        _("Status wykonania"), max_length=100,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PLANNED,
        null=True, blank=True,
    )
    requirement_status = models.CharField(
        _("Status wymagania"), max_length=100,
        choices=RequirementStatus.choices,
        default=RequirementStatus.OPTIONAL,
        null=True, blank=True,
    )
    validity_status = models.CharField(
        _("Status ważności"), max_length=100,
        choices=ValidityStatus.choices,
        default=ValidityStatus.NOT_URGENT,
        null=True, blank=True,
    )
    due_date = models.DateField(_("Termin wykonania"), null=True, blank=True)
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    def __str__(self):
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    class Meta:
        ordering = ["due_date"]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
