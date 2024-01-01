import logging

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from connection.models import Attachment
from .forms import (TripForm, TripReportForm, TripCostForm,
                    TripPersonalChecklistForm, TripBasicChecklistForm,
                    TripAdvancedChecklistForm, TripAdditionalInfoForm)
from .models import (Trip, TripReport, TripCost, TripPersonalChecklist,
                     TripBasicChecklist, TripAdvancedChecklist,
                     TripAdditionalInfo)

logger = logging.getLogger("all")


def trips(request):
    if not request.user.is_authenticated:
        messages.info(request, "Dostęp tylko dla zalogowanych użytkowników.")
        return redirect("login")

    order = request.GET.get("sort_data")
    if not order:
        order = "-updated"

    try:
        trips = Trip.objects.filter(user=request.user).order_by(order)
    except Trip.DoesNotExist:
        trips = None
    context = {"trips": trips}
    return render(request, "trip/trips.html", context)


@login_required(login_url="login")
def single_trip(request, pk):
    profile = request.user.profile
    trip = Trip.objects.get(id=pk)
    if trip:
        if trip.user != request.user:
            logger.critical(
                "user: %s - enter page: single-trip - 🛑 SAFETY BREACH - "
                "attempt to view trip (id: %s) of another user (id: %s)!"
                % (request.user.id, trip.id, trip.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")
    try:
        attachments = Attachment.objects.filter(trips=pk)
    except Attachment.DoesNotExist:
        attachments = None
    try:
        trip_report = TripReport.objects.filter(trip=trip)
    except TripReport.DoesNotExist:
        trip_report = None
    try:
        basic_trip = TripBasicChecklist.objects.filter(trip=trip)
    except TripBasicChecklist.DoesNotExist:
        basic_trip = None
    try:
        advanced_trip = TripAdvancedChecklist.objects.filter(trip=trip)
    except TripAdvancedChecklist.DoesNotExist:
        advanced_trip = None
    try:
        additional_trip = TripAdditionalInfo.objects.filter(trip=trip)
    except TripAdditionalInfo.DoesNotExist:
        additional_trip = None
    try:
        trip_personal_checklist = TripPersonalChecklist.objects.filter(trip=trip)
    except TripPersonalChecklist.DoesNotExist:
        trip_personal_checklist = None
    try:
        trip_costs = TripCost.objects.filter(trip=trip)
    except TripCost.DoesNotExist:
        trip_costs = None

    if trip_costs:
        queryset = TripCost.objects.filter(user=request.user, trip=trip)
        sum_of_costs = trip_costs[0].sum_of_trip_costs(queryset)
        cost_per_person = trip_costs[0].cost_per_person(queryset)
    else:
        trip_costs = None
        queryset = None
        sum_of_costs = 0
        cost_per_person = 0
    if trip.start_date and trip.end_date:
        days = (trip.end_date - trip.start_date).days + 1
    else:
        days = 0
    if trip.start_date and trip.end_date and queryset:
        cost_per_day = trip_costs[0].cost_per_day()
        cost_per_person_per_day = trip_costs[0].cost_per_person_per_day()
    else:
        cost_per_day = 0
        cost_per_person_per_day = 0

    context = {
        "profile": profile,
        "trip": trip,
        "trip_report": trip_report,
        "trip_basic": basic_trip,
        "trip_advanced": advanced_trip,
        "trip_additional": additional_trip,
        "trip_personal_checklist": trip_personal_checklist,
        "trip_costs": trip_costs,
        "sum_of_costs": sum_of_costs,
        "cost_per_person": cost_per_person,
        "cost_per_day": cost_per_day,
        "cost_per_person_per_day": cost_per_person_per_day,
        "days": days,
        "attachments": attachments,
    }
    return render(request, "trip/single_trip.html", context)


@login_required(login_url="login")
def add_trip(request):
    page = "add-trip"
    trip_names = list(Trip.objects.filter(
        user=request.user).values_list("name", flat=True))
    form = TripForm(trip_names=trip_names)
    if request.method == "POST":
        form = TripForm(request.POST, trip_names=trip_names)
        if form.is_valid():
            try:
                trip_form = form.save(commit=False)
                trip_form.user = request.user
                trip_form.save()
                messages.success(request, _("Dodano podróż."))
                return redirect("trip:trips")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-trip - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza.")
                )
        else:
            logger.error(
                "user: %s - enter page: add-trip - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {"page": page, "form": form, "trip_names": trip_names}
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def edit_trip(request, pk):
    page = "edit-trip"
    trip = Trip.objects.get(id=pk)
    trip_names = list(Trip.objects.filter(
        user=request.user).exclude(id=pk).values_list("name", flat=True))
    form = TripForm(instance=trip, trip_names=trip_names)
    if trip:
        if trip.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-trip - 🛑 SAFETY BREACH - "
                "attempt to edit trip (id: %s) of another user (id: %s)!"
                % (request.user.id, trip.id, trip.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = TripForm(request.POST, instance=trip, trip_names=trip_names)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=str(trip.id))
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-trip (id: %s)- "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, trip.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza.")
                )
        else:
            logger.error(
                "user: %s - enter page: edit-trip - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "
                                      "Sprawdź poprawność danych."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-trip (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "trip": trip,
        "form": form,
        "trip_names": trip_names
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def delete_trip(request, pk):
    page = "delete-trip"
    trip = Trip.objects.get(id=pk)
    if trip:
        if trip.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-trip - 🛑 SAFETY BREACH - "
                "attempt to delete trip (id: %s) of another user (id: %s)!"
                % (request.user.id, trip.id, trip.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        try:
            trip_report = TripReport.objects.filter(trip=trip)
        except TripReport.DoesNotExist:
            pass
        else:
            trip_report = TripReport.objects.filter(trip=trip)
            trip_report.delete()
        try:
            basic_trip = TripBasicChecklist.objects.filter(trip=trip)
        except TripBasicChecklist.DoesNotExist:
            pass
        else:
            basic_trip = TripBasicChecklist.objects.filter(trip=trip)
            basic_trip.delete()
        try:
            advanced_trip = TripAdvancedChecklist.objects.filter(trip=trip)
        except TripAdvancedChecklist.DoesNotExist:
            pass
        else:
            advanced_trip = TripAdvancedChecklist.objects.filter(trip=trip)
            advanced_trip.delete()
        try:
            additional_trip = TripAdditionalInfo.objects.filter(trip=trip)
        except TripAdditionalInfo.DoesNotExist:
            pass
        else:
            additional_trip = TripAdditionalInfo.objects.filter(trip=trip)
            additional_trip.delete()

        try:
            trip_costs = TripCost.objects.filter(trip=trip)
        except TripCost.DoesNotExist:
            pass
        else:
            trip_costs = TripCost.objects.filter(trip=trip)
            trip_costs.delete()

        trip.delete()

        messages.success(
            request, _("Usunięto podróż wraz z informacjami dodatkowymi."))
        return redirect("trip:trips")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-trip (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "trip": trip}
    return render(request, "trip/trip_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_trip_report(request, pk):
    page = "add-trip-report"
    trip = Trip.objects.get(id=pk)
    form = TripReportForm()
    if request.method == "POST":
        form = TripReportForm(request.POST)
        if form.is_valid():
            try:
                report_form = form.save(commit=False)
                report_form.trip = trip
                report_form.user = request.user
                trip_id = report_form.trip.id
                report_form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-trip-report - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-trip-report - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {
        "page": page,
        "form_report": form,
        "trip": trip,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def edit_trip_report(request, pk):
    page = "edit-trip-report"
    trip_report = TripReport.objects.get(id=pk)
    trip_id = trip_report.trip.id
    form = TripReportForm(instance=trip_report)
    if trip_report:
        if trip_report.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-trip-report - 🛑 SAFETY BREACH - "
                "attempt to edit trip report (id: %s) of another user (id: %s)!"
                % (request.user.id, trip_report.id, trip_report.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = TripReportForm(request.POST, instance=trip_report)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-trip-report (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, trip_report.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-trip-report (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, trip_report.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-trip-report (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_report.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "trip_report": trip_report,
        "form_report": form,
        "trip": trip_report.trip,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def delete_trip_report(request, pk):
    page = "delete-trip-report"
    trip_report = TripReport.objects.get(id=pk)
    trip_id = trip_report.trip.id
    if trip_report:
        if trip_report.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-trip-report - 🛑 SAFETY BREACH - "
                "attempt to delete trip report (id: %s) of another user (id: %s)!"
                % (request.user.id, trip_report.id, trip_report.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        trip_report.delete()
        messages.success(request, _("Usunięto opis podróży."))
        return redirect("trip:single-trip", pk=trip_id)
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-trip-report (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_report.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "trip_report": trip_report, "trip_id": trip_id}
    return render(request, "trip/trip_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_trip_basic(request, pk):
    page = "add-trip-basic"
    trip_names = list(TripBasicChecklist.objects.filter(
        user=request.user).values_list("name", flat=True))
    trip = Trip.objects.get(id=pk)
    form = TripBasicChecklistForm(trip_names=trip_names)
    if request.method == "POST":
        form = TripBasicChecklistForm(request.POST, trip_names=trip_names)
        if form.is_valid():
            try:
                trip_form = form.save(commit=False)
                trip_form.trip = trip
                trip_form.user = request.user
                trip_form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-trip-basic - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-trip-basic - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {
        "page": page,
        "form_basic": form,
        "trip_names": trip_names,
        "trip": trip,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def edit_trip_basic(request, pk):
    page = "edit-trip-basic"
    trip_names = list(TripBasicChecklist.objects.filter(
        user=request.user).exclude(id=pk).values_list("name", flat=True))
    trip_basic_checklist = TripBasicChecklist.objects.get(id=pk)
    trip_id = trip_basic_checklist.trip.id
    form = TripBasicChecklistForm(
        instance=trip_basic_checklist, trip_names=trip_names)
    if trip_basic_checklist:
        if trip_basic_checklist.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-trip-basic - 🛑 SAFETY BREACH - "
                "attempt to edit trip basic checklist (id: %s) of another user "
                "(id: %s)!"
                % (request.user.id, trip_basic_checklist.id,
                   trip_basic_checklist.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = TripBasicChecklistForm(
            request.POST,
            instance=trip_basic_checklist,
            trip_names=trip_names,
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-trip-basic (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, trip_basic_checklist.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-trip-basic (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, trip_basic_checklist.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-trip-basic (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_basic_checklist.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "trip_basic": trip_basic_checklist,
        "form_basic": form,
        "trip": trip_basic_checklist.trip,
        "trip_names": trip_names,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def delete_trip_basic(request, pk):
    page = "delete-trip-basic"
    trip_basic_checklist = TripBasicChecklist.objects.get(id=pk)
    trip_id = trip_basic_checklist.trip.id
    if trip_basic_checklist:
        if trip_basic_checklist.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-trip-basic - 🛑 SAFETY BREACH - "
                "attempt to delete trip basic checklist (id: %s) of another "
                "user (id: %s)!"
                % (request.user.id, trip_basic_checklist.id,
                   trip_basic_checklist.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        trip_basic_checklist.delete()
        messages.success(request, _("Usunięto podstawowe wyposażenie podróży."))
        return redirect("trip:single-trip", pk=trip_id)
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-trip-basic (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_basic_checklist.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {
        "page": page,
        "trip_basic": trip_basic_checklist,
        "trip_id": trip_id,
    }
    return render(request, "trip/trip_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_trip_advanced(request, pk):
    page = "add-trip-advanced"
    trip_names = list(TripAdvancedChecklist.objects.filter(
        user=request.user).values_list("name", flat=True))
    trip = Trip.objects.get(id=pk)
    form = TripAdvancedChecklistForm(trip_names=trip_names)
    if request.method == "POST":
        form = TripAdvancedChecklistForm(request.POST, trip_names=trip_names)
        if form.is_valid():
            try:
                trip_form = form.save(commit=False)
                trip_form.user = request.user
                trip_form.trip = trip
                trip_form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-trip-advanced - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-trip-advanced - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {
        "page": page,
        "form_advanced": form,
        "trip_names": trip_names,
        "trip": trip,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def edit_trip_advanced(request, pk):
    page = "edit-trip-advanced"
    trip_names = list(TripAdvancedChecklist.objects.filter(
        user=request.user).exclude(id=pk).values_list("name", flat=True))
    trip_advanced_checklist = TripAdvancedChecklist.objects.get(id=pk)
    trip_id = trip_advanced_checklist.trip.id
    form = TripAdvancedChecklistForm(
        instance=trip_advanced_checklist, trip_names=trip_names)
    if trip_advanced_checklist:
        if trip_advanced_checklist.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-trip-advanced - 🛑 SAFETY BREACH - "
                "attempt to edit trip advanced checklist (id: %s) "
                "of another user (id: %s)!"
                % (request.user.id, trip_advanced_checklist.id,
                   trip_advanced_checklist.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = TripAdvancedChecklistForm(
            request.POST,
            instance=trip_advanced_checklist,
            trip_names=trip_names,
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-trip-advanced (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, trip_advanced_checklist.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-trip-advanced (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, trip_advanced_checklist.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-trip-advanced (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_advanced_checklist.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "trip_advanced": trip_advanced_checklist,
        "form_advanced": form,
        "trip": trip_advanced_checklist.trip,
        "trip_names": trip_names,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def delete_trip_advanced(request, pk):
    page = "delete-trip-advanced"
    trip_advanced_checklist = TripAdvancedChecklist.objects.get(id=pk)
    trip_id = trip_advanced_checklist.trip.id
    if trip_advanced_checklist:
        if trip_advanced_checklist.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-trip-advanced - 🛑 SAFETY BREACH - "
                "attempt to delete trip advanced checklist (id: %s) "
                "of another user (id: %s)!"
                % (request.user.id, trip_advanced_checklist.id,
                   trip_advanced_checklist.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        trip_advanced_checklist.delete()
        messages.success(request, _("Usunięto zaawansowane wyposażenie podróży."))
        return redirect("trip:single-trip", pk=trip_id)
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-trip-advanced (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_advanced_checklist.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {
        "page": page,
        "trip_advanced": trip_advanced_checklist,
        "trip_id": trip_id
    }
    return render(request, "trip/trip_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_trip_additional(request, pk):
    page = "add-trip-additional"
    trip_names = list(TripAdditionalInfo.objects.filter(
        user=request.user).values_list("name", flat=True))
    trip = Trip.objects.get(id=pk)
    form = TripAdditionalInfoForm(trip_names=trip_names)
    if request.method == "POST":
        form = TripAdditionalInfoForm(request.POST, trip_names=trip_names)
        if form.is_valid():
            try:
                trip_form = form.save(commit=False)
                trip_form.user = request.user
                trip_form.trip = trip
                trip_form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-trip-additional - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-trip-additional - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {
        "page": page,
        "form_additional": form,
        "trip_names": trip_names,
        "trip": trip,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def edit_trip_additional(request, pk):
    page = "edit-trip-additional"
    trip_names = list(TripAdditionalInfo.objects.filter(
        user=request.user).exclude(id=pk).values_list("name", flat=True))
    trip_additional_info = TripAdditionalInfo.objects.get(id=pk)
    trip_id = trip_additional_info.trip.id
    form = TripAdditionalInfoForm(
        instance=trip_additional_info, trip_names=trip_names)
    if trip_additional_info:
        if trip_additional_info.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-trip-additional - 🛑 SAFETY BREACH - "
                "attempt to edit trip additional information (id: %s) "
                "of another user (id: %s)!"
                % (request.user.id, trip_additional_info.id,
                   trip_additional_info.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = TripAdditionalInfoForm(
            request.POST,
            instance=trip_additional_info,
            trip_names=trip_names,
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-trip-additional (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, trip_additional_info.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-trip-additional (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, trip_additional_info.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-trip-additional (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_additional_info.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "trip_additional": trip_additional_info,
        "form_additional": form,
        "trip": trip_additional_info.trip,
        "trip_names": trip_names,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def delete_trip_additional(request, pk):
    page = "delete-trip-additional"
    trip_additional_info = TripAdditionalInfo.objects.get(id=pk)
    trip_id = trip_additional_info.trip.id
    if trip_additional_info:
        if trip_additional_info.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-trip-additional - 🛑 SAFETY BREACH - "
                "attempt to delete trip additional information (id: %s) "
                "of another user (id: %s)!"
                % (request.user.id, trip_additional_info.id,
                    trip_additional_info.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        trip_additional_info.delete()
        messages.success(request, _("Usunięto dodatkowe informacje o podróży."))
        return redirect("trip:single-trip", pk=trip_id)
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-trip-additional (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_additional_info.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {
        "page": page,
        "trip_additional": trip_additional_info,
        "trip_id": trip_id
    }
    return render(request, "trip/trip_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_trip_personal_checklist(request, pk):
    page = "add-trip-personal-checklist"
    trip_names = list(TripPersonalChecklist.objects.filter(
        user=request.user).values_list("name", flat=True))
    trip = Trip.objects.get(id=pk)
    form = TripPersonalChecklistForm(trip_names=trip_names)
    if request.method == "POST":
        form = TripPersonalChecklistForm(request.POST, trip_names=trip_names)
        if form.is_valid():
            try:
                trip_form = form.save(commit=False)
                trip_form.user = request.user
                trip_form.trip = trip
                trip_form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-trip-personal-checklist - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-trip-personal-checklist - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {
        "page": page,
        "form_checklist": form,
        "trip_names": trip_names,
        "trip": trip,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def edit_trip_personal_checklist(request, pk):
    page = "edit-trip-personal-checklist"
    trip_checklist = TripPersonalChecklist.objects.get(id=pk)
    trip_names = list(TripPersonalChecklist.objects.filter(
        user=request.user).exclude(id=pk).values_list("name", flat=True))
    trip_id = trip_checklist.trip.id
    form = TripPersonalChecklistForm(
        instance=trip_checklist, trip_names=trip_names)
    if trip_checklist:
        if trip_checklist.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-trip-personal-checklist - "
                "🛑 SAFETY BREACH - attempt to edit trip personal checklist "
                "(id: %s) of another user (id: %s)!"
                % (request.user.id, trip_checklist.id, trip_checklist.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = TripPersonalChecklistForm(
            request.POST,
            instance=trip_checklist,
            trip_names=trip_names
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-trip-personal-checklist (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, trip_checklist.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-trip-personal-checklist (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, trip_checklist.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-trip-personal-checklist (id: %s) - "
            "⚠️invalid request method (required: POST)"
            % (request.user.id, trip_checklist.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "trip_checklist": trip_checklist,
        "form_checklist": form,
        "trip_names": trip_names,
        "trip": trip_checklist.trip,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def delete_trip_personal_checklist(request, pk):
    page = "delete-trip-personal-checklist"
    trip_checklist = TripPersonalChecklist.objects.get(id=pk)
    trip_id = trip_checklist.trip.id
    if trip_checklist:
        if trip_checklist.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-trip-personal-checklist - "
                "🛑 SAFETY BREACH - attempt to delete trip personal checklist "
                "(id: %s) of another user (id: %s)!"
                % (request.user.id, trip_checklist.id, trip_checklist.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        trip_checklist.delete()
        messages.success(request, _("Usunięto dodatkowe elementy podróży."))
        return redirect("trip:single-trip", pk=trip_id)
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-trip-personal-checklist (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_checklist.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {
        "page": page,
        "trip_checklist": trip_checklist,
        "trip_id": trip_id
    }
    return render(request, "trip/trip_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_trip_cost(request, pk):
    page = "add-trip-cost"
    trip = Trip.objects.get(id=pk)
    form = TripCostForm()
    if request.method == "POST":
        form = TripCostForm(request.POST)
        if form.is_valid():
            try:
                trip_form = form.save(commit=False)
                trip_form.user = request.user
                trip_form.trip = trip
                trip_form.save()
                messages.success(request, _("Uzupełniono koszty podroży."))
                return redirect("trip:single-trip", pk=trip.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-trip-cost - "
                    "⚠️ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-trip-cost - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {
        "page": page,
        "form_cost": form,
        "trip": trip,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def edit_trip_cost(request, pk):
    page = "edit-trip-cost"
    trip_cost = TripCost.objects.get(id=pk)
    trip_id = trip_cost.trip.id
    form = TripCostForm(instance=trip_cost)
    if trip_cost:
        if trip_cost.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-trip-cost - 🛑 SAFETY BREACH - "
                "attempt to edit trip cost (id: %s) of another user (id: %s)!"
                % (request.user.id, trip_cost.id, trip_cost.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = TripCostForm(request.POST, instance=trip_cost)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Uzupełniono podróż."))
                return redirect("trip:single-trip", pk=trip_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-trip-cost (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, trip_cost.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-trip-cost (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, trip_cost.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-trip-cost (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_cost.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "trip_cost": trip_cost,
        "form_cost": form,
        "trip": trip_cost.trip,
    }
    return render(request, "trip/trip_form.html", context)


@login_required(login_url="login")
def delete_trip_cost(request, pk):
    page = "delete-trip-cost"
    trip_cost = TripCost.objects.get(id=pk)
    trip_id = trip_cost.trip.id
    if trip_cost:
        if trip_cost.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-trip-cost - 🛑 SAFETY BREACH - "
                "attempt to delete trip cost (id: %s) of another user (id: %s)!"
                % (request.user.id, trip_cost.id, trip_cost.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        trip_cost.delete()
        messages.success(request, _("Usunięto koszt podróży."))
        return redirect("trip:single-trip", pk=trip_id)
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-trip-cost (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, trip_cost.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "trip_cost": trip_cost, "trip_id": trip_id}
    return render(request, "trip/trip_delete_form.html", context)
