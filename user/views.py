import logging
import os.path
import shutil

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.validators import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from .forms import CustomUserCreationForm, ProfileForm, AddAccessForm
from .models import Profile
from connection.models import Attachment

User = get_user_model()
logger = logging.getLogger("all")


def index_page(request):
    return render(request, "index.html")


def terms_page(request):
    return render(request, "terms_conditions.html")


def contact_page(request):
    return render(request, "contact.html")


def credentials_page(request):
    return render(request, "credentials.html")


def nav_payments_page(request):
    return render(request, "nav_boxes.html", {"page": "nav-payments"})


def nav_planner_page(request):
    return render(request, "nav_boxes.html", {"page": "nav-planner"})


def nav_medical_page(request):
    return render(request, "nav_boxes.html", {"page": "nav-medical"})

##############################################################################


def register_user(request):
    if request.user.is_authenticated:
        return redirect("user-profile")
    page = "register"
    user_usernames = list(
        User.objects.all().values_list("username", flat=True))
    user_emails = list(
        User.objects.all().values_list("email", flat=True))
    form = CustomUserCreationForm(user_usernames=user_usernames, user_emails=user_emails)
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST,
                                      user_usernames=user_usernames,
                                      user_emails=user_emails)
        if form.is_valid():
            user_form = form.save(commit=False)

            # Validate if email and username are unique
            email_list = list(User.objects.values_list("email", flat=True))
            username_list = list(User.objects.values_list("username", flat=True))
            if user_form.username in username_list:
                messages.error(request,
                               _("Użytkownik o podanej nazwie użytkownika "
                                 "istnieje już w bazie danych.",))
            elif user_form.email in email_list:
                messages.error(request,
                               _("Użytkownik o podanym adresie email "
                                 "istnieje już w bazie danych.",))
            # Validate if there is upload folder with the same name as user's id
            elif os.path.exists(os.path.join(settings.MEDIA_ROOT, str(user_form.id))):
                logger.error(
                    "🛑 Attempt to register a user with the same id as folder name "
                    "for attachments stored on server: %s" % user_form.id,
                )
                messages.error(request, _("Użytkownik o tym numerze id "
                                          "posiada już pliki w bazie danych."))
            else:
                try:
                    user_form.save()
                    messages.success(request, _("Utworzono użytkownika."))
                    login(request, user_form)
                    return redirect("user-profile")
                except ValidationError as e:
                    logger.error("⚠️ User Register Validation Error: %s" % e)
                    messages.error(request,
                                   _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error("⚠️ User Register unsuccessful POST with error: %s"
                         % form.errors)
            messages.error(request,
                           _("Wystąpił błąd podczas rejestracji użytkownika."))
    context = {"page": page, "form": form}
    return render(request, "user/login_register.html", context)


def login_user(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, _("Brak użytkownika w bazie danych."))
            return render(request, "user/login_register.html")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("user-profile")
        messages.error(request, _("Nieprawidłowe hasło."))
    return render(request, "user/login_register.html")


@login_required(login_url="login")
def logout_user(request):
    logout(request)
    messages.info(request, _("Użytkownik został wylogowany."))
    return redirect("login")


def user_profile(request):
    if not request.user.is_authenticated:
        return redirect("index")
    profile = Profile.objects.get(user=request.user)
    access_granted_from_list = Profile.objects.filter(access_granted_to=profile.email)
    access_granted_emails = []
    if access_granted_from_list:
        for access in access_granted_from_list:
            access_granted_emails.append(access.email)

    context = {"profile": profile, "access_granted_from": access_granted_emails}
    return render(request, "user/user_profile.html", context)


@login_required(login_url="login")
def edit_account(request):
    profile = request.user.profile
    profile_usernames = list(Profile.objects.all().exclude(
        username=profile.username).values_list("username", flat=True))
    profile_emails = list(Profile.objects.all().exclude(
        email=profile.email).values_list("email", flat=True))
    form = ProfileForm(instance=profile,
                       profile_usernames=profile_usernames,
                       profile_emails=profile_emails)
    if request.method == "POST":
        form = ProfileForm(request.POST,
                           instance=profile,
                           profile_usernames=profile_usernames,
                           profile_emails=profile_emails)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zaktualizowano dane."))
                return redirect("user-profile")
            except ValidationError as e:
                logger.error("user: %s - enter page: edit-profile - "
                             "⚠️ ValidationError with error: %s"
                             % (request.user.id, e))
                messages.error(request,
                               _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error("user: %s - enter page: edit-profile - "
                         "⚠️ unsuccessful POST with error: %s"
                         % (request.user.id, form.errors))
            messages.error(request,
                           _("Wystąpił błąd podczas zapisu formularza. "
                             "Sprawdź poprawność danych."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-account (profile id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, profile.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {"form": form}
    return render(request, "user/profile_form.html", context)


@login_required(login_url="login")
def delete_user(request):
    path = os.path.join(settings.MEDIA_ROOT, str(request.user.id))  # server folder to remove user's files
    credit_directory = str(request.user.id) + "_credit"
    credit_path = os.path.join(settings.MEDIA_ROOT, credit_directory)
    if request.method == "POST":
        try:
            user = User.objects.get(username=request.user)
            # Delete of users uploaded files
            if os.path.exists(path):
                Attachment.delete_all_files(request.user)
                messages.success(request,
                                 _("Usunięto wszystkie pliki użytkownika."))
                logger.info("user: %s - enter page: delete-user - "
                            "user files deleted successfully" % request.user.id)
            # Delete of users credit data
            if os.path.exists(credit_path):
                if os.path.isfile(credit_path) or os.path.islink(credit_path):
                    os.unlink(credit_path)
                    shutil.rmtree(credit_path)
                else:
                    shutil.rmtree(credit_path)
            # Delete of user
            user.delete()
            messages.success(request, _("Użytkownik został usunięty."))
            logger.info("user: %s - enter page: delete-user - "
                        "user deleted successfully" % request.user.id)
            return redirect("index")
        except User.DoesNotExist:
            logger.error("user: %s - enter page: delete-user - "
                         "⚠️ User.DoesNotExist error: %s"
                         % request.user.id)
            messages.error(request, _("Brak użytkownika w bazie danych."))
        except Exception as e:
            logger.error("user: %s - enter page: delete-user - "
                         "⚠️ Exception with error: %s"
                         % (request.user.id, e))
            messages.error(request, _("Wystąpił nieoczekiwany błąd."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-user (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, request.user.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    return render(request, "user/delete_user.html")


@login_required(login_url="login")
def edit_access(request):
    page = "edit-access"
    profile = Profile.objects.get(user=request.user)
    access_granted_to = profile.access_granted_to
    form = AddAccessForm(instance=profile)
    if request.method == "POST":
        form = AddAccessForm(request.POST, instance=profile)
        if form.is_valid():
            access_granted_to = form.cleaned_data["access_granted_to"]
            try:
                profile.access_granted_to = access_granted_to
                profile.save()
                messages.info(request, _("Zaktualizowano dostęp do danych dla "
                                         "zewnętrznego użytkownika."))
                return redirect("user-profile")
            except Exception as e:
                logger.error("user: %s - enter page: edit-access - "
                             "⚠️ Exception with error: %s"
                             % (request.user.id, e))
                messages.error(request, _("Wystąpił nieoczekiwany błąd."))

        else:
            logger.error("user: %s - enter page: edit-access - "
                         "⚠️unsuccessful POST with error: %s"
                         % (request.user.id, form.errors))
            messages.error(request, _("Wystąpił błąd podczas zapisu formularza. "
                                      "Sprawdź poprawność danych."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-access (profile id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, profile.id))
        return HttpResponse("Niepoprawna metoda zapisu formularza.", status=405)
    context = {"page": page, "form": form, "access": access_granted_to}
    return render(request, "user/manage_access.html", context)


@login_required(login_url="login")
def delete_access(request):
    page = "delete-access"
    profile = Profile.objects.get(user=request.user)
    access_granted_to = profile.access_granted_to
    if request.method == "POST":
        try:
            profile.access_granted_to = None
            profile.save()
            messages.info(
                request,
                _("Usunięto dostęp do danych dla zewnętrznego użytkownika."))
            return redirect("user-profile")
        except Exception as e:
            logger.error("user: %s - enter page: delete-access - "
                         "⚠️ Exception with error: %s"
                         % (request.user.id, e))
            messages.error(request, _("Wystąpił nieoczekiwany błąd."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-access (profile id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, profile.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "access": access_granted_to}
    return render(request, "user/manage_access.html", context)
