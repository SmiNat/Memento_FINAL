import logging

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from user.models import Profile
from payment.models import Payment
from connection.models import Attachment, Counterparty
from credit.models import Credit
from trip.models import (Trip, TripReport, TripBasicChecklist, TripAdvancedChecklist,
                         TripAdditionalInfo, TripCost, TripPersonalChecklist)
from renovation.models import Renovation, RenovationCost
from planner.models import ExpenseList, ExpenseItem, ToDoList, ToDoItem
from medical.models import MedCard, Medicine, MedicalVisit, HealthTestResult

logger = logging.getLogger("all")


def general_access(request):
    user = request.user
    access_granted = Profile.objects.filter(
        access_granted_to=user.email).order_by("email")
    if len(access_granted) == 0:
        return False
    return access_granted


def access_page(request):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")
    access_granted = general_access(request)
    context = {"access_granted": access_granted}
    return render(request, "access/access.html", context)


@login_required(login_url="login")
def access_to_models(request, slug, page):
    page_name = "all-shared-data"
    profile = get_object_or_404(Profile, slug=slug)  # slug of user who has the access to the files

    if profile.access_granted_to != request.user.email:
        logger.critical(
            "user: %s - enter page: data-access - 🛑 SAFETY BREACH - "
            "attempt to access data of another user (id: %s)!"
            % (request.user.id, profile.id))
        messages.error(
            request, _("Nie masz uprawnień do tych danych."))
        logout(request)
        return redirect("login")

    credits = Credit.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    credit_schedules = Credit.objects.filter(user=profile.user).filter(
        access_granted_for_schedule=_("Udostępnij dane")).order_by("-updated")
    payments = Payment.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    counterparties = Counterparty.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    attachments = Attachment.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    trips = Trip.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    renovations = Renovation.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    expense_lists = ExpenseList.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    todo_lists = ToDoList.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")

    try:
        medcard = MedCard.objects.get(user=profile.user, access_granted=_("Udostępnij dane"))
    except MedCard.DoesNotExist:
        medcard = None
    try:
        MedCard.objects.get(user=profile.user, access_granted_medicines=_("Udostępnij dane"))
        medicines = Medicine.objects.filter(user=profile.user)
    except MedCard.DoesNotExist or Medicine.DoesNotExist:
        medicines = None
    try:
        MedCard.objects.get(user=profile.user, access_granted_visits=_("Udostępnij dane"))
        med_visits = MedicalVisit.objects.filter(user=profile.user)
    except MedCard.DoesNotExist or MedicalVisit.DoesNotExist:
        med_visits = None
    try:
        MedCard.objects.get(user=profile.user, access_granted_test_results=_("Udostępnij dane"))
        med_results = HealthTestResult.objects.filter(user=profile.user)
    except MedCard.DoesNotExist or HealthTestResult.DoesNotExist:
        med_results = None

    context = {
        "page_name": page_name,
        "slug": profile.slug,
        "page_object_credits": credits,
        "credit_schedules": credit_schedules,
        "page_object_payments": payments,
        "page_object_counterparties": counterparties,
        "page_object_attachments": attachments,
        "page_object_trips": trips,
        "page_object_renovations": renovations,
        "page_object_expense_lists": expense_lists,
        "page_object_todo_lists": todo_lists,
        "medcard": medcard,
        "page_object_medicines": medicines,
        "page_object_med_visits": med_visits,
        "page_object_med_results": med_results,
    }
    return render(request, "access/data_access.html", context)


@login_required(login_url="login")
def access_to_payments(request, slug, page):
    page_name = "access-to-payments"
    profile = get_object_or_404(Profile, slug=slug)

    if profile.access_granted_to != request.user.email:
        logger.critical(
            "user: %s - enter page: data-access - 🛑 SAFETY BREACH - "
            "attempt to access data of another user (id: %s)!"
            % (request.user.id, profile.id))
        messages.error(
            request, _("Nie masz uprawnień do tych danych."))
        logout(request)
        return redirect("login")

    credits = Credit.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    credit_schedules = Credit.objects.filter(user=profile.user).filter(
        access_granted_for_schedule=_("Udostępnij dane")).order_by("-updated")
    payments = Payment.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    counterparties = Counterparty.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    attachments = Attachment.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")

    paginator_credits = Paginator(credits, per_page=3)
    paginator_payments = Paginator(payments, per_page=3)
    paginator_counterparties = Paginator(counterparties, per_page=3)
    paginator_attachments = Paginator(attachments, per_page=3)
    page_object_credits = paginator_credits.get_page(page)
    page_object_payments = paginator_payments.get_page(page)
    page_object_counterparties = paginator_counterparties.get_page(page)
    page_object_attachments = paginator_attachments.get_page(page)

    context = {
        "page_name": page_name,
        "slug": profile.slug,
        "page_object_credits": page_object_credits,
        "page_object_payments": page_object_payments,
        "page_object_counterparties": page_object_counterparties,
        "page_object_attachments": page_object_attachments,
    }
    return render(request, "access/data_access.html", context)


@login_required(login_url="login")
def access_to_planner(request, slug, page):
    page_name = "access-to-planner"
    profile = get_object_or_404(Profile, slug=slug)

    if profile.access_granted_to != request.user.email:
        logger.critical(
            "user: %s - enter page: data-access - 🛑 SAFETY BREACH - "
            "attempt to access data of another user (id: %s)!"
            % (request.user.id, profile.id))
        messages.error(
            request, _("Nie masz uprawnień do tych danych."))
        logout(request)
        return redirect("login")

    trips = Trip.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    renovations = Renovation.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by("-updated")
    expense_lists = ExpenseList.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by(
        "-updated")
    todo_lists = ToDoList.objects.filter(user=profile.user).filter(
        access_granted=_("Udostępnij dane")).order_by(
        "-updated")

    context = {
        "page_name": page_name,
        "slug": profile.slug,
        "page_object_trips": trips,
        "page_object_renovations": renovations,
        "page_object_expense_lists": expense_lists,
        "page_object_todo_lists": todo_lists,
    }
    return render(request, "access/data_access.html", context)


@login_required(login_url="login")
def access_to_medical(request, slug, page):
    page_name = "access-to-medical"
    profile = get_object_or_404(Profile, slug=slug)

    if profile.access_granted_to != request.user.email:
        logger.critical(
            "user: %s - enter page: data-access - 🛑 SAFETY BREACH - "
            "attempt to access data of another user (id: %s)!"
            % (request.user.id, profile.id))
        messages.error(
            request, _("Nie masz uprawnień do tych danych."))
        logout(request)
        return redirect("login")

    try:
        medcard = MedCard.objects.get(user=profile.user,
                                      access_granted=_("Udostępnij dane"))
    except MedCard.DoesNotExist:
        medcard = None
    try:
        MedCard.objects.get(user=profile.user,
                            access_granted_medicines=_("Udostępnij dane"))
        medicines = Medicine.objects.filter(user=profile.user)
    except MedCard.DoesNotExist or Medicine.DoesNotExist:
        medicines = None
    try:
        MedCard.objects.get(user=profile.user,
                            access_granted_visits=_("Udostępnij dane"))
        med_visits = MedicalVisit.objects.filter(user=profile.user)
    except MedCard.DoesNotExist or MedicalVisit.DoesNotExist:
        med_visits = None
    try:
        MedCard.objects.get(user=profile.user,
                            access_granted_test_results=_("Udostępnij dane"))
        med_results = HealthTestResult.objects.filter(user=profile.user)
    except MedCard.DoesNotExist or HealthTestResult.DoesNotExist:
        med_results = None

    context = {
        "page_name": page_name,
        "slug": profile.slug,
        "medcard": medcard,
        "page_object_medicines": medicines,
        "page_object_med_visits": med_visits,
        "page_object_med_results": med_results,
    }
    return render(request, "access/data_access.html", context)
