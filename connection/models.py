from __future__ import annotations
import os
import shutil
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from access.enums import Access
from credit.models import Credit
from medical.models import HealthTestResult, MedicalVisit
from payment.models import Payment
from renovation.models import Renovation
from trip.models import Trip
from user.handlers import create_slug


class Counterparty(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik"),
    )
    payments = models.ManyToManyField(
        Payment,
        verbose_name=_("Wskaż płatności"),
    )
    credits = models.ManyToManyField(
        Credit,
        verbose_name=_("Wskaż kredyty"),
    )
    renovations = models.ManyToManyField(
        Renovation,
        verbose_name=_("Wskaż remonty"),
    )
    trips = models.ManyToManyField(
        Trip,
        verbose_name=_("Wskaż podróże"),
    )
    name = models.CharField(
        _("Nazwa"),
        max_length=255,
        help_text=_("Pole wymagane."),
    )
    phone_number = models.CharField(
        _("Numer telefonu - infolinia"),
        max_length=24,
        null=True, blank=True,
    )
    email = models.EmailField(
        _("Adres email - ogólny"), max_length=255,
        blank=True, null=True,
    )
    address = models.CharField(
        _("Adres korespondencyjny"),
        max_length=255,
        blank=True, null=True,
    )
    www = models.URLField(_("Strona internetowa"), blank=True, null=True)
    bank_account = models.CharField(
        _("Numer konta do przelewów"),
        max_length=40,
        blank=True, null=True,
        validators=[RegexValidator("^[A-Z]{0,2}[ ]?[0-9- ]{24,40}$")],
        help_text=_("Dozwolone znaki: A-Z0-9- ."),
    )
    payment_app = models.CharField(
        _("Aplikacja do zarządzania płatnościami"),
        max_length=255,
        blank=True, null=True,
    )
    client_number = models.CharField(
        _("Numer płatnika (klienta)"),
        max_length=255,
        blank=True, null=True,
    )
    primary_contact_name = models.CharField(
        _("Imię i nazwisko"),
        max_length=255,
        blank=True, null=True,
    )
    primary_contact_phone_number = models.CharField(
        _("Numer telefonu"),
        max_length=24,
        null=True, blank=True,
    )
    primary_contact_email = models.EmailField(
        _("Adres email"),
        max_length=255,
        blank=True, null=True,
    )
    secondary_contact_name = models.CharField(
        _("Imię i nazwisko (2)"),
        max_length=255,
        blank=True, null=True,
    )
    secondary_contact_phone_number = models.CharField(
        _("Numer telefonu (2)"),
        max_length=24,
        null=True, blank=True,
    )
    secondary_contact_email = models.EmailField(
        _("Adres email (2)"),
        max_length=255,
        blank=True, null=True,
    )
    notes = models.TextField(
        _("Uwagi"), max_length=500,
        null=True, blank=True,
    )
    access_granted = models.CharField(
        _("Dostęp do danych"), max_length=20,
        choices=Access.choices, default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może "
                    "przeglądać te dane.")
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="unique_cp_name")
        ]

    def __str__(self):
        return str(self.name)

    def __iter__(self):
        """For looping over verbose name and field's value."""
        for field in self._meta.fields:
            yield field.verbose_name, field.value_to_string(self)

    def attachments(self):
        """Return queryset of attachments assign to the counterparty."""
        queryset = self.attachment_set.all().values_list("counterparties__id", flat=True)
        return queryset

    def clean(self):
        if not self.access_granted in Access.values:
            raise ValidationError(_("Błędna wartość pola 'Dostęp do danych' (%s). Sprawdź czy "
                                    "polskie znaki nie zostały zastąpione innymi znakami."
                                    % self.access_granted))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

#######################################################################################


def user_upload_path(instance, filename):
    name = filename
    name_split = [name[:name.rfind(".")], name[name.rfind("."):]]
    return "{0}/{1}{2}".format(
        instance.user.id, instance.slug, name_split[1]
    )


class Attachment(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Użytkownik"),
    )
    slug = models.SlugField(null=False, unique=True)
    payments = models.ManyToManyField(
        Payment,
        blank=True,
        verbose_name=_("Płatności"),
    )
    counterparties = models.ManyToManyField(
        Counterparty,
        blank=True,
        verbose_name=_("Kontrahenci"),
    )
    credits = models.ManyToManyField(
        Credit,
        blank=True,
        verbose_name=_("Kredyty"),
    )
    renovations = models.ManyToManyField(
        Renovation,
        blank=True,
        verbose_name=_("Remonty"),
    )
    trips = models.ManyToManyField(
        Trip,
        blank=True,
        verbose_name=_("Podróże"),
    )
    health_results = models.ManyToManyField(
        HealthTestResult,
        blank=True,
        verbose_name=_("Badania"),
    )
    medical_visits = models.ManyToManyField(
        MedicalVisit,
        blank=True,
        verbose_name=_("Wizyty lekarskie"),
    )
    attachment_name = models.CharField(
        _("Nazwa dokumentu"),
        max_length=255,
        help_text=_("Pole wymagane.")
    )
    attachment_path = models.FileField(
        _("Załącz dokument"),
        upload_to=user_upload_path,
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Tylko pliki pdf oraz png i jpg."),
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "png", "jpg"],
                message=_("Niedopuszczalny format pliku.")
            )
        ],
    )
    file_date = models.DateField(
        _("Data zawarcia dokumentu"), null=True, blank=True,
        help_text=_("Format: YYYY-MM-DD (np. 2020-07-21).")
    )
    file_info = models.TextField(
        _("Informacja o dokumencie"),
        max_length=500,
        null=True, blank=True,
    )
    access_granted = models.CharField(
        _("Dostęp do danych"),
        max_length=20,
        choices=Access.choices,
        default=Access.NO_ACCESS_GRANTED,
        help_text=_("Użytkownik upoważniony do dostępu do danych może przeglądać te dane.")
    )
    created = models.DateField(_("Data dodania"), auto_now_add=True)
    updated = models.DateField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "attachment_name"], name="unique_attachment_name"
            )
        ]

    def __str__(self):
        return str(self.attachment_name)

    def __iter__(self):
        """For looping over verbose name and field's value"""
        for field in self._meta.fields:
            yield field.verbose_name, field.value_to_string(self)

    def attachment_file_path(self):
        """A method to download a file from its upload path by using static"""
        name = self.attachment_path.name
        file_path = os.path.join(settings.MEDIA_URL, name)
        return file_path

    def delete_attachment(self, *args, **kwargs):
        """Delete single attachment from user's upload location"""
        os.remove(os.path.join(settings.MEDIA_ROOT, self.attachment_path.name))
        super(Attachment, self).delete(*args, **kwargs)

    @classmethod
    def delete_all_files(cls, user, delete_path=settings.MEDIA_ROOT):
        """Delete user's upload folder with all files in it"""
        if user is None:
            user_id = cls.user.id
        else:
            user_id = user.id
        path = os.path.join(delete_path, str(user_id))

        if not os.path.exists(path):
            return
        if os.path.isfile(path) or os.path.islink(path):
            os.unlink(path)
        else:
            shutil.rmtree(path)

    def clean(self):
        if not self.access_granted in Access.values:
            raise ValidationError(_("Błędna wartość pola 'Dostęp do danych' (%s). Sprawdź czy "
                                    "polskie znaki nie zostały zastąpione innymi znakami."
                                    % self.access_granted))

    def save(self, *args, **kwargs):
        slugs = Attachment.objects.all().exclude(
            id=self.id).values_list("slug", flat=True)
        if not self.slug:
            self.slug = create_slug(self.user)
        while self.slug in slugs:
            self.slug = create_slug(self.user)
        self.full_clean()
        return super().save(*args, **kwargs)
