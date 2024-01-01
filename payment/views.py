import logging

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, render

from connection.models import Attachment
from payment.forms import PaymentForm
from payment.models import Payment

logger = logging.getLogger("all")


def payments(request):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")

    order = request.GET.get("sort_data")
    if not order:
        order = "-updated"

    try:
        payments = Payment.objects.filter(
            user=request.user).order_by(order)
    except Payment.DoesNotExist:
        payments = None
    context = {"payments": payments}
    return render(request, "payment/payments.html", context)


@login_required(login_url="login")
def single_payment(request, pk):
    profile = request.user.profile
    payment = Payment.objects.get(id=pk)
    try:
        attachments = Attachment.objects.filter(payments=payment.id)
    except Attachment.DoesNotExist:
        attachments = None
    if payment:
        if payment.user != request.user:
            logger.critical(
                "user: %s - enter page: single-payment - 🛑 SAFETY BREACH - "
                "attempt to view payment (id: %s) of another user (id: %s)!"
                % (request.user.id, payment.id, payment.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")
    context = {
        "profile": profile,
        "payment": payment,
        "attachments": attachments,
    }
    return render(request, "payment/single_payment.html", context)


@login_required(login_url="login")
def add_payment(request):
    page = "add-payment"
    payment_names = list(Payment.objects.filter(
        user=request.user).values_list("name", flat=True))
    form = PaymentForm(payment_names=payment_names)
    if request.method == "POST":
        form = PaymentForm(request.POST, payment_names=payment_names)
        if form.is_valid():
            try:
                payment_form = form.save(commit=False)
                payment_form.user = request.user
                payment_form.save()
                messages.success(request, _("Dodano płatność."))
                return redirect("payment:payments")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-payment - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-payment - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {"page": page, "form": form, "payment_names": payment_names}
    return render(request, "payment/payment_form.html", context)


@login_required(login_url="login")
def edit_payment(request, pk):
    page = "edit-payment"
    payment = Payment.objects.get(id=pk)
    payment_names = list(
        Payment.objects.filter(user=request.user).exclude(id=pk).values_list(
            "name", flat=True))
    form = PaymentForm(instance=payment, payment_names=payment_names)
    if payment:
        if payment.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-payment - 🛑 SAFETY BREACH - "
                "attempt to edit payment (id: %s) of another user (id: %s)!"
                % (request.user.id, payment.id, payment.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment, payment_names=payment_names)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Płatność została zaktualizowana."))
                return redirect("payment:single-payment", pk=pk)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-payment (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, payment.id, e))
                messages.error(request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-payment (id: %s) - "
                "⚠️unsuccessful POST with error: %s"
                % (request.user.id, payment.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. Sprawdź poprawność danych.")
            )
            print("***************", form.errors)
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-payment (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, payment.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "payment": payment,
        "payment_names": payment_names
    }
    return render(request, "payment/payment_form.html", context)


@login_required(login_url="login")
def delete_payment(request, pk):
    page = "delete-payment"
    payment = Payment.objects.get(id=pk)
    if payment:
        if payment.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-medicine - 🛑 SAFETY BREACH - "
                "attempt to delete medicine (id: %s) of another user (id: %s)!"
                % (request.user.id, payment.id, payment.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        payment.delete()
        messages.success(request, _("Płatność została usunięta."))
        return redirect("payment:payments")
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-payment (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, payment.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "payment": payment}
    return render(request, "payment/payment_delete_form.html", context)
