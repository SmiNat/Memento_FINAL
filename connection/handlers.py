import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import gettext_lazy as _

from memento.settings import MAX_FILE_SIZE, MAX_UPLOADED_FILES

from .forms import AttachmentForm

logger = logging.getLogger("all")


class FileExtension(Exception):
    """File extension is not allowed"""

    pass


def is_number_of_attachments_valid(request, stored_files_in_db):
    if len(stored_files_in_db) >= MAX_UPLOADED_FILES:   # stored_files_in_db instead of list(filter(None, existing_attachments))
        messages.error(
            request,
            _("Osiągnąłeś maksymalny dopuszczalny limit ilości załączników (%s)."
              % MAX_UPLOADED_FILES),
        )
        return False
    return True


def is_size_of_attachment_valid(request, new_file):
    if new_file.size >= MAX_FILE_SIZE:
        max_file_size_in_mb = MAX_FILE_SIZE / (1024 * 1024)
        messages.error(
            request,
            _("Przekroczyłeś maksymalny dopuszczalny rozmiar pliku: %s MB."
              % max_file_size_in_mb),
        )
        return False
    return True


def handle_post_add_attachment(request, user, page, attachment_names):
    form = AttachmentForm(request.POST, request.FILES, attachment_names=attachment_names)
    context = {"page": page, "form": form, "attachment_names": attachment_names}

    try:
        new_file = request.FILES["attachment_path"]
    except MultiValueDictKeyError:
        messages.error(request, _("Zapomniałeś wskazać plik do załączenia."))
        return
    except FileExtension:
        messages.error(request, _("Niedopuszczalny format pliku."))
        return
    except ValidationError as e:
        logger.error("user: %s - enter page: add-attachment - "
                     "⚠️validation error: %s" % (request.user.id, e))
        messages.error(request, _("Błąd formularza. Sprawdź poprawność danych."))
        return

    new_file = request.FILES["attachment_path"]
    # logger.info("📂 New attachment: %s", request.FILES)

    # Verify if file size has acceptable limit
    if not is_size_of_attachment_valid(request, new_file):
        logger.info("user: %s - enter page: add-attachment - "
                    "⚠️invalid attachment size" % request.user.id)
        return render(request, "attachment/attachment_form.html", context)

    if form.is_valid():
        try:
            attachment = form.save(commit=False)
            attachment.user = user
            # logger.info("📂 SAVE:", attachment.save())
            attachment.save()
            form.save_m2m()
            messages.success(request, _("Plik został dodany do bazy danych."))
            logger.info("user: %s - enter page: add-attachment "
                        "(POST method successful)" % request.user.id)
            return redirect("connection:attachments")
        except IntegrityError:
            messages.error(request, _("Dwa załączniki nie mogą posiadać "
                                      "takiej samej nazwy dokumentu."))
        except ValidationError as error:
            logger.error("user: %s - enter page: add-attachment - "
                         "⚠️ValidationError with error: %s"
                         % (request.user.id, error))
            messages.error(request,
                           _("Wystąpił błąd podczas zapisu pliku do bazy danych."))
    else:
        logger.error("user: %s - enter page: add-attachment - "
                     "⚠️unsuccessful POST with error: %s"
                     % (request.user.id, form.errors))
        messages.error(
            request, _("Błąd formularza. Sprawdź, czy formularz zawiera "
                       "odpowiedni format pliku lub nazwa dokumentu się "
                       "nie powtarza."))
        return
