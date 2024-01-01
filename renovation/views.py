import logging

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from connection.models import Attachment
from .forms import RenovationForm, RenovationCostForm
from .models import Renovation, RenovationCost

logger = logging.getLogger("all")


def renovations(request):
    if not request.user.is_authenticated:
        messages.info(request, "Dostęp tylko dla zalogowanych użytkowników.")
        return redirect("login")

    order = request.GET.get("sort_data")
    if not order:
        order = "-updated"

    try:
        renovations = Renovation.objects.filter(
            user=request.user).order_by(order)
    except Renovation.DoesNotExist:
        renovations = None
    context = {"renovations": renovations}
    return render(request, "renovation/renovations.html", context)


@login_required(login_url="login")
def single_renovation(request, pk):
    profile = request.user.profile
    renovation = Renovation.objects.get(id=pk)
    if renovation:
        if renovation.user != request.user:
            logger.critical(
                "user: %s - enter page: single-renovation - 🛑 SAFETY BREACH - "
                "attempt to view renovation (id: %s) of another user (id: %s)!"
                % (request.user.id, renovation.id, renovation.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")

    try:
        renovation_costs = RenovationCost.objects.filter(renovation=renovation)
        sum_of_costs = renovation.get_all_costs()
        if sum_of_costs and renovation.estimated_cost:
            costs_to_budget = round((sum_of_costs / renovation.estimated_cost)*100, 2)
        else:
            costs_to_budget = 0
    except RenovationCost.DoesNotExist:
        renovation_costs = None
        costs_to_budget = 0
        sum_of_costs = 0
    try:
        attachments = Attachment.objects.filter(renovations=pk)
    except Attachment.DoesNotExist:
        attachments = None

    context = {
        "profile": profile,
        "renovation": renovation,
        "renovation_costs": renovation_costs,
        "costs_to_budget": costs_to_budget,
        "sum_of_costs": sum_of_costs,
        "attachments": attachments,
    }
    return render(request, "renovation/single_renovation.html", context)


@login_required(login_url="login")
def add_renovation(request):
    page = "add-renovation"
    renovation_names = list(Renovation.objects.filter(
        user=request.user).values_list("name", flat=True))
    form = RenovationForm(renovation_names=renovation_names)
    if request.method == "POST":
        form = RenovationForm(request.POST, renovation_names=renovation_names)
        if form.is_valid():
            try:
                renovation_form = form.save(commit=False)
                renovation_form.user = request.user
                renovation_form.save()
                messages.success(request, _("Dodano remont."))
                return redirect("renovation:renovations")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-renovation - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-renovation - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(request,
                           _("Wystąpił błąd podczas zapisu formularza. "
                             "Sprawdź poprawność danych."))
    context = {
        "page": page,
        "form": form,
        "renovation_names": renovation_names,
    }
    return render(request, "renovation/renovation_form.html", context)


@login_required(login_url="login")
def edit_renovation(request, pk):
    page = "edit-renovation"
    renovation = Renovation.objects.get(id=pk)
    if renovation:
        if renovation.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-renovation - 🛑 SAFETY BREACH - "
                "attempt to edit renovation (id: %s) of another user (id: %s)!"
                % (request.user.id, renovation.id, renovation.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    renovation_names = list(Renovation.objects.filter(
        user=request.user).exclude(id=pk).values_list("name", flat=True))
    form = RenovationForm(instance=renovation, renovation_names=renovation_names)
    if request.method == "POST":
        form = RenovationForm(
            request.POST,
            instance=renovation,
            renovation_names=renovation_names,
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zaktualizowano remont."))
                return redirect("renovation:single-renovation", pk=pk)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-renovation (id: %s)- "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, renovation.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-renovation (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, renovation.id, form.errors))
            messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "
                                      "Sprawdź poprawność danych."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-renovation (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, renovation.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "renovation": renovation,
        "renovation_names": renovation_names,
    }
    return render(request, "renovation/renovation_form.html", context)


@login_required(login_url="login")
def delete_renovation(request, pk):
    page = "delete-renovation"
    renovation = Renovation.objects.get(id=pk)
    if renovation:
        if renovation.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-renovation - 🛑 SAFETY BREACH - "
                "attempt to delete renovation (id: %s) of another user (id: %s)!"
                % (request.user.id, renovation.id, renovation.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        # OPTION TO CONSIDER (delete attachment connected to renovation):
        # path = "{0}/{1}/".format(settings.MEDIA_ROOT, str(request.user.id))
        # if os.path.exists(path):
        #     renovation_attachments = Attachment.objects.filter(renovations=renovation)
        #     for attachment in renovation_attachments:
        #         if attachment.attachment_path:
        #             attachment.delete_attachment()
        #         else:
        #             attachment.delete()
        #     messages.success(request,
        #                      _("Usunięto pliki dotyczące remontu '%s'."
        #                        % renovation.name))
        try:
            renovation_costs = RenovationCost.objects.filter(renovation=renovation)
            for cost in renovation_costs:
                cost.delete()
        except RenovationCost.DoesNotExist:
            pass

        renovation.delete()
        messages.success(request,
                         _("Usunięto remont wraz z informacjami dodatkowymi."))
        return redirect("renovation:renovations")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-renovation (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, renovation.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "renovation": renovation}
    return render(request, "renovation/renovation_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_renovation_cost(request, pk):
    page = "add-renovation-cost"
    renovation = Renovation.objects.get(id=pk)
    form = RenovationCostForm()
    if request.method == "POST":
        form = RenovationCostForm(request.POST)
        if form.is_valid():
            try:
                renovation_form = form.save(commit=False)
                renovation_form.renovation = renovation
                renovation_form.user = request.user
                renovation_form.save()
                messages.success(request, _("Dodano koszty remontu."))
                return redirect("renovation:single-renovation", pk=renovation.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-renovation-cost - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "))
        else:
            logger.error(
                "user: %s - enter page: add-renovation-cost - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "
                                      "Sprawdź poprawność danych."))
    context = {
        "page": page,
        "form_cost": form,
        "renovation": renovation,
        "renovation_id": renovation.id,
    }
    return render(request, "renovation/renovation_form.html", context)


@login_required(login_url="login")
def edit_renovation_cost(request, pk):
    page = "edit-renovation-cost"
    renovation_cost = RenovationCost.objects.get(id=pk)
    renovation = renovation_cost.renovation
    renovation_id = renovation_cost.renovation.id
    form = RenovationCostForm(instance=renovation_cost,)
    if renovation_cost:
        if renovation_cost.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-renovation-cost - 🛑 SAFETY BREACH - "
                "attempt to edit renovation cost (id: %s) of another user (id: %s)!"
                % (request.user.id, renovation_cost.id, renovation_cost.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = RenovationCostForm(
            request.POST,
            instance=renovation_cost,
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Uzupełniono remont."))
                return redirect("renovation:single-renovation", pk=renovation_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-renovation-cost (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, renovation_cost.id, e))
                messages.error(request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-renovation-cost (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, renovation_cost.id, form.errors))
            messages.error(request,
                           _("Wystąpił błąd podczas zapisu formularza. "
                             "Sprawdź poprawność danych."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-renovation-cost (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, renovation_cost.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.", status=405)
    context = {
        "page": page,
        "cost": renovation_cost,
        "form_cost": form,
        "renovation": renovation,
        "renovation_id": renovation_id,
    }
    return render(request, "renovation/renovation_form.html", context)


@login_required(login_url="login")
def delete_renovation_cost(request, pk):
    page = "delete-renovation-cost"
    renovation_cost = RenovationCost.objects.get(id=pk)
    if renovation_cost:
        if renovation_cost.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-renovation-cost - 🛑 SAFETY BREACH - "
                "attempt to delete renovation cost (id: %s) of another user (id: %s)!"
                % (request.user.id, renovation_cost.id, renovation_cost.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        renovation_cost.delete()
        messages.success(request, _("Usunięto koszt remontu."))
        return redirect("renovation:renovations")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-renovation-cost (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, renovation_cost.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "cost": renovation_cost}
    return render(request, "renovation/renovation_delete_form.html", context)
