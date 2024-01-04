import logging

from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import logout
from django.core.validators import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required

from connection.models import Attachment
from .models import MedCard, Medicine, MedicalVisit, HealthTestResult
from .forms import (MedCardForm, MedicineForm,
                    MedicalVisitForm, HealthTestResultForm)

logger = logging.getLogger("all")


def medcard(request):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")
    profile = request.user.profile
    try:
        medcard = MedCard.objects.get(user=request.user)
    except MedCard.DoesNotExist:
        medcard = None
    if medcard:
        if medcard.user != request.user:
            logger.critical(
                "user: %s - enter page: medcard - 🛑 SAFETY BREACH - "
                "attempt to view medcard (id: %s) of another user (id: %s)!"
                % (request.user.id, medcard.id, medcard.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")
    context = {"medcard": medcard, "profile": profile}
    return render(request, "medical/medcard.html", context)


@login_required(login_url="login")
def add_medcard(request):
    page = "add-medcard"
    form = MedCardForm()
    if request.method == "POST":
        form = MedCardForm(request.POST)
        if form.is_valid():
            try:
                med_form = form.save(commit=False)
                med_form.user = request.user
                med_form.save()
                messages.success(request, _("Dodano kartę medyczną."))
                return redirect("medical:medcard")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-medcard - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza.")
                )
        else:
            logger.error(
                "user: %s - enter page: add-medcard - "
                "⚠️ unsuccessful POST with errors : %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {"page": page, "form": form}
    return render(request, "medical/medical_form.html", context)


@login_required(login_url="login")
def edit_medcard(request, pk):
    page = "edit-medcard"
    medcard = MedCard.objects.get(id=pk)
    form = MedCardForm(instance=medcard)
    if medcard:
        if medcard.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-medcard - 🛑 SAFETY BREACH - "
                "attempt to edit v (id: %s) of another user (id: %s)!"
                % (request.user.id, medcard.id, medcard.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = MedCardForm(request.POST, instance=medcard)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zaktualizowano kartę medyczną."))
                return redirect("medical:medcard")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-medcard (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, medcard.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza.")
                )
        else:
            logger.error(
                "user: %s - enter page: edit-medcard (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, medcard.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-medcard (id: %s) - "
            "⚠️invalid request method (required: POST)"
            % (request.user.id, medcard.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {"page": page, "form": form, "medcard": medcard}
    return render(request, "medical/medical_form.html", context)


@login_required(login_url="login")
def delete_medcard(request, pk):
    page = "delete-medcard"
    medcard = MedCard.objects.get(id=pk)
    if medcard:
        if medcard.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-medcard - 🛑 SAFETY BREACH - "
                "attempt to delete medcard (id: %s) of another user (id: %s)!"
                % (request.user.id, medcard.id, medcard.user.id))
            messages.error(request, _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        medcard.delete()
        messages.success(request, _("Usunięto kartę medyczną."))
        return redirect("medical:medcard")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-medcard (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, medcard.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "medcard": medcard}
    return render(request, "medical/medical_delete_form.html", context)

###############################################################################


def medicines(request):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")
    page = "medicines-page"
    profile = request.user.profile

    # Sorting engine - sort queryset by selected field (HTML code)
    order = request.GET.get("sort_data")
    if not order:
        order = "-updated"
    order_in_field_names = order[1:] if order.startswith("-") else order
    if order_in_field_names not in Medicine.field_names():
        messages.error(request, _("Błędny zakres sortowania. Sprawdź czy wskazane nazwy "
                                  "są zgodne z nazwami pól modelu."))
        order = "-updated"

    try:
        medcard = MedCard.objects.get(user=request.user)
    except MedCard.DoesNotExist:
        medcard = None
    try:
        all_medicines = Medicine.objects.filter(user=request.user).order_by(order)
    except Medicine.DoesNotExist:
        all_medicines = None

    # Searching engine - search through selected fields
    # If search results in empty queryset, error message is displayed
    # If search engine is empty, queryset data is displayed in full
    search_query = request.GET.get("q")
    if search_query:
        medicines = Medicine.objects.filter(
            user=request.user).filter(
                Q(drug_name_and_dose__icontains=search_query) |
                # Q(medication_frequency__icontains=search_query) |
                Q(disease__icontains=search_query)
                ).order_by(order)
        if not medicines:
            medicines = all_medicines
            messages.info(request, _("Brak danych spełniających wyszukiwane kryteria."))
    else:
        medicines = all_medicines

    context = {
        "page": page,
        "all_medicines": all_medicines,
        "medicines": medicines,
        "medcard": medcard,
        "profile": profile
    }
    return render(request, "medical/medical.html", context)


@login_required(login_url="login")
def single_medicine(request, pk):
    page = "single-medicine"
    profile = request.user.profile
    try:
        medcard = MedCard.objects.get(user=request.user)
    except MedCard.DoesNotExist:
        medcard = None
    medicine = Medicine.objects.get(id=pk)
    if medicine:
        if medicine.user != request.user:
            logger.critical(
                "user: %s - enter page: single-medicine - 🛑 SAFETY BREACH - "
                "attempt to view medicine (id: %s) of another user (id: %s)!"
                % (request.user.id, medicine.id, medicine.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")
    context = {
        "page": page,
        "medicine": medicine,
        "medcard": medcard,
        "profile": profile
    }
    return render(request, "medical/single_medical.html", context)


@login_required(login_url="login")
def add_medicine(request):
    page = "add-medicine"
    drug_names = list(Medicine.objects.filter(
        user=request.user).values_list("drug_name_and_dose", flat=True))
    form = MedicineForm(drug_names=drug_names)
    if request.method == "POST":
        form = MedicineForm(request.POST, drug_names=drug_names)
        if form.is_valid():
            try:
                medicine_form = form.save(commit=False)
                medicine_form.user = request.user
                medicine_form.save()
                messages.success(request, _("Dodano lek do bazy danych."))
                return redirect("medical:medicines")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-medicine - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza.")
                )
        else:
            logger.error(
                "user: %s - enter page: add-medicine - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {"page": page, "form": form, "drug_names": drug_names}
    return render(request, "medical/medical_form.html", context)


@login_required(login_url="login")
def edit_medicine(request, pk):
    page = "edit-medicine"
    medicine = Medicine.objects.get(id=pk)
    drug_names = list(Medicine.objects.filter(
        user=request.user).exclude(
        id=pk).values_list(
        "drug_name_and_dose", flat=True))
    form = MedicineForm(instance=medicine, drug_names=drug_names)
    if medicine:
        if medicine.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-medicine - 🛑 SAFETY BREACH - "
                "attempt to edit medicine (id: %s) of another user (id: %s)!"
                % (request.user.id, medicine.id, medicine.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = MedicineForm(
            request.POST, instance=medicine, drug_names=drug_names
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zaktualizowano informacje o leku."))
                return redirect("medical:single-medicine", pk=pk)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-medicine (id: %s)- "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, medicine.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza.")
                )
        else:
            logger.error(
                "user: %s - enter page: edit-medicine (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, medicine.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-medicine (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, medicine.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "medicine": medicine,
        "drug_names": drug_names
    }
    return render(request, "medical/medical_form.html", context)


@login_required(login_url="login")
def delete_medicine(request, pk):
    page = "delete-medicine"
    medicine = Medicine.objects.get(id=pk)
    if medicine:
        if medicine.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-medicine - 🛑 SAFETY BREACH - "
                "attempt to delete medicine (id: %s) of another user (id: %s)!"
                % (request.user.id, medicine.id, medicine.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        medicine.delete()
        messages.success(request, _("Usunięto lek z bazy danych."))
        return redirect("medical:medicines")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-medicine (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, medicine.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "medicine": medicine}
    return render(request, "medical/medical_delete_form.html", context)

###############################################################################


def medical_visits(request):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")
    page = "medical-visits-page"
    profile = request.user.profile

    # Sorting engine - sort queryset by selected field (HTML code)
    order = request.GET.get("sort_data")
    if not order:
        order = "-updated"
    order_in_field_names = order[1:] if order.startswith("-") else order
    if order_in_field_names not in MedicalVisit.field_names():
        messages.error(request, _("Błędny zakres sortowania. Sprawdź czy wskazane nazwy "
                                  "są zgodne z nazwami pól modelu."))
        order = "-updated"

    try:
        medcard = MedCard.objects.get(user=request.user)
    except MedCard.DoesNotExist:
        medcard = None
    try:
        all_visits = MedicalVisit.objects.filter(user=request.user).order_by(order)
    except MedicalVisit.DoesNotExist:
        all_visits = None

    # Searching engine - search through selected fields
    # If search results in empty queryset, error message is displayed
    # If search engine is empty, queryset data is displayed in full
    search_query = request.GET.get("q")
    if search_query:
        visits = MedicalVisit.objects.filter(
            user=request.user).filter(
                Q(specialization__icontains=search_query) | Q(doctor__icontains=search_query)
                ).order_by(order)
        if not visits:
            visits = all_visits
            messages.info(request, _("Brak danych spełniających wyszukiwane kryteria."))
    else:
        visits = all_visits

    context = {
        "page": page,
        "profile": profile,
        "all_visits": all_visits,
        "visits": visits,
        "medcard": medcard
    }
    return render(request, "medical/medical.html", context)


@login_required(login_url="login")
def single_visit(request, pk):
    page = "single-visit"
    profile = request.user.profile
    try:
        medcard = MedCard.objects.get(user=request.user)
    except MedCard.DoesNotExist:
        medcard = None
    try:
        visit = MedicalVisit.objects.get(id=pk)
    except MedicalVisit.DoesNotExist:
        visit = None
    try:
        attachments = Attachment.objects.filter(medical_visits=visit.id)
    except Attachment.DoesNotExist:
        attachments = None
    if visit:
        if visit.user != request.user:
            logger.critical(
                "user: %s - enter page: single-visit - 🛑 SAFETY BREACH - "
                "attempt to view visit (id: %s) of another user (id: %s)!"
                % (request.user.id, visit.id, visit.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")
    context = {
        "page": page,
        "visit": visit,
        "medcard": medcard,
        "attachments": attachments,
        "profile": profile
    }
    return render(request, "medical/single_medical.html", context)


@login_required(login_url="login")
def add_visit(request):
    page = "add-visit-page"
    profile = request.user.profile
    queryset = list(MedicalVisit.objects.filter(user=request.user).values(
        "specialization", "visit_date", "visit_time"))
    form = MedicalVisitForm(queryset=queryset)
    if request.method == "POST":
        form = MedicalVisitForm(request.POST, queryset=queryset)
        if form.is_valid():
            try:
                visit_form = form.save(commit=False)
                visit_form.user = request.user
                visit_form.specialization = form.cleaned_data[
                    "specialization"].capitalize()
                visit_form.save()
                messages.success(request, _("Dodano wizytę."))
                return redirect("medical:medical-visits")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-visit - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza.")
                )
        else:
            logger.error(
                "user: %s - enter page: add-visit - "
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
        "profile": profile,
        "queryset": queryset
    }
    return render(request, "medical/medical_form.html", context)


@login_required(login_url="login")
def edit_visit(request, pk):
    page = "edit-visit-page"
    visit = MedicalVisit.objects.get(id=pk)
    queryset = list(MedicalVisit.objects.filter(
        user=request.user).exclude(id=pk).values(
        "specialization", "visit_date", "visit_time")
    )
    form = MedicalVisitForm(instance=visit, queryset=queryset)
    if visit:
        if visit.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-visit - 🛑 SAFETY BREACH - "
                "attempt to edit visit (id: %s) of another user (id: %s)!"
                % (request.user.id, visit.id, visit.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = MedicalVisitForm(
            request.POST, instance=visit, queryset=queryset
        )
        if form.is_valid():
            try:
                visit_form = form.save(commit=False)
                visit_form.specialization = form.cleaned_data[
                    "specialization"].capitalize()
                visit_form.save()
                messages.success(request, _("Zaktualizowano wizytę."))
                return redirect("medical:medical-visits")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-visit (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, visit.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza.")
                )
        else:
            logger.error(
                "user: %s - enter page: edit-visit (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, visit.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-visit (id: %s) - "
            "⚠️invalid request method (required: POST)"
            % (request.user.id, visit.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {"page": page, "form": form, "visit": visit, "queryset": queryset}
    return render(request, "medical/medical_form.html", context)


@login_required(login_url="login")
def delete_visit(request, pk):
    page = "delete-visit"
    visit = MedicalVisit.objects.get(id=pk)
    if visit:
        if visit.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-visit - 🛑 SAFETY BREACH - "
                "attempt to delete visit (id: %s) of another user (id: %s)!"
                % (request.user.id, visit.id, visit.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        visit.delete()
        messages.success(request, _("Usunięto wizytę lekarską."))
        return redirect("medical:medical-visits")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-visit (id: %s) - "
            "⚠️invalid request method (required: POST)"
            % (request.user.id, visit.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "visit": visit}
    return render(request, "medical/medical_delete_form.html", context)

###############################################################################


def test_results(request):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")
    page = "test-results"
    profile = request.user.profile

    # Sorting engine - sort queryset by selected field (HTML code)
    order = request.GET.get("sort_data")
    if not order:
        order = "-updated"
    order_in_field_names = order[1:] if order.startswith("-") else order
    if order_in_field_names not in HealthTestResult.field_names():
        messages.error(request, _("Błędny zakres sortowania. Sprawdź czy wskazane nazwy "
                                  "są zgodne z nazwami pól modelu."))
        order = "-updated"

    try:
        medcard = MedCard.objects.get(user=request.user)
    except MedCard.DoesNotExist:
        medcard = None
    try:
        all_test_results = HealthTestResult.objects.filter(
            user=request.user).order_by(order)
    except HealthTestResult.DoesNotExist:
        all_test_results = None

    # Searching engine - search through selected fields
    # If search results in empty queryset, error message is displayed
    # If search engine is empty, queryset data is displayed in full
    search_query = request.GET.get("q")
    if search_query:
        test_results = HealthTestResult.objects.filter(
            user=request.user).filter(
                Q(name__icontains=search_query) |
                Q(test_result__icontains=search_query) |
                Q(disease__icontains=search_query)
                ).order_by(order)
        if not test_results:
            test_results = all_test_results
            messages.info(request, _("Brak danych spełniających wyszukiwane kryteria."))
    else:
        test_results = all_test_results

    context = {
        "page": page,
        "all_test_results": all_test_results,
        "test_results": test_results,
        "medcard": medcard,
        "profile": profile
    }
    return render(request, "medical/medical.html", context)


@login_required(login_url="login")
def single_test_result(request, pk):
    page = "single-test-result"
    profile = request.user.profile
    try:
        medcard = MedCard.objects.get(user=request.user)
    except MedCard.DoesNotExist:
        medcard = None
    try:
        test_result = HealthTestResult.objects.get(id=pk)
    except HealthTestResult.DoesNotExist:
        test_result = None
    try:
        attachments = Attachment.objects.filter(health_results=test_result.id)
    except Attachment.DoesNotExist:
        attachments = None
    if test_result:
        if test_result.user != request.user:
            logger.critical(
                "user: %s - enter page: single-test-result - 🛑 SAFETY BREACH - "
                "attempt to view test result (id: %s) of another user (id: %s)!"
                % (request.user.id, test_result.id, test_result.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")
    context = {
        "page": page,
        "test_result": test_result,
        "medcard": medcard,
        "profile": profile,
        "attachments": attachments,
    }
    return render(request, "medical/single_medical.html", context)


@login_required(login_url="login")
def add_test_result(request):
    page = "add-test-result"
    profile = request.user.profile
    queryset = list(HealthTestResult.objects.filter(
        user=request.user).values("name", "test_date"))
    form = HealthTestResultForm(queryset=queryset)
    if request.method == "POST":
        form = HealthTestResultForm(request.POST, queryset=queryset)
        if form.is_valid():
            try:
                result_form = form.save(commit=False)
                result_form.user = request.user
                result_form.save()
                messages.success(request, _("Dodano wyniki."))
                return redirect("medical:test-results")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-test-result - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza.")
                )
        else:
            logger.error(
                "user: %s - enter page: add-test-result - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {"page": page,
               "form": form,
               "profile": profile,
               "queryset": queryset
               }
    return render(request, "medical/medical_form.html", context)


@login_required(login_url="login")
def edit_test_result(request, pk):
    page = "edit-test-result"
    test_result = HealthTestResult.objects.get(id=pk)
    queryset = list(HealthTestResult.objects.filter(
        user=request.user).exclude(id=pk).values("name", "test_date"))
    form = HealthTestResultForm(instance=test_result, queryset=queryset)
    if test_result:
        if test_result.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-test-result - 🛑 SAFETY BREACH - "
                "attempt to edit test result (id: %s) of another user (id: %s)!"
                % (request.user.id, test_result.id, test_result.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = HealthTestResultForm(
            request.POST, instance=test_result, queryset=queryset
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zaktualizowano wyniki."))
                return redirect("medical:test-results")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-test-result (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, test_result.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza.")
                )
        else:
            logger.error(
                "user: %s - enter page: edit-test-result (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, test_result.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-test-result (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, test_result.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {"page": page,
               "form": form,
               "test_result": test_result,
               "queryset": queryset
               }
    return render(request, "medical/medical_form.html", context)


@login_required(login_url="login")
def delete_test_result(request, pk):
    page = "delete-test-result"
    test_result = HealthTestResult.objects.get(id=pk)
    if test_result:
        if test_result.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-test-result - 🛑 SAFETY BREACH - "
                "attempt to delete test result (id: %s) of another user (id: %s)!"
                % (request.user.id, test_result.id, test_result.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        test_result.delete()
        messages.success(request, _("Usunięto wyniki badań."))
        return redirect("medical:test-results")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-test-result (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, test_result.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "test_result": test_result}
    return render(request, "medical/medical_delete_form.html", context)
