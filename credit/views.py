import calendar
import datetime
import decimal
import logging
import os
import shutil

from pyxirr import xirr
from dateutil.relativedelta import relativedelta

import pandas as pd
import numpy as np

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, render, get_object_or_404


from .forms import (CreditForm, CreditInsuranceForm,
                    CreditCollateralForm, CreditTrancheForm,
                    CreditInterestRateForm, CreditAdditionalCostForm,
                    CreditEarlyRepaymentForm)
from .models import (Credit, CreditInsurance, CreditCollateral,
                     CreditTranche, CreditInterestRate,
                     CreditAdditionalCost, CreditEarlyRepayment)
from connection.models import Attachment, Counterparty

desired_width = 320
pd.set_option('display.width', desired_width)
np.set_printoptions(linewidth=desired_width)
pd.set_option('display.max_columns', 15)

logger = logging.getLogger("all")


def credits(request):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")

    order = request.GET.get("sort_data")
    if not order:
        order = "-updated"

    credits = Credit.objects.filter(user=request.user).order_by(order)
    counterparties = request.user.counterparty_set.all()
    attachments = request.user.attachment_set.all()

    context = {
        "credits": credits,
        "counterparties": counterparties,
        "attachments": attachments,
    }
    return render(request, "credit/credits.html", context)


@login_required(login_url="login")
def single_credit(request, pk):
    profile = request.user.profile
    credit = Credit.objects.get(id=pk)
    if credit:
        if credit.user != request.user:
            logger.critical(
                "user: %s - enter page: single-credit - 🛑 SAFETY BREACH - "
                "attempt to view credit (id: %s) of another user (id: %s)!"
                % (request.user.id, credit.id, credit.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")

    try:
        credit_interest_rate = CreditInterestRate.objects.filter(
            credit=credit).order_by("interest_rate_start_date")
    except CreditInterestRate.DoesNotExist:
        credit_interest_rate = None
    try:
        credit_insurance = CreditInsurance.objects.filter(credit=pk).order_by(
            "start_date")
    except CreditInsurance.DoesNotExist:
        credit_insurance = None
    try:
        credit_tranche = CreditTranche.objects.filter(credit=credit).order_by(
            "tranche_date")
        queryset = CreditTranche.objects.filter(credit=credit)
        credit_tranches_total = CreditTranche.total_tranche(queryset)
        credit_tranches_ratio = round(
            ((credit_tranches_total / credit.credit_amount) * 100), 2)
    except CreditTranche.DoesNotExist:
        credit_tranche = None
        credit_tranches_total = None
        credit_tranches_ratio = None
    try:
        credit_early_repayment = CreditEarlyRepayment.objects.filter(
            credit=credit).order_by("repayment_date")
        queryset = CreditEarlyRepayment.objects.filter(credit=credit)
        credit_total_repayment = CreditEarlyRepayment.total_repayment(queryset)
        credit_repayment_ratio = round(((CreditEarlyRepayment.total_repayment(
            queryset) / credit.credit_amount) * 100), 2)
    except CreditEarlyRepayment.DoesNotExist:
        credit_early_repayment = None
        credit_total_repayment = None
        credit_repayment_ratio = None
    try:
        credit_collateral = CreditCollateral.objects.filter(
            credit=credit).order_by("collateral_set_date")
    except CreditCollateral.DoesNotExist:
        credit_collateral = None
    try:
        credit_additional_cost = CreditAdditionalCost.objects.filter(
            credit=credit).order_by("cost_payment_date")
    except CreditAdditionalCost.DoesNotExist:
        credit_additional_cost = None

    attachments = Attachment.objects.filter(credits=credit.id)

    context = {
        "profile": profile,
        "credit": credit,
        "credit_interest_rate": credit_interest_rate,
        "credit_insurance": credit_insurance,
        "credit_tranche": credit_tranche,
        "credit_tranches_total": credit_tranches_total,
        "credit_tranches_ratio": credit_tranches_ratio,
        "credit_early_repayment": credit_early_repayment,
        "credit_total_repayment": credit_total_repayment,
        "credit_repayment_ratio": credit_repayment_ratio,
        "credit_collateral": credit_collateral,
        "credit_additional_cost": credit_additional_cost,
        "attachments": attachments,
    }
    return render(request, "credit/single_credit.html", context)


@login_required(login_url="login")
def add_credit(request):
    page = "add-credit"
    credit_names = list(Credit.objects.filter(user=request.user).values_list(
        "name", flat=True))
    form = CreditForm(credit_names=credit_names)
    if request.method == "POST":
        form = CreditForm(request.POST, credit_names=credit_names)
        if form.is_valid():
            try:
                credit = form.save(commit=False)
                credit.user = request.user
                credit.save()
                messages.success(request, _("Dodano kredyt."))
                return redirect("credit:credits")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-credit - "
                    "⚠️ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-credit - "
                "⚠️unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {
        "page": page,
        "form": form,
        "credit_names": credit_names,
    }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def edit_credit(request, pk):
    page = "edit-credit"
    credit = Credit.objects.get(id=pk)
    if credit:
        if credit.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-credit - 🛑 SAFETY BREACH - "
                "attempt to edit credit (id: %s) of another user (id: %s)!"
                % (request.user.id, credit.id, credit.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    credit_names = list(Credit.objects.filter(user=request.user).exclude(
        id=credit.id).values_list("name", flat=True))
    form = CreditForm(instance=credit, credit_names=credit_names)
    if request.method == "POST":
        form = CreditForm(request.POST, instance=credit, credit_names=credit_names)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zaktualizowano kredyt."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-credit (id: %s)- "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, credit.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-credit (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, credit.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-credit (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "credit": credit,
        "credit_names": credit_names,
    }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def delete_credit(request, pk):
    page = "delete-credit"
    credit = Credit.objects.get(id=pk)
    credit_directory = str(request.user.id) + "_credit"
    credit_path = os.path.join(settings.MEDIA_ROOT, credit_directory)  # server folder to remove directory
    if credit:
        if credit.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-credit - 🛑 SAFETY BREACH - "
                "attempt to delete credit (id: %s) of another user (id: %s)!"
                % (request.user.id, credit.id, credit.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        try:
            credit_interest_rate = CreditInterestRate.objects.filter(
                credit=credit)
        except CreditInterestRate.DoesNotExist:
            pass
        else:
            credit_interest_rate = CreditInterestRate.objects.filter(
                credit=credit)
            credit_interest_rate.delete()

        try:
            credit_insurance = CreditInsurance.objects.get(credit=credit)
        except CreditInsurance.DoesNotExist:
            pass
        else:
            credit_insurance = CreditInsurance.objects.get(credit=credit)
            credit_insurance.delete()

        try:
            credit_tranche = CreditTranche.objects.get(credit=credit)
        except CreditTranche.DoesNotExist:
            pass
        else:
            credit_tranche = CreditTranche.objects.get(credit=credit)
            credit_tranche.delete()

        try:
            credit_early_repayment = CreditEarlyRepayment.objects.filter(
                credit=credit)
        except CreditEarlyRepayment.DoesNotExist:
            pass
        else:
            credit_early_repayment = CreditEarlyRepayment.objects.filter(
                credit=credit)
            credit_early_repayment.delete()

        try:
            credit_collateral = CreditCollateral.objects.filter(credit=credit)
        except CreditCollateral.DoesNotExist:
            pass
        else:
            credit_collateral = CreditCollateral.objects.filter(credit=credit)
            credit_collateral.delete()

        try:
            credit_additional_cost = CreditAdditionalCost.objects.filter(
                credit=credit)
        except CreditAdditionalCost.DoesNotExist:
            pass
        else:
            credit_additional_cost = CreditAdditionalCost.objects.filter(
                credit=credit)
            credit_additional_cost.delete()

        if os.path.exists(credit_path):
            if os.path.isfile(credit_path) or os.path.islink(credit_path):
                os.unlink(credit_path)
                shutil.rmtree(credit_path)
            else:
                shutil.rmtree(credit_path)

        credit.delete()

        messages.success(request,
                         _("Usunięto kredyt wraz z informacjami dodatkowymi."))
        return redirect("credit:credits")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-credit (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "credit": credit}
    return render(request, "credit/credit_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_credit_tranche(request, pk):
    page = "add-credit-tranche"
    credit = Credit.objects.get(id=pk)
    queryset = CreditTranche.objects.filter(credit=credit.id)
    sum_of_tranches = CreditTranche.total_tranche(queryset)
    dates_of_tranches = list(queryset.exclude(id=credit.id).values_list(
        "tranche_date", flat=True))
    form = CreditTrancheForm(
        credit=credit,
        queryset=queryset,
        sum_of_tranches=sum_of_tranches,
        dates_of_tranches=dates_of_tranches,
    )
    if request.method == "POST":
        form = CreditTrancheForm(
            request.POST,
            credit=credit,
            queryset=queryset,
            sum_of_tranches=sum_of_tranches,
            dates_of_tranches=dates_of_tranches,
        )
        if form.is_valid():
            try:
                tranche_form = form.save(commit=False)
                tranche_form.user = request.user
                tranche_form.credit = credit
                tranche_form.save()
                messages.success(request,
                                 _("Dodano informacje związane z transzą."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-credit-tranche - "
                    "⚠️ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-credit-tranche - "
                "⚠️unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {
        "page": page,
        "form": form,
        "credit": credit,
        "queryset": queryset,
        "sum_of_tranches": sum_of_tranches,
        "dates_of_tranches": dates_of_tranches,
        }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def edit_credit_tranche(request, pk):
    page = "edit-credit-tranche"
    credit_tranche = CreditTranche.objects.get(id=pk)
    credit = credit_tranche.credit
    queryset = CreditTranche.objects.filter(credit=credit.id)
    sum_of_tranches = (CreditTranche.total_tranche(queryset)
                       - credit_tranche.tranche_amount)
    dates_of_tranches = list(queryset.exclude(id=pk).values_list(
        "tranche_date", flat=True))
    if credit_tranche:
        if credit_tranche.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-credit-tranche - 🛑 SAFETY BREACH - "
                "attempt to edit credit tranche (id: %s) of another user (id: %s)!"
                % (request.user.id, credit_tranche.id, credit_tranche.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    form = CreditTrancheForm(
        instance=credit_tranche,
        credit=credit,
        queryset=queryset,
        sum_of_tranches=sum_of_tranches,
        dates_of_tranches=dates_of_tranches,
        )
    if request.method == "POST":
        form = CreditTrancheForm(
            request.POST,
            instance=credit_tranche,
            credit=credit,
            queryset=queryset,
            sum_of_tranches=sum_of_tranches,
            dates_of_tranches=dates_of_tranches,
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request,
                                 _("Dodano informacje związane z transzą."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-credit-tranche (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, credit_tranche.id, e))
                messages.error(request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-credit-tranche (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, credit_tranche.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-credit-tranche (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_tranche.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "credit": credit,
        "credit_tranche": credit_tranche,
        "queryset": queryset,
        "sum_of_tranches": sum_of_tranches,
        "dates_of_tranches": dates_of_tranches,
        }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def delete_credit_tranche(request, pk):
    page = "delete-credit-tranche"
    credit_tranche = CreditTranche.objects.get(id=pk)
    credit = credit_tranche.credit
    if credit_tranche:
        if credit_tranche.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-credit-tranche - 🛑 SAFETY BREACH - "
                "attempt to delete credit tranche (id: %s) of another user (id: %s)!"
                % (request.user.id, credit_tranche.id, credit_tranche.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        credit_tranche.delete()
        messages.success(request, _("Usunięto transzę."))
        return redirect("credit:single-credit", pk=str(credit.id))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-credit-tranche (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_tranche.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "credit_tranche": credit_tranche, "credit": credit}
    return render(request, "credit/credit_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_credit_interest_rate(request, pk):
    page = "add-credit-interest-rate"
    credit = Credit.objects.get(id=pk)
    installment_type = credit.installment_type
    start_of_payment = credit.start_of_payment
    payment_day = credit.payment_day
    form = CreditInterestRateForm(
        credit_id=credit.id,
        installment_type=installment_type,
        start_of_payment=start_of_payment,
        payment_day=payment_day,
    )
    if request.method == "POST":
        form = CreditInterestRateForm(
            request.POST,
            credit_id=credit.id,
            installment_type=installment_type,
            start_of_payment=start_of_payment,
            payment_day=payment_day,
        )
        if form.is_valid():
            try:
                interest_rate_form = form.save(commit=False)
                interest_rate_form.user = request.user
                interest_rate_form.credit = credit
                interest_rate_form.save()
                messages.success(
                    request,
                    _("Dodano informacje związane z oprocentowaniem zmiennym.")
                )
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-credit-interest-rate - "
                    "⚠️ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-credit-interest-rate - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {
        "page": page,
        "form": form,
        "credit": credit,
        "installment_type": installment_type,
        "start_of_payment": start_of_payment,
        "payment_day": payment_day,
    }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def edit_credit_interest_rate(request, pk):
    page = "edit-credit-interest-rate"
    credit_interest_rate = CreditInterestRate.objects.get(id=pk)
    credit = credit_interest_rate.credit
    installment_type = credit.installment_type
    start_of_payment = credit.start_of_payment
    payment_day = credit.payment_day
    if credit_interest_rate:
        if credit_interest_rate.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-credit-interest-rate - "
                "🛑 SAFETY BREACH - attempt to edit interest rate (id: %s) "
                "of another user (id: %s)!" % (request.user.id,
                                               credit_interest_rate.id,
                                               credit_interest_rate.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    form = CreditInterestRateForm(
        instance=credit_interest_rate,
        credit_id=credit.id,
        installment_type=installment_type,
        start_of_payment=start_of_payment,
        payment_day=payment_day,
    )
    if request.method == "POST":
        form = CreditInterestRateForm(
            request.POST,
            instance=credit_interest_rate,
            credit_id=credit.id,
            installment_type=installment_type,
            start_of_payment=start_of_payment,
            payment_day=payment_day,
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(
                    request,
                    _("Zaktualizowano informacje związane z oprocentowaniem zmiennym.")
                )
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-credit-interest-rate (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, credit_interest_rate.id, e))
                messages.error(request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-credit-interest-rate (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, credit_interest_rate.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-credit-interest-rate (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_interest_rate.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "credit": credit,
        "credit_interest_rate": credit_interest_rate,
        "installment_type": installment_type,
        "start_of_payment": start_of_payment,
        "payment_day": payment_day,
    }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def delete_credit_interest_rate(request, pk):
    page = "delete-credit-interest-rate"
    interest_rate = CreditInterestRate.objects.get(id=pk)
    credit = interest_rate.credit
    if interest_rate:
        if interest_rate.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-credit-interest-rate - "
                "🛑 SAFETY BREACH - attempt to delete interest rate (id: %s) "
                "of another user (id: %s)!"
                % (request.user.id, interest_rate.id, interest_rate.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        interest_rate.delete()
        messages.success(request, _("Usunięto oprocentowanie."))
        return redirect("credit:single-credit", pk=str(credit.id))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-credit-interest-rate (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, interest_rate.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "interest_rate": interest_rate, "credit": credit}
    return render(request, "credit/credit_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_credit_insurance(request, pk):
    page = "add-credit-insurance"
    credit = Credit.objects.get(id=pk)
    start_of_credit = Credit.objects.get(id=credit.id).start_of_credit
    form = CreditInsuranceForm(start_of_credit=start_of_credit)
    if request.method == "POST":
        form = CreditInsuranceForm(request.POST, start_of_credit=start_of_credit)
        if form.is_valid():
            try:
                insurance_form = form.save(commit=False)
                insurance_form.user = request.user
                insurance_form.credit = credit
                insurance_form.save()
                messages.success(request,
                                 _("Dodano informacje związane z ubezpieczeniem."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-credit-insurance - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-credit-insurance - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "
                                      "Sprawdź poprawność danych."))
    context = {
        "page": page,
        "form": form,
        "credit": credit,
        "start_of_credit": start_of_credit,
    }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def edit_credit_insurance(request, pk):
    page = "edit-credit-insurance"
    credit_insurance = CreditInsurance.objects.get(id=pk)
    credit = credit_insurance.credit
    start_of_credit = credit.start_of_credit
    if credit_insurance:
        if credit_insurance.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-credit-insurance - 🛑 SAFETY BREACH - "
                "attempt to edit credit insurance (id: %s) of another user (id: %s)!"
                % (request.user.id, credit_insurance.id, credit_insurance.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    form = CreditInsuranceForm(instance=credit_insurance,
                               start_of_credit=start_of_credit)
    if request.method == "POST":
        form = CreditInsuranceForm(
            request.POST,
            instance=credit_insurance,
            start_of_credit=start_of_credit,
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request,
                                 _("Zaktualizowano informacje związane z ubezpieczeniem."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-credit-insurance (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, credit_insurance.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-credit-insurance (id: %s) - "
                "⚠️ invalid request method (required: POST)"
                % (request.user.id, credit_insurance.id))
            messages.error(request,
                           _("Wystąpił błąd podczas zapisu formularza. "
                             "Sprawdź poprawność danych."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-credit-insurance (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_insurance.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "credit": credit,
        "credit_insurance": credit_insurance,
        "start_of_credit": start_of_credit,
    }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def delete_credit_insurance(request, pk):
    page = "delete-credit-insurance"
    credit_insurance = CreditInsurance.objects.get(id=pk)
    credit = credit_insurance.credit
    if credit_insurance:
        if credit_insurance.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-credit-insurance - "
                "🛑 SAFETY BREACH - attempt to delete credit insurance (id: %s) "
                "of another user (id: %s)!" % (request.user.id,
                                               credit_insurance.id,
                                               credit_insurance.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        credit_insurance.delete()
        messages.success(request, _("Usunięto ubezpieczenie."))
        return redirect("credit:single-credit", pk=str(credit.id))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-credit-insurance (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_insurance.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {
        "page": page,
        "credit": credit,
        "credit_insurance": credit_insurance,
    }
    return render(request, "credit/credit_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_credit_collateral(request, pk):
    page = "add-credit-collateral"
    credit = Credit.objects.get(id=pk)
    form = CreditCollateralForm(credit=credit)
    if request.method == "POST":
        form = CreditCollateralForm(request.POST, credit=credit)
        if form.is_valid():
            try:
                collateral_form = form.save(commit=False)
                collateral_form.user = request.user
                collateral_form.credit = credit
                collateral_form.save()
                messages.success(request,
                                 _("Dodano informacje związane z zabezpieczeniem."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-credit-collateral - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-credit-collateral - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "
                                      "Sprawdź poprawność danych."))
    context = {
        "page": page,
        "form": form,
        "credit": credit,
    }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def edit_credit_collateral(request, pk):
    page = "edit-credit-collateral"
    credit_collateral = CreditCollateral.objects.get(id=pk)
    credit = credit_collateral.credit
    form = CreditCollateralForm(instance=credit_collateral, credit=credit)
    if credit_collateral:
        if credit_collateral.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-credit-collateral - "
                "🛑 SAFETY BREACH - attempt to edit credit collateral (id: %s) "
                "of another user (id: %s)!" % (request.user.id,
                                               credit_collateral.id,
                                               credit_collateral.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = CreditCollateralForm(
            request.POST,
            instance=credit_collateral,
            credit=credit
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request,
                                 _("Zaktualizowano informacje związane z zabezpieczeniem."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-credit-collateral (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, credit_collateral.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-credit-collateral (id: %s) - "
                "⚠️unsuccessful POST with error: %s"
                % (request.user.id, credit_collateral.id, form.errors))
            messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "
                                      "Sprawdź poprawność danych."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-credit-collateral (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_collateral.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "credit": credit,
        "credit_collateral": credit_collateral,
    }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def delete_credit_collateral(request, pk):
    page = "delete-credit-collateral"
    credit_collateral = CreditCollateral.objects.get(id=pk)
    credit = credit_collateral.credit
    if credit_collateral:
        if credit_collateral.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-credit-collateral - 🛑 SAFETY BREACH - "
                "attempt to delete credit collateral (id: %s) of another user (id: %s)!"
                % (request.user.id, credit_collateral.id, credit_collateral.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        credit_collateral.delete()
        messages.success(request, _("Usunięto zabezpieczenie."))
        return redirect("credit:single-credit", pk=str(credit.id))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-credit-collateral (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_collateral.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {
        "page": page,
        "credit": credit,
        "credit_collateral": credit_collateral,
    }
    return render(request, "credit/credit_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_credit_additional_cost(request, pk):
    page = "add-credit-additional-cost"
    credit = Credit.objects.get(id=pk)
    form = CreditAdditionalCostForm(credit=credit)
    if request.method == "POST":
        form = CreditAdditionalCostForm(request.POST, credit=credit)
        if form.is_valid():
            try:
                cost_form = form.save(commit=False)
                cost_form.user = request.user
                cost_form.credit = credit
                cost_form.save()
                messages.success(request, _("Dodano dodatkowe koszty kredytu."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-additional-cost - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-additional-cost - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "
                                      "Sprawdź poprawność danych."))
    context = {
        "page": page,
        "form": form,
        "credit": credit,
    }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def edit_credit_additional_cost(request, pk):
    page = "edit-credit-additional-cost"
    credit_additional_cost = CreditAdditionalCost.objects.get(id=pk)
    credit = credit_additional_cost.credit
    if credit_additional_cost:
        if credit_additional_cost.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-credit-additional-cost - "
                "🛑 SAFETY BREACH - attempt to edit additional cost (id: %s) "
                "of another user (id: %s)!" % (request.user.id,
                                               credit_additional_cost.id,
                                               credit_additional_cost.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    form = CreditAdditionalCostForm(
        instance=credit_additional_cost, credit=credit)
    if request.method == "POST":
        form = CreditAdditionalCostForm(
            request.POST,
            instance=credit_additional_cost,
            credit=credit
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zaktualizowano dodatkowe koszty kredytu."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-credit-additional-cost (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, credit_additional_cost.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-credit-additional-cost (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, credit_additional_cost.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-credit-additional-cost (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_additional_cost.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "credit": credit,
        "credit_additional_cost": credit_additional_cost,
        }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def delete_credit_additional_cost(request, pk):
    page = "delete-credit-additional-cost"
    credit_additional_cost = CreditAdditionalCost.objects.get(id=pk)
    credit = credit_additional_cost.credit
    if credit_additional_cost:
        if credit_additional_cost.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-credit-additional-cost - "
                "🛑 SAFETY BREACH - attempt to delete additional cost (id: %s) "
                "of another user (id: %s)!" % (request.user.id,
                                               credit_additional_cost.id,
                                               credit_additional_cost.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        credit_additional_cost.delete()
        messages.success(request, _("Usunięto koszt."))
        return redirect("credit:single-credit", pk=str(credit.id))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-credit-additional-cost (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_additional_cost.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {
        "page": page,
        "credit": credit,
        "credit_additional_cost": credit_additional_cost,
    }
    return render(request, "credit/credit_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_credit_early_repayment(request, pk):
    page = "add-credit-early-repayment"
    credit = Credit.objects.get(id=pk)
    form = CreditEarlyRepaymentForm(credit=credit)
    if request.method == "POST":
        form = CreditEarlyRepaymentForm(request.POST, credit=credit)
        if form.is_valid():
            # if "kwota nadpłaty > kwota pozostała do spłaty - OKODOWAĆ":
            #     messages.error(request, _("Wysokość nadpłaty nie może przekraczać kwoty pozostałej do spłaty"))
            try:
                repayment_form = form.save(commit=False)
                repayment_form.user = request.user
                repayment_form.credit = credit
                repayment_form.save()
                messages.success(request, _("Dodano nadpłatę kredytu."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-early-repayment - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-early-repayment - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "
                                      "Sprawdź poprawność danych."))
    context = {"page": page, "form": form, "credit": credit}
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def edit_credit_early_repayment(request, pk):
    page = "edit-credit-early-repayment"
    credit_early_repayment = CreditEarlyRepayment.objects.get(id=pk)
    credit = credit_early_repayment.credit
    if credit_early_repayment:
        if credit_early_repayment.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-credit-early-repayment - "
                "🛑 SAFETY BREACH - attempt to edit early repayment (id: %s) "
                "of another user (id: %s)!" % (request.user.id,
                                               credit_early_repayment.id,
                                               credit_early_repayment.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    form = CreditEarlyRepaymentForm(
        instance=credit_early_repayment, credit=credit)
    if request.method == "POST":
        form = CreditEarlyRepaymentForm(
            request.POST,
            instance=credit_early_repayment,
            credit=credit,
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zaktualizowano dodatkowe koszty kredytu."))
                return redirect("credit:single-credit", pk=credit.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-credit-early-repayment (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, credit_early_repayment.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-credit-early-repayment (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, credit_early_repayment.id, form.errors))
            messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "
                                      "Sprawdź poprawność danych."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-credit-early-repayment (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_early_repayment.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "credit": credit,
        "credit_early_repayment": credit_early_repayment,
        }
    return render(request, "credit/credit_form.html", context)


@login_required(login_url="login")
def delete_credit_early_repayment(request, pk):
    page = "delete-credit-early-repayment"
    credit_early_repayment = CreditEarlyRepayment.objects.get(id=pk)
    credit = credit_early_repayment.credit
    if credit_early_repayment:
        if credit_early_repayment.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-credit-early-repayment - "
                "🛑 SAFETY BREACH - attempt to delete early repayment (id: %s) "
                "of another user (id: %s)!" % (request.user.id,
                                               credit_early_repayment.id,
                                               credit_early_repayment.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        credit_early_repayment.delete()
        messages.success(request, _("Usunięto nadpłatę."))
        return redirect("credit:single-credit", pk=str(credit.id))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-credit-early-repayment (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, credit_early_repayment.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {
        "page": page,
        "credit": credit,
        "credit_early_repayment": credit_early_repayment,
    }
    return render(request, "credit/credit_delete_form.html", context)


###############################################################################
# CREDIT ENGINE
###############################################################################


@login_required(login_url="login")
def credit_repayment_schedule(request, pk):
    profile = request.user.profile
    credit = Credit.objects.get(id=pk)

    if credit.user != request.user:
        logger.critical(
            "user: %s - enter page: credit-repayment-schedule - "
            "🛑 SAFETY BREACH - attempt to access credit repayment schedule of "
            "another user (id: %s)!" % (request.user.id, credit.user.id))
        messages.error(
            request, _("Nie masz uprawnień do tych danych."))
        logout(request)
        return redirect("login")

    credit_schedule = CreditSchedule(request, pk)
    credit_tranches = CreditTranche.objects.filter(credit=credit)
    sum_of_tranches = CreditTranche.total_tranche(credit_tranches)

    context = {
        "credit": credit,
        "credit_schedule": credit_schedule,
        "profile": profile,
        "tranches": sum_of_tranches,
    }
    if credit.tranches_in_credit == _("Tak"):
        if not CreditTranche.objects.filter(credit=credit):
            messages.error(request, _("Uzupełnij wpierw transze kredytu. "
                                      "Wymagana wpłata inicjalna."))
            return redirect("credit:single-credit", pk=str(credit.id))
        elif sum_of_tranches < credit.credit_amount:
            messages.error(request,
                           _(f"Suma transz ({sum_of_tranches}) nie jest równa "
                             f"wartości kredytu ({credit.credit_amount}). "
                             f"Uzupełnij warunki kredytu by uzyskać prawidłowy "
                             f"harmonogram."))
    return render(request, "credit/credit_repayment_schedule.html", context)


@login_required(login_url="login")
def access_to_credit_schedule(request, slug):
    # Function used to get access to credit schedule from user with granted access
    # (without passing the id of that credit in url address to user with access)
    page = "access_granted"
    credit = get_object_or_404(Credit, slug=slug)

    if (credit.user.profile.access_granted_to != request.user.email or
            credit.access_granted_for_schedule == _("Brak dostępu")):
        logger.critical(
            "user: %s - enter page: access-to-credit-schedule - 🛑 SAFETY BREACH - "
            "attempt to access credit schedule of another user (id: %s)!"
            % (request.user.id, credit.user.id))
        messages.error(
            request, _("Nie masz uprawnień do tych danych."))
        logout(request)
        return redirect("login")

    credit_tranches = CreditTranche.objects.filter(credit=credit)
    sum_of_tranches = CreditTranche.total_tranche(credit_tranches)

    if credit.tranches_in_credit == _("Tak"):
        if not CreditTranche.objects.filter(credit=credit):
            messages.error(request, _("Harmonogram niedostępny - nieprawidłowe "
                                      "dane dotyczące kredytu. Wymagana wpłata "
                                      "inicjalna."))
            # return HttpResponseRedirect(request.META.get("HTTP_REFERER", "access:access"))
            return redirect("access:data-access-payments", credit.user.profile.slug, 1)
        elif sum_of_tranches < credit.credit_amount:
            messages.error(request,
                           _(f"Suma transz ({round(sum_of_tranches, 2)}) nie "
                             f"jest równa wartości kredytu "
                             f"({round(credit.credit_amount, 2)}). "
                             f"Wymagane uzupełnienie kredytu celem wygenerowania "
                             f"prawidłowego harmonogramu."))
    pk = credit.id
    credit_schedule = CreditSchedule(request, pk)

    context = {
        "page": page,
        "credit": credit,
        "credit_schedule": credit_schedule,
        "tranches": sum_of_tranches,
    }

    return render(request, "credit/credit_repayment_schedule.html", context)


class CreditSchedule():
    def __init__(self, request, pk):
        try:
            self.credit = Credit.objects.get(id=pk)
            self.provision = (self.credit.provision
                              if isinstance(self.credit.provision,
                                            (int, float, decimal.Decimal))
                                 and self.credit.provision > 0
                              else 0)
            self.market_value = (self.credit.market_value
                                 if isinstance(self.credit.market_value,
                                               (int, float, decimal.Decimal))
                                    and self.credit.market_value > 0
                                 else 0)
            self.collateral_rate = (self.credit.collateral_rate
                                    if isinstance(self.credit.collateral_rate,
                                                  (int, float, decimal.Decimal))
                                       and self.credit.collateral_rate > 0
                                    else 0)
            self.grace_period = (self.credit.grace_period
                                 if isinstance(self.credit.grace_period, int)
                                    and self.credit.grace_period > 0
                                 else 0)
        except Credit.DoesNotExist:
            messages.error(request, _("Brak kredytu w bazie danych."))

    def credit_table(self):
        df = pd.DataFrame(columns=["Liczba dni", "Data", "Zaciągnięcie kredytu",
                                   "Wcześniejsza spłata", "Oprocentowanie pomostowe (%)",
                                   "Oprocentowanie kredytu (%)",
                                   "Rata odsetkowa", "Rata kapitałowa", "Rata całkowita",
                                   "Saldo", "LTV (%)", "Ubezpieczenie (niekredytowane)",
                                   "Prowizje i inne", "Razem płatność"])

        # df[_("Data")] = sorted((set(self.installment_dates()).union(set(self.payments_from_bank().keys()))))

        df["Data"] = pd.to_datetime(self.dates_set())
        df["Liczba dni"] = (df["Data"] - pd.Series(df["Data"]).shift(1)).dt.days
        df["Zaciągnięcie kredytu"] = df["Data"].map(self.payments_from_bank_schedule()).fillna(0)
        # df["Wcześniejsza spłata"] = df["Data"].map(self.early_repayments_schedule()).fillna(0)
        df["Wcześniejsza spłata"] = df["Data"].map(self.early_repayment_modified_schedule()).fillna(0)
        df["Data"] = [time.date() for time in df["Data"]]
        if self.collateral_rate:
            df["Oprocentowanie pomostowe (%)"] = (np.where(df["Data"]
                                                           < self.collateral_set_date(),
                                                           self.collateral_rate,
                                                           df["Oprocentowanie pomostowe (%)"])
                                                  )
            df["Oprocentowanie pomostowe (%)"] = (np.where(df["Data"]
                                                           >= self.collateral_set_date(),
                                                           0,
                                                           df["Oprocentowanie pomostowe (%)"])
                                                  )
        df["Oprocentowanie kredytu (%)"] = df["Data"].map(self.interest_rates_schedule())
        df["Rata odsetkowa"] = df["Data"].map(self.interest_installment_schedule())
        df["Rata kapitałowa"] = df["Data"].map(self.capital_installments_schedule())
        if self.credit.installment_type == _("Raty równe"):
            df["Rata całkowita"] = df["Rata odsetkowa"] + df["Rata kapitałowa"]
        else:
            df["Rata całkowita"] = df["Data"].map(self.total_installments_schedule())
        df["Saldo"] = df["Data"].map(self.credit_balance_schedule())
        df["LTV (%)"] = ("n/a" if self.market_value == 0
                         else (df["Saldo"].astype("float")/float(self.market_value)).round(2))
        df["Ubezpieczenie (niekredytowane)"] = df["Data"].map(self.insurance_payments_schedule()).fillna(0)
        df["Prowizje i inne"] = df["Data"].map(self.additional_payments_schedule()).fillna(0)
        df["Razem płatność"] = ((df["Wcześniejsza spłata"].astype(float)
                                 + df["Rata całkowita"].astype(float)
                                 + df["Ubezpieczenie (niekredytowane)"].astype(float)
                                 + df["Prowizje i inne"].astype(float)))

        # Setting data types
        df["Data"] = pd.to_datetime(self.dates_set()).date
        # df["Liczba dni"] = df["Liczba dni"].dt.days
        df["Liczba dni"] = df["Liczba dni"].fillna(0).astype("int")
        df["Zaciągnięcie kredytu"] = df["Zaciągnięcie kredytu"].astype("float")
        df["Wcześniejsza spłata"] = df["Wcześniejsza spłata"].astype("float")
        df["Oprocentowanie pomostowe (%)"] = (df["Oprocentowanie pomostowe (%)"].astype("float")
                                              if not df["Oprocentowanie pomostowe (%)"].isnull().values.any()
                                              else df["Oprocentowanie pomostowe (%)"].fillna("n/a"))
        df["Oprocentowanie kredytu (%)"] = df["Oprocentowanie kredytu (%)"].astype("float").fillna("---")
        df["Rata odsetkowa"] = df["Rata odsetkowa"].astype("float").fillna(0)
        df["Rata kapitałowa"] = df["Rata kapitałowa"].astype("float").fillna(0)
        df["Rata całkowita"] = df["Rata całkowita"].astype("float").fillna(0)
        df["Saldo"] = df["Saldo"].astype("float")
        if self.market_value:
            df["LTV (%)"] = df["LTV (%)"].astype("float")
        df["Ubezpieczenie (niekredytowane)"] = df["Ubezpieczenie (niekredytowane)"].astype("float")
        df["Prowizje i inne"] = df["Prowizje i inne"].astype("float")
        df["Razem płatność"] = df["Razem płatność"].astype("float")

        # Removing unnecessary rows from table
        # df = df.replace(0, np.nan)
        # df = df.dropna(subset=["Saldo", "Rata całkowita", "Razem płatność"], how="all")
        # df = df.replace(np.nan, 0)

        return df

    def to_html(self):
        df = self.credit_table()
        df = df.style.format(precision=2, thousands=".", decimal=",")
        df.set_table_styles({
            ("Zaciągnięcie kredytu"): [
                {"selector": "th", "props": "border-left: 1px solid white"},
                {"selector": "td", "props": "border-left: 1px solid white"},
            ],
            ("Oprocentowanie pomostowe (%)"): [
                {"selector": "th", "props": "border-left: 1px solid white"},
                {"selector": "td", "props": "border-left: 1px solid white"},
            ],
            ("Rata odsetkowa"): [
                {"selector": "th", "props": "border-left: 1px solid white"},
                {"selector": "td", "props": "border-left: 1px solid white"},
            ],
            ("Rata całkowita"): [
                {"selector": "th", "props": "border-left: 1px dashed white"},
                {"selector": "td", "props": "border-left: 1px dashed white"},
            ],
            ("Razem płatność"): [
                {"selector": "th", "props": "border-left: 1px solid white"},
                {"selector": "td", "props": "border-left: 1px solid white"},
            ],
            ("Saldo"): [
                {"selector": "th", "props": "border-left: 1px solid white"},
                {"selector": "td", "props": "border-left: 1px solid white"},
            ],
            ("Ubezpieczenie (niekredytowane)"): [
                {"selector": "th", "props": "border-left: 1px solid white"},
                {"selector": "td", "props": "border-left: 1px solid white"},
            ],
            ("Razem płatność"): [
                {"selector": "th", "props": "border-left: 2px solid white"},
                {"selector": "td", "props": "border-left: 2px solid white"},
            ],
        })
        df.set_table_styles([
            {"selector": "th.col_heading",
             "props": "font-size: 85%; "
                      "max-width: 100%; "
                      "line-height: 15px; "
                      "inline-size: 100px; "
                      "white-space: normal; overflow-wrap: break-word; "
                      "padding: 10px 0px;"
             },
        ], overwrite=False)

        return df.to_html()

    def to_excel(self):
        """Save dataframe as excel file on user's local path."""
        user = self.credit.user
        filename = str(self.credit).replace(" ", "_") + ".xlsx"
        file_path = f"{user.id}_credit/{filename}"
        directory = os.path.join(settings.MEDIA_ROOT, f"{user.id}_credit")
        if os.path.exists(directory):
            shutil.rmtree(directory)  # to clean old files
            os.mkdir(directory)
        else:
            os.mkdir(directory)
        path = os.path.join(settings.MEDIA_ROOT, file_path)

        self.credit_table().to_excel(path)
        return path

    # def attachment_file_path(self):
    #     """A method to download a file from it's upload path by using static"""
    #     name = self.attachment_path.name
    #     file_path = os.path.join(settings.MEDIA_URL, name)
    #     file_path = os.path.join(settings.MEDIA_URL, name)
    #     return file_path

    def sum_for_table_columns(self):
        df = self.credit_table()
        total_column_value = dict()
        # total_column_value["Łączna liczba dni spłaty"] = df["Liczba dni"].astype("float").sum()
        total_column_value["Otrzymana kwota kredytu"] = round(df["Zaciągnięcie kredytu"].sum(), 2)
        total_column_value["Wartość wcześniejszej spłaty"] = round(df["Wcześniejsza spłata"].sum(), 2)
        total_column_value["Łączna rata odsetkowa"] = round(df["Rata odsetkowa"].sum(), 2)
        total_column_value["Łączna rata kapitałowa"] = round(df["Rata kapitałowa"].sum(), 2)
        total_column_value["Rata całkowita"] = round(df["Rata całkowita"].sum(), 2)
        total_column_value["Ubezpieczenie (niekredytowane)"] = round(df["Ubezpieczenie (niekredytowane)"].sum(), 2)
        total_column_value["Prowizje i inne (niekredytowane)"] = round(df["Prowizje i inne"].sum(), 2)
        total_column_value["Razem płatność"] = round(df["Razem płatność"].sum(), 2)
        total_column_value["Razem poniesione koszty"] = (round(total_column_value["Razem płatność"]
                                                               - total_column_value["Otrzymana kwota kredytu"],
                                                               2))

        total_column_value["XIRR (%)"] = round(self.xirr() * 100, 2) if self.xirr() else "n/a"

        return total_column_value

    def xirr(self):
        df = self.credit_table()
        if not df["Razem płatność"].isnull().values.any():
            amounts = df["Zaciągnięcie kredytu"] - df["Razem płatność"]
            dates = df["Data"]
            irr = xirr(zip(dates, amounts))
        else:
            irr = None
        return irr

    def frequency(self, variable):
        frequency = (
            12 if variable == _("Roczne") else
            6 if variable == _("Półroczne") else
            3 if variable == _("Kwartalne") else
            1 if variable == _("Miesięczne") else
            0
        )
        return frequency

    def dates_set(self):
        list_of_dates = set(self.basic_installment_dates_list()).union(set(self.payments_from_bank_schedule().keys()))
        list_of_dates = (list_of_dates.union(set((self.insurance_payments_schedule().keys())))
                         if self.insurance_payments_schedule() else list_of_dates)
        list_of_dates = (list_of_dates.union(set((self.early_repayments_schedule().keys())))
                         if self.early_repayments_schedule() else list_of_dates)
        list_of_dates = (list_of_dates.union(set((self.additional_payments_schedule().keys())))
                         if self.additional_payments_schedule() else list_of_dates)
        return sorted(list_of_dates)

    def basic_installment_dates_list(self):
        """Returns list of dates of installment payments from the date of first
        installment to the date of last payment according to schedule from credit agreement."""
        installment_dates = []
        start = self.credit.start_of_payment
        installment_dates.append(start)
        frequency = self.frequency(self.credit.installment_frequency)
        if frequency:
            i = 1
            for period in range(1, self.credit.credit_period+1, frequency):
                # +1 period to fully cover installment schedule in case of assumption with start of payment at the same date as start of credit
                # (which is illogical and first payment of credit is usually set after payment of first tranche from bank)
                if self.credit.payment_day == 0:
                    installment_date = ((datetime.date(start.year, start.month, 1)
                                         + relativedelta(months=frequency*i))
                                        - datetime.timedelta(days=1))
                    installment_dates.append(installment_date)
                else:
                    installment_dates.append((start
                                              + relativedelta(months=frequency*i))
                                             + relativedelta(day=self.credit.payment_day))
                i += 1
        else:
            installment_dates.append((start
                                      + relativedelta(months=frequency))
                                     + relativedelta(day=self.credit.payment_day))
        return sorted(installment_dates)

    def payments_from_bank_schedule(self):
        """Returns dictionary of dates and amounts of all credit tranches."""
        payments_from_bank = {}
        initial_payments = 0

        if self.credit.credited_provision == _("Tak"):
            initial_payments = self.provision
        if self.credit.life_insurance_first_year:
            initial_payments += self.credit.life_insurance_first_year
        if self.credit.property_insurance_first_year:
            initial_payments += self.credit.property_insurance_first_year
        payments_from_bank[self.credit.start_of_credit] = initial_payments

        # If credit is paid in tranches
        try:
            tranches = CreditTranche.objects.filter(credit=self.credit)
            tranche_dates = [tranche.tranche_date for tranche in tranches]
            tranche_amounts = [tranche.tranche_amount for tranche in tranches]
        except CreditTranche.DoesNotExist:
            tranches = None
            tranche_dates = self.credit.start_of_credit
            tranche_amounts = [self.credit.credit_amount]

        for date, amount in zip(tranche_dates, tranche_amounts):
            if date in payments_from_bank.keys():
                payments_from_bank[date] += amount
            else:
                payments_from_bank[date] = amount

        # If credit is paid at once
        if not tranches:
            initial_payments += self.credit.credit_amount
            payments_from_bank[self.credit.start_of_credit] = initial_payments

        # Verification of amount received from bank (tranches can be added and updated during credit lifetime)
        # if sum(payments_from_bank.values()) != self.credit.total_loan_value():
        #     logger.info("🛑 Sum of tranches not match credited value, sum: %s, value: %s", sum(payments_from_bank.values()), self.credit.total_loan_value())
        #     raise ValueError(_("Suma transz nie jest równa wartości kredytu."), sum(payments_from_bank.values()), self.credit.total_loan_value())

        return payments_from_bank

    def early_repayments_schedule(self):
        """
        Returns dictionary of dates and amounts of all repayments
        (according to dates and amounts given by the user).
        Modifications of early repayment amounts according to actual credit balance
        provided in early_repayment_modified_schedule method.
        """
        early_repayments = {}
        try:
            repayments = CreditEarlyRepayment.objects.filter(credit=self.credit)
        except CreditEarlyRepayment.DoesNotExist:
            repayments = None
        if not repayments:
            return early_repayments

        repayments = CreditEarlyRepayment.objects.filter(credit=self.credit)
        repayment_dates = [record.repayment_date for record in repayments]
        repayment_amounts = [record.repayment_amount for record in repayments]
        for date, amount in zip(repayment_dates, repayment_amounts):
            early_repayments[date] = amount
        return early_repayments

    def collateral_set_date(self):
        """Returns date until additional rate is required due to pending collateral set."""
        # No collateral required
        collateral_set = self.credit.collateral_required
        if collateral_set == _("Nie"):
            return None

        # Collateral required
        try:
            collateral = CreditCollateral.objects.get(credit=self.credit)
        except CreditCollateral.DoesNotExist:
            collateral = None

        # No date of collateral set
        if not collateral:
            return self.basic_installment_dates_list()[-1]

        # With collateral set date
        return collateral.collateral_set_date

    def interest_rates_schedule(self):  # <<<<<<<<
        """Returns dictionary of dates and interest rates at installment payments."""
        interest_rates = {}

        # Interest rate specified in credit agreement
        initial_interest_rate = 0
        if self.credit.fixed_interest_rate:
            initial_interest_rate += self.credit.fixed_interest_rate
        else:
            initial_interest_rate += (self.credit.floating_interest_rate + self.credit.bank_margin)
        if self.credit.collateral_required == _("Tak"):
            initial_interest_rate += self.collateral_rate
        interest_rates[self.credit.start_of_credit] = initial_interest_rate

        try:
            rates = CreditInterestRate.objects.filter(credit=self.credit)
        except CreditInterestRate.DoesNotExist:
            rates = None

        # Without changes of interest rates during credit lifetime
        if not rates:
            try:
                collateral = CreditCollateral.objects.get(credit=self.credit)
            except CreditCollateral.DoesNotExist:
                for period in self.basic_installment_dates_list():
                    interest_rates[period] = initial_interest_rate
                return interest_rates
            else:
                # UWAGA!!!! Dodać, że jeśli zabezpieczenie jest ustanowione przed rozpoczęciem spłaty kredytu, to nie ma go w odsetkach
                collateral = CreditCollateral.objects.get(credit=self.credit)
                interest_rate_without_collateral_rate = initial_interest_rate - self.collateral_rate
                interest_rates[collateral.collateral_set_date] = interest_rate_without_collateral_rate
                for period in self.basic_installment_dates_list():
                    if period < collateral.collateral_set_date:
                        interest_rates[period] = initial_interest_rate
                    else:
                        interest_rates[period] = interest_rate_without_collateral_rate
                return interest_rates

        # With different interest rates during credit lifetime
        all_rates = CreditInterestRate.objects.filter(credit=self.credit)
        dates = [record.interest_rate_start_date for record in all_rates]
        rates = [record.interest_rate for record in all_rates]
        for date, rate in zip(dates, rates):
            interest_rates[date] = rate

        sorted(interest_rates)

        # Making changes in interest rate if first change in interest rate is after set of collateral
        # (floating interest rates are set by bank and communicated to user
        # - rate already includes additional rate due to lack of collateral
        # therefore any changes in interest rate made during credit lifetime
        # should already include changes in rate caused by setting a collateral.
        # If collateral will be set before first change in interest rate,
        # interest rate must be recalculated.
        collateral_change_in_rate = False
        try:
            collateral = CreditCollateral.objects.get(credit=self.credit)
        except CreditCollateral.DoesNotExists:
            collateral = None
        if collateral:
            if collateral.collateral_set_date < list(interest_rates.keys())[1]:
                collateral_change_in_rate = True

        # Interest rates in installment periods with no additional changes
        interest_rates_final = {}
        rate = initial_interest_rate
        for period in self.basic_installment_dates_list():
            if period in interest_rates:
                rate = interest_rates[period]
                collateral_change_in_rate = False
            elif period >= collateral.collateral_set_date and collateral_change_in_rate:
                rate = initial_interest_rate - self.collateral_rate
            interest_rates_final[period] = rate
        return interest_rates_final
        # rate = 0
        # for period in self.basic_installment_dates_list():
        #     if period in interest_rates:
        #         rate = interest_rates[period]
        #     else:
        #         interest_rates[period] = rate
        # return interest_rates

    def total_installments_for_interest_rates_schedule(self):
        """Returns dictionary of dates and amounts of fixed installments set
        after change of interest rate."""
        # NOTE! Only installments set at interest rate changes starts at the same
        # date as date of new interest rate (all other credit changes like tranches,
        # repayments changes installments form period after changes in credit payments)
        installments = {}

        # Interest rates (dates and installment amounts)
        try:
            installment_values = CreditInterestRate.objects.filter(credit=self.credit).filter(total_installment__gt=0)
        except CreditInterestRate.DoesNotExist:
            installment_values = None
        if not installment_values:
            return

        installment_values = CreditInterestRate.objects.filter(credit=self.credit).filter(total_installmentf__gt=0)
        dates = [record.interest_rate_start_date for record in installment_values]
        amounts = [record.total_installment for record in installment_values]
        for date, amount in zip(dates, amounts):
            installments[date] = amount

        # logger.info("📂 total_installment_for_interest_rates:", installments)
        return installments

    def capital_installments_for_interest_rates_schedule(self):
        """Returns dictionary of dates and amounts of capital installments set
        after change of interest rate."""
        # NOTE! Only installments set at interest rate changes starts at the same date
        # as date of new interest rate (all other credit changes like tranches,
        # repayments changes installments form period after changes in credit payments)

        installments = {}

        # Interest rates (dates and installment amounts)
        try:
            installment_values = CreditInterestRate.objects.filter(credit=self.credit).filter(capital_installment__gt=0)
        except CreditInterestRate.DoesNotExist:
            installment_values = None
        if not installment_values:
            return

        installment_values = CreditInterestRate.objects.filter(credit=self.credit).filter(capital_installment__gt=0)
        dates = [record.interest_rate_start_date for record in installment_values]
        amounts = [record.capital_installment for record in installment_values]
        for date, amount in zip(dates, amounts):
            installments[date] = amount

        # logger.info("📂 capital_installments_for_interest_rates:", installments)
        return installments

    def total_installments_for_tranches_schedule(self):
        """Returns dictionary of dates and amounts of fixed installments set after tranches payments."""
        installments = {}

        # Tranches (dates and installment amounts)
        try:
            installment_values = CreditTranche.objects.filter(credit=self.credit).filter(total_installment__gt=0)
        except CreditTranche.DoesNotExist:
            installment_values = None
        if not installment_values:
            return

        installment_values = CreditTranche.objects.filter(credit=self.credit).filter(total_installment__gt=0)
        dates = [record.tranche_date for record in installment_values]
        amounts = [record.total_installment for record in installment_values]
        for date, amount in zip(dates, amounts):
            installments[date] = amount

        # logger.info("📂 total_installment_for_tranches:", installments)
        return installments

    def capital_installments_for_tranches_schedule(self):
        """Returns dictionary of dates and amounts of capital installments set after tranches payments."""
        installments = {}

        # Tranches (dates and installment amounts)
        try:
            installment_values = CreditTranche.objects.filter(credit=self.credit).filter(capital_installment__gt=0)
        except CreditTranche.DoesNotExist:
            installment_values = None
        if not installment_values:
            return

        installment_values = CreditTranche.objects.filter(credit=self.credit).filter(capital_installment__gt=0)
        dates = [record.tranche_date for record in installment_values]
        amounts = [record.capital_installment for record in installment_values]
        for date, amount in zip(dates, amounts):
            installments[date] = amount

        # logger.info("📂 capital_installments_for_tranches:", installments)
        return installments

    def total_installments_for_repayments_schedule(self):
        """Returns dictionary of dates and amounts of fixed installments set after repayments."""
        installments = {}

        # Early repayments (dates and installment amounts)
        try:
            installment_values = CreditEarlyRepayment.objects.filter(credit=self.credit).filter(total_installment__gt=0)
        except CreditEarlyRepayment.DoesNotExist:
            installment_values = None
        if not installment_values:
            return

        installment_values = CreditEarlyRepayment.objects.filter(credit=self.credit).filter(total_installment__gt=0)
        dates = [record.repayment_date for record in installment_values]
        amounts = [record.total_installment for record in installment_values]

        # Fixed installments after repayments
        for date, amount in zip(dates, amounts):
            installments[date] = amount

        # logger.info("📂 total_installment_for_repayments:", installments)
        return installments

    def capital_installments_for_repayments_schedule(self):
        """Returns dictionary of dates and amounts of capital installments set after repayments."""
        installments = {}

        # Early repayments (dates and installment amounts)
        try:
            installment_values = CreditEarlyRepayment.objects.filter(credit=self.credit).filter(capital_installment__gt=0)
        except CreditEarlyRepayment.DoesNotExist:
            installment_values = None
        if not installment_values:
            return

        installment_values = CreditEarlyRepayment.objects.filter(credit=self.credit).filter(capital_installment__gt=0)
        dates = [record.repayment_date for record in installment_values]
        amounts = [record.capital_installment for record in installment_values]

        # Capital installments after repayments
        for date, amount in zip(dates, amounts):
            installments[date] = amount

        # logger.info("📂 capital_installments_for_repayments:", installments)
        return installments

    def installment_schedule_without_interest_rate_changes(
            self, changes_in_installments: list, initial_installment_value: int):
        """Returns a dictionary of dates and amounts of all (capital or total) installment payments except for
        changes of installment payments caused by interest rate changes."""

        # Note that all changes in installment values caused by either payment of new tranche or
        # credit earlier repayment or setting a collateral has the effect of installment changes one period after
        # the event has occurred.
        # Only changes in interest rate with changes in installment value are occur simultaneously.

        installment_dates_list = self.basic_installment_dates_list()
        installments = dict()
        installment_payments_schedule = dict()

        installment_payments_schedule[self.credit.start_of_payment] = initial_installment_value

        # Combining all changes in installments (except for changes caused by interest rate changes)
        dictionaries = changes_in_installments
        for dictionary in dictionaries:
            if dictionary:
                installment_payments_schedule = installment_payments_schedule | dictionary

        installment_payments_schedule = dict(sorted(installment_payments_schedule.items()))
        # logger.info("📂 installment_payments_schedule:",  installment_payments_schedule)

        # If there is change in installment value before credit installment payment starts (but after setting initial values of credit)
        # (e.g. if payment of first tranche at "start of credit" date changes installment value at "start of payment" day)
        # initial value of installment no longer applies and should be replaced by new value
        # Note that change of installment value made at the same date as start of payment is valid from the following installment payment,
        # initial payment remains unchanged (according to the assumption that all credit changes that affects changes in installment value,
        # except for changes caused by interest rate change, are valid from the next payment).
        if list(installment_payments_schedule.keys())[0] < self.credit.start_of_payment:
            initial_installment_value = list(installment_payments_schedule.values())[0]
            installment_payments_schedule.pop(self.credit.start_of_payment)

        # Adding installment values to installment dates with no changes in value
        dict_len = len(installment_payments_schedule)
        dict_keys = list(installment_payments_schedule.keys())
        dict_values = list(installment_payments_schedule.values())

        # If there is more than one change in installment value during credit lifetime
        if dict_len > 1:
            i = 1
            for element in installment_dates_list:
                if element > dict_keys[i]:
                    installments[element] = dict_values[i]
                    if i < (dict_len - 1):
                        i += 1
                else:
                    installments[element] = dict_values[i - 1]
        # If there is only initial installment value (no changes in installment value during credit lifetime)
        else:
            for element in installment_dates_list:
                installments[element] = initial_installment_value

        return installments

    def installment_schedule_with_interest_rate_changes(
            self, installment_schedule: dict, installments_for_interest_rates: dict):
        """Returns a dictionary of all dates and amounts of (capital or total) installment payments including
        changes of installment payments caused by interest rate changes."""

        installments_dict = installment_schedule
        interest_rates_dict = installments_for_interest_rates
        if interest_rates_dict:
            current_date = self.credit.start_of_credit
            current_installment_amount = 0
            new_value = 0
            for key, value in installments_dict.items():
                if key in interest_rates_dict.keys():
                    current_date = key
                    current_installment_amount = value
                    new_value = interest_rates_dict[key]
                    installments_dict[key] = new_value
                elif key > current_date and value == current_installment_amount:
                    installments_dict[key] = new_value
                else:
                    continue
        return installments_dict

    def installment_grace_period(self, installments: dict):
        """Returns dictionary of dates and installment amounts taking into account the grace period."""
        if self.grace_period > 0:
            i = 0
            for element in installments:
                if i < self.grace_period:
                    installments[element] = 0
                    i += 1
                else:
                    pass
        return installments

    def total_installments_schedule_for_fixed_installments(self):
        """Returns dictionary of dates and amounts of all changed total installments during credit lifetime for credits with fixed installments."""

        # Fixed installments during credit lifetime
        tranches = self.total_installments_for_tranches_schedule()
        if tranches:
            tranches = dict(sorted(tranches.items()))
        repayments = self.total_installments_for_repayments_schedule()

        # Initial value of fixed installment
        # (only if there is no tranches [credit amount paid at once]
        # or initial tranche is set without installment amount [no changes in value of fixed installments])
        if not tranches or list(tranches.values())[0] == 0:
            initial_total_installment = self.credit.total_installment
        else:
            initial_total_installment = list(tranches.values())[0]

        try:
            collateral = CreditCollateral.objects.get(credit=self.credit)
        except CreditCollateral.DoesNotExist:
            collateral = {}
        else:
            collateral = CreditCollateral.objects.get(credit=self.credit)
            if collateral.total_installment:
                collateral = {collateral.collateral_set_date: collateral.total_installment}
            else:
                collateral = {}
        dictionaries = [tranches, repayments, collateral]

        # Fixed installments combined (note that installment changes caused by
        # interest rate change are excluded due to start date at interest rate change date)
        total_installments = self.installment_schedule_without_interest_rate_changes(dictionaries, initial_total_installment)

        # Adding installment changes caused by interest rate change
        interest_rates = self.total_installments_for_interest_rates_schedule()
        total_installments = self.installment_schedule_with_interest_rate_changes(total_installments, interest_rates)

        # Adding grace period
        total_installments = self.installment_grace_period(total_installments)

        # Adding initial date to installment schedule
        if self.credit.start_of_credit < self.credit.start_of_payment:
            total_installments[self.credit.start_of_credit] = 0

        # Calculation of credit final payment in dataframe
        return total_installments

    def total_installments_schedule(self):
        """Returns dictionary of final dates and amounts of all changed total installments during credit lifetime."""

        # Fixed (equal) installments
        if self.credit.installment_type == _("Raty równe"):

            credit_balance = self.credit_balance_schedule()
            full_repayment_date = None
            for key, value in credit_balance.items():
                if round(value, 0) < 0.00001:
                    full_repayment_date = key
                    break
            total_installments = self.total_installments_schedule_for_fixed_installments()
            if full_repayment_date:
                for key, value in total_installments.items():
                    if key > full_repayment_date:
                        total_installments[key] = 0
            return total_installments

        # Decreasing installments
        total_installments = {}
        full_cash_flows = self.credit_balance_calculation()

        for element in full_cash_flows:
            total_installments[element["date"]] = element["total installment"]

        return total_installments

    def capital_installments_schedule_for_decreasing_installments(self):
        """Returns dictionary of final dates and amounts of all changed capital installments during credit lifetime."""
        initial_capital_installment = self.credit.capital_installment

        # Capital installments during credit lifetime
        tranches = self.capital_installments_for_tranches_schedule()
        repayments = self.capital_installments_for_repayments_schedule()
        try:
            collateral = CreditCollateral.objects.get(credit=self.credit)
        except CreditCollateral.DoesNotExist:
            collateral = {}
        else:
            collateral = CreditCollateral.objects.get(credit=self.credit)
            if collateral.capital_installment:
                collateral = {collateral.collateral_set_date: collateral.capital_installment}
            else:
                collateral = {}
        dictionaries = [tranches, repayments, collateral]

        # Capital installments combined (installment changes caused by interest rate
        # change excluded due to start date at interest rate change date)
        capital_installments = self.installment_schedule_without_interest_rate_changes(dictionaries, initial_capital_installment)

        # Adding installment changes caused by interest rate change
        interest_rates = self.capital_installments_for_interest_rates_schedule()
        capital_installments = self.installment_schedule_with_interest_rate_changes(capital_installments, interest_rates)

        # Adding grace period
        capital_installments = self.installment_grace_period(capital_installments)

        # Adding initial date to installment schedule
        if self.credit.start_of_credit < self.credit.start_of_payment:
            capital_installments[self.credit.start_of_credit] = 0

        # Adding final credit repayment calculation
        # OKODOWAĆ po dodaniu salda!

        return capital_installments

    def capital_installments_schedule(self):
        """Returns dictionary of final dates and amounts of all changed
        capital installments during credit lifetime."""

        # Decreasing installments
        if self.credit.installment_type == _("Raty malejące"):
            credit_balance = self.credit_balance_schedule()
            full_repayment_date = None
            for key, value in credit_balance.items():
                if round(value, 0) < 0.00001:
                    full_repayment_date = key
                    break
            capital_installments = self.capital_installments_schedule_for_decreasing_installments()
            if full_repayment_date:
                for key, value in capital_installments.items():
                    if key > full_repayment_date:
                        capital_installments[key] = 0
            return capital_installments

        # Fixed (equal) installments
        capital_installments = {}
        full_cash_flows = self.credit_balance_calculation()

        for element in full_cash_flows:
            capital_installments[element["date"]] = element["capital installment"]

        return capital_installments

    def initial_credit_balance(self):
        """Returns dictionary of date and balance of debt at credit start date"""
        credit_balance = dict()
        credit_balance["date"] = self.credit.start_of_credit

        # Credited insurances and provision
        additional_credited_costs = 0
        if self.credit.credited_provision == _("Tak"):
            additional_credited_costs += self.provision
        if self.credit.life_insurance_first_year:
            additional_credited_costs += self.credit.life_insurance_first_year
        if self.credit.property_insurance_first_year:
            additional_credited_costs += self.credit.property_insurance_first_year

        # Initially received credit amount
        if self.credit.tranches_in_credit == _("Nie"):
            initial_balance = self.credit.credit_amount
        else:
            first_tranche = CreditTranche.objects.filter(credit=self.credit).order_by("tranche_date")[0]
            if first_tranche:
                initial_balance = first_tranche.tranche_amount
            else:
                raise ValueError(_("Brak możliwości wyznaczenia wartości początkowej kredytu."
                                   " Uzupełnij wpierw transze kredytu."))

        # Repayment at initial date
        try:
            early_repayment = CreditEarlyRepayment.objects.filter(credit=self.credit)
        except CreditEarlyRepayment.DoesNotExist:
            early_repayment = None
        if early_repayment:
            early_repayment = CreditEarlyRepayment.objects.filter(credit=self.credit).order_by(
                "repayment_date")[0]
            if early_repayment.repayment_date == credit_balance["date"]:
                initial_balance -= early_repayment.repayment_amount

        credit_balance["credit balance"] = (initial_balance + additional_credited_costs)
        return credit_balance

    def credit_cash_flows_without_interest(self):
        """Returns list of dictionaries with all available information provided by user
        concerning changes in credit before calculating interest and balance of credit."""
        all_dates = self.dates_set()

        basic_installment_dates = self.basic_installment_dates_list()
        payments_from_bank = self.payments_from_bank_schedule()
        early_repayments = self.early_repayments_schedule()
        interest_rates = self.interest_rates_schedule()
        capital_installments = self.capital_installments_schedule_for_decreasing_installments()
        total_installments = self.total_installments_schedule_for_fixed_installments()
        insurance_payments = self.insurance_payments_schedule()
        additional_costs = self.additional_payments_schedule()

        # cf_list_of_dict_keys = ["date", "payment from bank", "early repayment", "interest rate",
        #       "capital installment", "total installment", "insurance", "other costs"]
        cash_flow = []
        for record in all_dates:
            cash_flow.append({"date": record, "payment from bank": 0, "early repayment": 0,
                              "interest rate": 0, "capital installment": 0,
                              "total installment": 0, "insurance": 0, "other costs": 0})

        for element in cash_flow:
            for key, value in payments_from_bank.items():
                if key == element["date"]:
                    element["payment from bank"] += value
        for element in cash_flow:
            for key, value in early_repayments.items():
                if key == element["date"]:
                    element["early repayment"] += value
        for element in cash_flow:
            for key, value in interest_rates.items():
                if key == element["date"]:
                    element["interest rate"] += value
        for element in cash_flow:
            for key, value in capital_installments.items():
                if key == element["date"]:
                    element["capital installment"] += value
        for element in cash_flow:
            for key, value in total_installments.items():
                if key == element["date"]:
                    element["total installment"] += value
        for element in cash_flow:
            for key, value in insurance_payments.items():
                if key == element["date"]:
                    element["insurance"] += value
        for element in cash_flow:
            for key, value in additional_costs.items():
                if key == element["date"]:
                    element["other costs"] += value

        return cash_flow

    def credit_balance_calculation(self):
        """Returns list of dictionaries of all credit dates and cash flows."""
        # Note: All calculations are based on ACT/ACT day count convention.

        initial_balance = self.initial_credit_balance()
        cash_flows = self.credit_cash_flows_without_interest()
        basic_installment_dates = self.basic_installment_dates_list()

        # Auxiliary variables (for calculating changes inbetween installment payment days)
        changes = False
        interest_installment_changes = 0
        interest_rate = 0
        periods_in_cash_flows = len(cash_flows)
        additional_days = False
        normal_days = 0
        leap_days = 0
        i = 0

        # Temporary logger
        user = self.credit.user
        file_directory = str(user.id) + "_credit"
        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, file_directory)):
            os.mkdir(os.path.join(settings.MEDIA_ROOT, file_directory))
        if os.path.exists(os.path.join(settings.MEDIA_ROOT, file_directory, "credit_temp2.txt")):
            os.remove(os.path.join(settings.MEDIA_ROOT, file_directory, "credit_temp2.txt"))
            open(os.path.join(settings.MEDIA_ROOT, file_directory, "credit_temp2.txt"), "x").close()

        with open(os.path.join(settings.MEDIA_ROOT, file_directory, "credit_temp.txt"), "w+") as file:
            file.write(str(initial_balance)+"\n"+"\n")
            file.write(str(cash_flows)+"\n"+"\n")
            file.write(str(basic_installment_dates)+"\n"+"\n")

        def interest_installment_payments_considering_turn_of_the_leap_year():
            days_in_year = 366 if calendar.isleap(element["date"].year) else 365

            if not calendar.isleap(cash_flows[i - 1]["date"].year) and calendar.isleap(element["date"].year):
                change_of_days = int((element["date"] - cash_flows[i - 1]["date"]).days)
                year = cash_flows[i - 1]["date"].year
                days_in_regular_year = int((datetime.date(year=year, month=12, day=31) - cash_flows[i - 1]["date"]).days + 1)
                days_in_leap_year = int((element["date"] - (datetime.date(year=year + 1, month=1, day=1))).days)
                if (days_in_regular_year + days_in_leap_year) != change_of_days:
                    logger.info("🛑 Number of days does not match", element["date"],
                                cash_flows[i - 1]["date"], change_of_days, days_in_regular_year, days_in_leap_year)
                    raise ValueError("Incorrect calculations of number of days for payment at turn of the leap year.")
                regular_year_days = days_in_regular_year + (normal_days if additional_days is True else 0)
                leap_year_days = days_in_leap_year + (leap_days if additional_days is True else 0)
                interest_installment = (round(previous_balance * (interest_rate * regular_year_days / 365), 2)
                                       + round(previous_balance * (interest_rate * leap_year_days / 366), 2)
                                       + (interest_installment_changes if changes is True else 0))

            elif calendar.isleap(cash_flows[i - 1]["date"].year) and not calendar.isleap(element["date"].year):
                change_of_days = int((element["date"] - cash_flows[i - 1]["date"]).days)
                year = cash_flows[i - 1]["date"].year
                days_in_leap_year = int((datetime.date(year=year, month=12, day=31) - cash_flows[i - 1]["date"]).days + 1)
                days_in_regular_year = int((element["date"] - (datetime.date(year=year + 1, month=1, day=1))).days)
                if round(days_in_regular_year) + round(days_in_leap_year) != round(change_of_days):
                    logger.info("🛑 Number of days does not match", element["date"],
                                cash_flows[i - 1]["date"], change_of_days, days_in_regular_year, days_in_leap_year)
                    raise ValueError("Incorrect calculations of number of days for payment at turn of the leap year.")
                regular_year_days = days_in_regular_year + (normal_days if additional_days is True else 0)
                leap_year_days = days_in_leap_year + (leap_days if additional_days is True else 0)
                interest_installment = (round(previous_balance * (interest_rate * leap_year_days / 366), 2)
                                       + round(previous_balance * (interest_rate * regular_year_days / 365), 2)
                                       + (interest_installment_changes if changes is True else 0))

            else:
                if additional_days:
                    leap_year_days = leap_days
                    regular_year_days = normal_days + int((element["date"] - cash_flows[i - 1]["date"]).days)
                    interest_installment = (round(previous_balance * (interest_rate * leap_year_days / 366), 2)
                                           + round(previous_balance * (interest_rate * regular_year_days / 365), 2)
                                           + (interest_installment_changes if changes is True else 0))
                else:
                    installment_period = int((element["date"] - cash_flows[i - 1]["date"]).days)
                    interest_installment = round(previous_balance * decimal.Decimal(interest_rate * installment_period / days_in_year),
                                                 2) + (interest_installment_changes if changes is True else 0)

            return interest_installment

        # For decreasing installments
        if self.credit.installment_type == _("Raty malejące"):
            for element in cash_flows:

                with open(os.path.join(settings.MEDIA_ROOT, file_directory, "credit_temp2.txt"), "a+") as file:
                    file.write(str(i) + "\n")
                    file.write("element[date]: " + str(element["date"]) + "\n")
                    file.write("cash_flows[i][date]: " + str(cash_flows[i]["date"]) + "\n")
                    file.write("changes: " + str(changes) + "\n")
                    file.write("additional_days: " + str(additional_days) + "\n")
                    file.write("normal_days: " + str(normal_days) + " leap_days: " + str(leap_days) + "\n" + "\n")

                # Initial balance
                if element["date"] == initial_balance["date"]:
                    element["interest installment"] = 0
                    element["credit balance"] = initial_balance["credit balance"]
                    i += 1

                # Other cash flows
                else:
                    previous_balance = cash_flows[i - 1]["credit balance"]

                    # All debt is paid scenario
                    if round(previous_balance, 0) == 0:
                        element["capital installment"] = 0
                        element["interest installment"] = 0
                        element["total installment"] = 0
                        element["credit balance"] = 0

                    # Last installment payment scenario
                    elif element["capital installment"] >= (previous_balance + element["payment from bank"]):
                        new_balance = 0
                        # days_in_year = 366 if calendar.isleap(element["date"].year) else 365
                        interest_rate = decimal.Decimal(element["interest rate"] / 100)

                        interest_installment = interest_installment_payments_considering_turn_of_the_leap_year()
                        # interest_installment = round(previous_balance * (interest_rate * installment_period / days_in_year), 2)

                        element["capital installment"] = previous_balance
                        total_installment = interest_installment + previous_balance
                        element["interest installment"] = interest_installment
                        element["total installment"] = total_installment
                        element["credit balance"] = new_balance
                        additional_days = False
                        i += 1

                    # No credit changes (other payments related to credit but not with credit balance) [additional_days settlement]
                    elif element["payment from bank"] == 0 and element["early repayment"] == 0 and element["date"] not in basic_installment_dates:
                        additional_days = True
                        element["credit balance"] = previous_balance
                        element["interest installment"] = None

                        if not calendar.isleap(cash_flows[i - 1]["date"].year) and calendar.isleap(element["date"].year):
                            change_of_days = int((element["date"] - cash_flows[i - 1]["date"]).days)
                            year = cash_flows[i - 1]["date"].year
                            days_in_regular_year = int((datetime.date(year=year, month=12, day=31) - cash_flows[i - 1]["date"]).days + 1)
                            days_in_leap_year = int((element["date"] - (datetime.date(year=year + 1, month=1, day=1))).days)
                            if days_in_regular_year + days_in_leap_year != change_of_days:
                                logger.info("🛑 Number of days does not match", element["date"],
                                            cash_flows[i - 1]["date"], change_of_days, days_in_regular_year, days_in_leap_year)
                                raise ValueError("Incorrect calculations of number of days for payment at turn of the leap year.")
                            normal_days = days_in_regular_year
                            leap_days = days_in_leap_year

                        elif calendar.isleap(cash_flows[i - 1]["date"].year) and not calendar.isleap(element["date"].year):
                            change_of_days = int((element["date"] - cash_flows[i - 1]["date"]).days)
                            year = cash_flows[i - 1]["date"].year
                            days_in_leap_year = int((datetime.date(year=year, month=12, day=31) - cash_flows[i - 1]["date"]).days + 1)
                            days_in_regular_year = int((element["date"] - (datetime.date(year=year + 1, month=1, day=1))).days)
                            if days_in_regular_year + days_in_leap_year != change_of_days:
                                logger.info("🛑 Number of days does not match", element["date"],
                                            cash_flows[i - 1]["date"], change_of_days, days_in_regular_year,
                                            days_in_leap_year)
                                raise ValueError("Incorrect calculations of number of days for payment at turn of the leap year.")
                            normal_days = days_in_regular_year
                            leap_days = days_in_leap_year

                        else:
                            days_in_regular_year = int((element["date"] - cash_flows[i - 1]["date"]).days)
                            normal_days = days_in_regular_year
                            leap_days = 0

                        with open(os.path.join(settings.MEDIA_ROOT, file_directory, "credit_temp2.txt"), "a+") as file:
                            file.write("element[date]: " + str(element["date"]) + "\n")
                            file.write("cash_flows[i - 1][date]: " + str(cash_flows[i - 1]["date"]) + "\n")
                            file.write("NORMAL DAYS: " + str(normal_days) + "\n")
                            file.write("LEAP DAYS: " + str(leap_days) + "\n")

                        i += 1

                    # Changes in credit between installment dates scenario
                    elif ((element["payment from bank"] > 0 or element["early repayment"] > 0)
                          and element["date"] not in basic_installment_dates and element["date"] > self.credit.start_of_credit):
                        changes = True
                        # If rate of interest changes after tranche payment or early repayment date, interest should be calculated at new interest rate
                        if i + 1 < periods_in_cash_flows:
                            if cash_flows[i]["interest rate"] != cash_flows[i+1]["interest rate"]:
                                interest_rate = decimal.Decimal(cash_flows[i+1]["interest rate"]/100)
                        new_balance = previous_balance - element["capital installment"] + element["payment from bank"] - element["early repayment"]
                        days_in_year = 366 if calendar.isleap(element["date"].year) else 365

                        if additional_days:
                            leap_year_days = leap_days
                            regular_year_days = normal_days + int((element["date"] - cash_flows[i - 1]["date"]).days)
                            interest_installment_changes = round(previous_balance * (interest_rate * leap_year_days / 366), 2) \
                                                   + round(previous_balance * (interest_rate * regular_year_days / 365), 2)
                            additional_days = False
                        else:
                            installment_period = int((element["date"] - cash_flows[i - 1]["date"]).days)
                            interest_installment_changes = round(previous_balance * (interest_rate * installment_period / days_in_year), 2)

                        element["credit balance"] = new_balance
                        element["interest installment"] = None
                        previous_balance = new_balance

                        i += 1

                    # Changes in credit at installment dates scenario
                    elif element["payment from bank"] > 0 or element["early repayment"] > 0 or element["date"] in basic_installment_dates:
                        new_balance = previous_balance - element["capital installment"] + element["payment from bank"] - element["early repayment"]
                        # days_in_year = 366 if calendar.isleap(element["date"].year) else 365
                        interest_rate = decimal.Decimal(element["interest rate"] / 100)

                        interest_installment = interest_installment_payments_considering_turn_of_the_leap_year()

                        total_installment = interest_installment + element["capital installment"]
                        element["interest installment"] = interest_installment
                        element["total installment"] = total_installment
                        element["credit balance"] = new_balance
                        previous_balance = new_balance

                        changes = False
                        additional_days = False
                        interest_installment_changes = 0
                        i += 1

            return cash_flows

        # For fixed installments
        if self.credit.installment_type == _("Raty równe"):
            for element in cash_flows:

                with open(os.path.join(settings.MEDIA_ROOT, file_directory, "credit_temp2.txt"), "a+") as file:
                    file.write(str(i) + "\n")
                    file.write("element[date]: " + str(element["date"]) + "\n")
                    file.write("cash_flows[i][date]: " + str(cash_flows[i]["date"]) + "\n")
                    file.write("changes: " + str(changes) + "\n")
                    file.write("additional_days: " + str(additional_days) + "\n")
                    file.write("normal_days: " + str(normal_days) + " leap_days: " + str(leap_days) + "\n" + "\n")

                # Initial balance
                if element["date"] == initial_balance["date"]:
                    element["interest installment"] = 0
                    element["capital installment"] = 0
                    element["credit balance"] = initial_balance["credit balance"]
                    i += 1

                # Other cash flows
                else:
                    previous_balance = cash_flows[i - 1]["credit balance"]
                    element["interest installment"] = 0
                    element["credit balance"] = previous_balance

                    # All debt is paid scenario
                    if round(previous_balance, 0) == 0:
                        element["interest installment"] = 0
                        element["capital installment"] = 0
                        element["total installment"] = 0
                        element["credit balance"] = 0

                    # Last installment scenario
                    elif (element["payment from bank"] == 0
                          and element["total installment"] > 0
                          and (previous_balance - element["early repayment"] - cash_flows[i - 1]["capital installment"] <= 0)):
                        interest_installment = decimal.Decimal(interest_installment_payments_considering_turn_of_the_leap_year())
                        element["credit balance"] = 0
                        # element["capital installment"] = previous_balance
                        element["capital installment"] = (element["total installment"] - interest_installment)
                        element["interest installment"] = interest_installment
                        # Correcting amount of early repayment to value of unpaid debt
                        if (element["capital installment"] + element["early repayment"]) > previous_balance:
                            element["early repayment"] = previous_balance - (element["total installment"] - interest_installment)
                        # element["total installment"] = previous_balance + interest_installment

                        additional_days = False
                        i += 1

                    # No credit changes (other payments related to credit but not with credit balance) [additional_days settlement]
                    elif element["payment from bank"] == 0 and element["early repayment"] == 0 and element["date"] not in basic_installment_dates:
                        additional_days = True
                        element["credit balance"] = previous_balance
                        element["interest installment"] = None

                        if not calendar.isleap(cash_flows[i - 1]["date"].year) and calendar.isleap(element["date"].year):
                            change_of_days = int((element["date"] - cash_flows[i - 1]["date"]).days)
                            year = cash_flows[i - 1]["date"].year
                            days_in_regular_year = int((datetime.date(year=year, month=12, day=31) - cash_flows[i - 1]["date"]).days + 1)
                            days_in_leap_year = int((element["date"] - (datetime.date(year=year + 1, month=1, day=1))).days)
                            if days_in_regular_year + days_in_leap_year != change_of_days:
                                logger.info("🛑 Number of days does not match", element["date"],
                                            cash_flows[i - 1]["date"], change_of_days, days_in_regular_year,
                                            days_in_leap_year)
                                raise ValueError("Incorrect calculations of number of days for payment at turn of the leap year.")
                            normal_days = days_in_regular_year
                            leap_days = days_in_leap_year

                        elif calendar.isleap(cash_flows[i - 1]["date"].year) and not calendar.isleap(element["date"].year):
                            change_of_days = int((element["date"] - cash_flows[i - 1]["date"]).days)
                            year = cash_flows[i - 1]["date"].year
                            days_in_leap_year = int((datetime.date(year=year, month=12, day=31) - cash_flows[i - 1]["date"]).days + 1)
                            days_in_regular_year = int((element["date"] - (datetime.date(year=year + 1, month=1, day=1))).days)
                            if days_in_regular_year + days_in_leap_year != change_of_days:
                                logger.info("🛑 Number of days does not match", element["date"],
                                            cash_flows[i - 1]["date"], change_of_days, days_in_regular_year,
                                            days_in_leap_year)
                                raise ValueError(
                                    "Incorrect calculations of number of days for payment at turn of the leap year.")
                            normal_days = days_in_regular_year
                            leap_days = days_in_leap_year

                        else:
                            days_in_regular_year = int((element["date"] - cash_flows[i - 1]["date"]).days)
                            normal_days = days_in_regular_year
                            leap_days = 0

                        with open(os.path.join(settings.MEDIA_ROOT, file_directory, "credit_temp2.txt"), "a+") as file:
                            file.write("element[date]: " + str(element["date"]) + "\n")
                            file.write("cash_flows[i - 1][date]: " + str(cash_flows[i - 1]["date"]) + "\n")
                            file.write("NORMAL DAYS: " + str(normal_days) + "\n")
                            file.write("LEAP DAYS: " + str(leap_days) + "\n")

                        i += 1

                    # Changes in credit between installment dates scenario
                    elif ((element["payment from bank"] > 0 or element["early repayment"] > 0)
                          and element["date"] not in basic_installment_dates and element["date"] > self.credit.start_of_credit):
                        changes = True
                        # If rate of interest changes after tranche payment or early repayment date, interest should be calculated at new interest rate
                        if i + 1 < periods_in_cash_flows:
                            if cash_flows[i]["interest rate"] != cash_flows[i + 1]["interest rate"]:
                                interest_rate = decimal.Decimal(cash_flows[i + 1]["interest rate"] / 100)
                        new_balance = previous_balance - element["capital installment"] + element["payment from bank"] - element["early repayment"]
                        days_in_year = 366 if calendar.isleap(element["date"].year) else 365

                        if additional_days:
                            leap_year_days = leap_days
                            regular_year_days = normal_days + int((element["date"] - cash_flows[i - 1]["date"]).days)
                            interest_installment_changes = round(previous_balance * (interest_rate * leap_year_days / 366), 2) \
                                                           + round(previous_balance * (interest_rate * regular_year_days / 365), 2)
                            additional_days = False
                        else:
                            installment_period = int((element["date"] - cash_flows[i - 1]["date"]).days)
                            interest_installment_changes = round(previous_balance * (interest_rate * installment_period / days_in_year), 2)

                        element["interest installment"] = None
                        element["capital installment"] = 0
                        element["credit balance"] = new_balance

                        previous_balance = new_balance
                        i += 1

                    # Changes in credit at installment dates scenario
                    elif element["payment from bank"] > 0 or element["early repayment"] > 0 or element["date"] in basic_installment_dates:
                        # days_in_year = 366 if calendar.isleap(element["date"].year) else 365
                        interest_rate = decimal.Decimal(element["interest rate"] / 100)

                        interest_installment = interest_installment_payments_considering_turn_of_the_leap_year()

                        capital_installment = element["total installment"] - interest_installment
                        new_balance = previous_balance - capital_installment + element["payment from bank"] - element["early repayment"]
                        element["interest installment"] = interest_installment
                        element["capital installment"] = capital_installment
                        element["credit balance"] = new_balance

                        previous_balance = new_balance
                        additional_days = False
                        i += 1
                        changes = False
                        interest_installment_changes = 0

            return cash_flows

    def credit_balance_schedule(self):
        """Returns dictionary of dates and credit balance during credit lifetime."""
        full_cash_flows = self.credit_balance_calculation()

        credit_balance = {}
        for element in full_cash_flows:
            credit_balance[element["date"]] = element["credit balance"]

        return credit_balance

    def interest_installment_schedule(self):
        """Returns dictionary of dates and interest installments during credit lifetime."""
        full_cash_flows = self.credit_balance_calculation()

        interest_installment = {}
        for element in full_cash_flows:
            interest_installment[element["date"]] = element["interest installment"]

        return interest_installment

    def early_repayment_modified_schedule(self):
        """Returns dictionary of dates and early repayments during credit lifetime modified with modification the value of unpaid credit."""
        full_cash_flows = self.credit_balance_calculation()

        early_repayment = {}
        for element in full_cash_flows:
            early_repayment[element["date"]] = element["early repayment"]

        return early_repayment

    def insurance_payments_schedule(self):
        """Returns dictionary of dates and amounts of all insurance payments
        except of credited insurances."""
        insurance_payments = {}

        try:
            insurances = CreditInsurance.objects.filter(credit=self.credit)
        except CreditInsurance.DoesNotExist:
            insurances = None

        payments = []
        for insurance in insurances:
            if not insurance.amount:
                continue
            if insurance.frequency == _("Jednorazowo"):
                payments.append((insurance.start_date, insurance.amount))
            else:
                payments.append((insurance.start_date, insurance.amount))
                i = 1
                if insurance.payment_period is not None:
                    frequency = self.frequency(insurance.frequency) if insurance.frequency else 0
                    for number in range(1, insurance.payment_period):
                        payments.append(((insurance.start_date + relativedelta(
                            months=frequency * i)) + relativedelta(
                            day=insurance.start_date.day), insurance.amount))
                        i += 1

        for payment in payments:
            if payment[0] in insurance_payments.keys():
                insurance_payments[payment[0]] += payment[1]
            else:
                insurance_payments[payment[0]] = payment[1]

        return insurance_payments

    def additional_payments_schedule(self):
        """Returns dictionary of dates and amounts of all additional payments except during credit lifetime."""
        additional_payments = {}

        # Not credited provision
        if self.credit.credited_provision == _("Nie"):
            additional_payments[self.credit.start_of_credit] = self.provision

        # Additional costs during credit lifetime
        try:
            additional_costs = CreditAdditionalCost.objects.filter(credit=self.credit).values("cost_amount", "cost_payment_date")
        except CreditAdditionalCost.DoesNotExist:
            additional_costs = []

        for element in additional_costs:
            if element["cost_payment_date"] in additional_payments.keys():
                additional_payments[element["cost_payment_date"]] += element["cost_amount"]
            else:
                additional_payments[element["cost_payment_date"]] = element["cost_amount"]

        return additional_payments

    def all_payments_connected_with_credit(self):
        """Returns dictionary of all dates and payments during credit lifetime"""
        all_payments_schedule = {}
        full_cash_flows = self.credit_balance_calculation()

        for element in full_cash_flows:
            all_payments_schedule[element["date"]] = element["interest installment"]

        return all_payments_schedule
