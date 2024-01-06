import logging

from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import gettext_lazy as _

from .forms import AttachmentForm, CounterpartyForm
from .models import Attachment, Counterparty
from payment.models import Payment
from credit.models import Credit
from renovation.models import Renovation
from trip.models import Trip
from medical.models import HealthTestResult, MedicalVisit
from .handlers import (
    handle_post_add_attachment,
    is_number_of_attachments_valid
)
from user.models import Profile

logger = logging.getLogger("all")
User = get_user_model()


def counterparties(request):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")

    # Sorting engine - sort queryset by selected field (HTML code)
    order = request.GET.get("sort_data")
    if not order:
        order = "-updated"
    order_in_field_names = order[1:] if order.startswith("-") else order
    if order_in_field_names not in Counterparty.field_names():
        messages.error(request, _("Błędny zakres sortowania. Sprawdź czy wskazane nazwy "
                                  "są zgodne z nazwami pól modelu."))
        order = "-updated"

    try:
        all_counterparties = Counterparty.objects.filter(
            user=request.user).order_by(order)
    except Counterparty.DoesNotExist:
        all_counterparties = None

    # Searching engine - search by name or value of estimated cost (gte)
    # If search engine is empty, queryset data is displayed in full
    search_query = request.GET.get("q")
    if search_query:
        counterparties = Counterparty.objects.filter(
            user=request.user).filter(name__icontains=search_query).order_by(order)
    else:
        counterparties = None
    if not counterparties:
        counterparties = all_counterparties

    context = {"cps": counterparties, "all_cps": all_counterparties}
    return render(request, "counterparty/counterparties.html", context)


@login_required(login_url="login")
def single_counterparty(request, pk):
    profile = request.user.profile
    counterparty = Counterparty.objects.get(id=pk)
    if counterparty:
        if counterparty.user != request.user:
            logger.critical(
                "user: %s - enter page: single-counterparty - 🛑 SAFETY BREACH - "
                "attempt to view counterparty (id: %s) of another user (id: %s)!"
                % (request.user.id, counterparty.id, counterparty.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")
    attachments = Attachment.objects.filter(counterparties=counterparty.id)
    context = {
        "profile": profile,
        "cp": counterparty,
        "attachments": attachments,
    }
    return render(request, "counterparty/single_counterparty.html", context)


@login_required(login_url="login")
def add_counterparty(request):
    page = "add-counterparty"
    cp_names = list(
        Counterparty.objects.filter(user=request.user).values_list("name", flat=True))
    form = CounterpartyForm(cp_names=cp_names)
    form.fields["payments"].queryset = Payment.objects.filter(user=request.user)
    form.fields["credits"].queryset = Credit.objects.filter(user=request.user)
    form.fields["renovations"].queryset = Renovation.objects.filter(user=request.user)
    form.fields["trips"].queryset = Trip.objects.filter(user=request.user)
    if request.method == "POST":
        form = CounterpartyForm(request.POST, cp_names=cp_names)
        form.fields["payments"].queryset = Payment.objects.filter(user=request.user)
        form.fields["credits"].queryset = Credit.objects.filter(user=request.user)
        form.fields["renovations"].queryset = Renovation.objects.filter(user=request.user)
        form.fields["trips"].queryset = Trip.objects.filter(user=request.user)
        if form.is_valid():
            counterparty = form.save(commit=False)
            counterparty.user = request.user
            counterparty.name = form.cleaned_data["name"].capitalize()
            if form.cleaned_data.get("email", None):
                counterparty.email = form.cleaned_data["email"].strip()
            if form.cleaned_data.get("primary_contact_email", None):
                counterparty.primary_contact_email = form.cleaned_data[
                        "primary_contact_email"].strip()
            counterparty.save()
            form.save_m2m()
            messages.success(request, _("Dodano kontrahenta."))
            return redirect("connection:counterparties")
        else:
            logger.error(
                "user: %s - enter page: add-counterparty - "
                "⚠️unsuccessful POST with errors : %s"
                % (request.user.id, form.errors))
            messages.error(
                request, _("Wystąpił błąd podczas zapisu formularza. "
                           "Sprawdź poprawność danych."))
    context = {"page": page, "form": form, "cp_names": cp_names}
    return render(request, "counterparty/counterparty_form.html", context)


@login_required(login_url="login")
def edit_counterparty(request, pk):
    page = "edit-counterparty"
    counterparty = Counterparty.objects.get(id=pk)
    cp_names = list(Counterparty.objects.filter(
        user=request.user).exclude(id=pk).values_list("name", flat=True))
    form = CounterpartyForm(instance=counterparty, cp_names=cp_names)
    form.fields["payments"].queryset = Payment.objects.filter(user=counterparty.user)
    form.fields["credits"].queryset = Credit.objects.filter(user=request.user)
    form.fields["renovations"].queryset = Renovation.objects.filter(user=request.user)
    form.fields["trips"].queryset = Trip.objects.filter(user=request.user)
    if counterparty:
        if counterparty.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-counterparty - 🛑 SAFETY BREACH - "
                "attempt to edit counterparty (id: %s) of another user (id: %s)!"
                % (request.user.id, counterparty.id, counterparty.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = CounterpartyForm(request.POST, request.FILES, instance=counterparty, cp_names=cp_names)
        form.fields["payments"].queryset = Payment.objects.filter(user=counterparty.user)
        form.fields["credits"].queryset = Credit.objects.filter(user=request.user)
        form.fields["renovations"].queryset = Renovation.objects.filter(user=request.user)
        form.fields["trips"].queryset = Trip.objects.filter(user=request.user)
        if form.is_valid():
            counterparty = form.save(commit=False)
            if form.cleaned_data.get("email", None):
                counterparty.email = form.cleaned_data["email"].strip()
            if form.cleaned_data.get("primary_contact_email", None):
                counterparty.primary_contact_email = form.cleaned_data[
                        "primary_contact_email"].strip()
            counterparty.name = form.cleaned_data["name"].capitalize()
            counterparty.save()
            messages.success(request, _("Dane kontrahenta zostały zaktualizowane."))
            return redirect("connection:single-counterparty", pk=pk)
        else:
            logger.error(
                "user: %s - enter page: edit-counterparty (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, counterparty.id, form.errors))
            messages.error(
                request, _("Wystąpił błąd podczas zapisu formularza. "
                           "Sprawdź poprawność danych."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-counterparty (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, counterparty.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.", status=405)
    context = {"page": page, "form": form, "cp": counterparty, "cp_names": cp_names}
    return render(request, "counterparty/counterparty_form.html", context)


@login_required(login_url="login")
def delete_counterparty(request, pk):
    page = "delete-counterparty"
    counterparty = Counterparty.objects.get(id=pk)
    if counterparty:
        if counterparty.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-counterparty - 🛑 SAFETY BREACH - "
                "attempt to delete counterparty (id: %s) of another user (id: %s)!"
                % (request.user.id, counterparty.id, counterparty.user.id))
            messages.error(request, _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        counterparty.delete()
        messages.success(request, _("Usunięto kontrahenta."))
        return redirect("connection:counterparties")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-counterparty (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, counterparty.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "counterparty": counterparty}
    return render(request, "counterparty/counterparty_delete_form.html", context)


###############################################################################
# ATTACHMENT
###############################################################################

def attachments(request):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")
    profile = request.user.profile
    attachments = Attachment.objects.filter(user=request.user)
    context = {
        "attachments": attachments,
        "profile": profile,
    }
    return render(request, "attachment/attachments.html", context)


@login_required(login_url="login")
def download_attachment(request, slug, pk):
    attachment = Attachment.objects.get(id=pk)
    profile = get_object_or_404(Profile, slug=slug)

    try:    # ZABLOKOWAĆ DO TESTÓW / ODBLOKOWAĆ!
        attachment.attachment_path.file
    except FileNotFoundError as e:
        messages.error(request, _("Brak załącznika w bazie danych."))
        logger.error(
            "user: %s - enter page: download-attachment (id: %s) - "
            "⚠️no attachment found in database!"
            % (request.user.id, attachment.id))
        return redirect("connection:attachments")
    if attachment:
        if attachment.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-counterparty - 🛑 SAFETY BREACH - "
                "attempt to download attachment (id: %s) of another user (id: %s)!"
                % (request.user.id, attachment.id, attachment.user.id))
            messages.error(request, _("Nie masz uprawnień do tych danych."))
            logout(request)
            return redirect("login")
        if str(request.session["_auth_user_id"]) != str(attachment.user.id):
            logger.critical(
                "user: %s - enter page: delete-counterparty - 🛑 SAFETY BREACH - "
                "attempt to download attachment (id: %s) of another user (id: %s)!"
                % (request.user.id, attachment.id, attachment.user.id))
            messages.error(request, _("Nie masz uprawnień do tych danych."))
            logout(request)
            return redirect("login")

    response = FileResponse(attachment.attachment_path,
                            as_attachment=True,
                            filename=attachment.attachment_path.name)
    return response


@login_required(login_url="login")
def add_attachment(request):  # uwaga! nie zapomnij w html w <form> o enctype="multipart/form-data"
    page = "add-attachment"
    user = request.user
    attachment_names = list(Attachment.objects.filter(
        user=user).values_list("attachment_name", flat=True))
    form = AttachmentForm(attachment_names=attachment_names)
    form.fields["payments"].queryset = Payment.objects.filter(user=user)
    form.fields["counterparties"].queryset = Counterparty.objects.filter(user=user)
    form.fields["renovations"].queryset = Renovation.objects.filter(user=user)
    form.fields["credits"].queryset = Credit.objects.filter(user=user)
    form.fields["trips"].queryset = Trip.objects.filter(user=user)
    form.fields["health_results"].queryset = HealthTestResult.objects.filter(user=user)
    form.fields["medical_visits"].queryset = MedicalVisit.objects.filter(user=user)

    # NOTE! The order of if's is important! Do not change it!

    existing_records_in_db = Attachment.objects.filter(
        user=user).values_list('attachment_path', flat=True)
    # logger.info("user: %s - enter page: add-attachment - existing attachment records: %s" (request.user.id, existing_records_in_db))
    stored_files_in_db = [file_path for file_path in existing_records_in_db if file_path]
    # logger.info("user: %s - enter page: add-attachment - number of attachments stored in DB: %s; files stored in DB: %s" %(request.user.id, len(stored_files_in_db), stored_files_in_db))

    # Verify if number of files does not exceed maximum number of allowed files
    if not is_number_of_attachments_valid(request, stored_files_in_db):
        logger.info("user: %s - enter page: add-attachments - "
                    "⚠️ maximum limit of attachments reached"
                    % request.user.id)
        return redirect("connection:attachments")

    if request.method == "POST":
        result = handle_post_add_attachment(request, user, page, attachment_names)
        if result:
            return result
    context = {"page": page, "form": form, "attachment_names": attachment_names}
    return render(request, "attachment/attachment_form.html", context)


@login_required(login_url="login")
def delete_attachment(request, pk):
    page = "delete-attachment"
    try:    # ZABLOKOWAĆ DO TESTÓW / ODBLOKOWAĆ!
        attachment = Attachment.objects.get(id=pk)
    except (Attachment.DoesNotExist, ValueError) as error:
        logger.error(
            "user: %s - enter page: delete-attachment (id: %s) - "
            "⚠️ unsuccessful POST - id of attachment not found in database; "
            "error: %s" % (request.user.id, pk, error))
        messages.error(request, _("Brak załącznika w bazie danych."))
        return redirect("connection:attachments")
    if attachment:
        if attachment.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-attachment - 🛑 SAFETY BREACH - "
                "attempt to delete attachment of another user (id: %s)!"
                % (request.user.id, attachment.id))
            messages.error(request, _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
        if not attachment.attachment_path:
            logger.error("user: %s - enter page: delete-attachment (id: %s) - "
                "⚠️ unsuccessful POST - attachment (%s) not found in database; "
                "record of attachment instance deleted from database; "
                % (request.user.id, pk, attachment.attachment_name))
            messages.info(request,
                          _("Brak załącznika w bazie danych. Usunięto rekord z bazy danych."))
            attachment.delete()
            return redirect("connection:attachments")
    if request.method == "POST":
        try:
            attachment.delete_attachment()
            messages.success(request, _("Załącznik został usunięty."))
            return redirect("connection:attachments")
        except FileNotFoundError as error:  # ZABLOKOWAĆ DO TESTÓW / ODBLOKOWAĆ!
            logger.error(
                "user: %s - enter page: delete-attachment (id: %s) - "
                "⚠️ unsuccessful POST - no attachment found in database, "
                "record of attachment instance deleted from database; error: %s"
                % (request.user.id, attachment.id, error))
            messages.info(request,
                          _("Brak załącznika w bazie danych. Usunięto rekord z bazy danych."))
            attachment.delete()
            return redirect("connection:attachments")
        except PermissionError as error:
            logger.error(
                "user: %s - enter page: delete-attachment (id: %s) - "
                "⚠️ unsuccessful POST - permission denied; error: %s"
                % (request.user.id, attachment.id, error))
            messages.error(
                request, _("Odmowa dostępu. Spróbuj po ponownym zalogowaniu się "
                           "lub zgłoś problem do administratora."))
            return redirect("connection:attachments")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-attachment - "
            "⚠️ invalid request method (required: POST)"
            % request.user.id)
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "attachment": attachment}
    return render(request, "attachment/attachment_delete_form.html", context)
