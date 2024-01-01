import uuid

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .handlers import create_slug


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, username, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email or not username:
            raise ValueError(
                _("Użytkownik musi posiadać adres email i nazwę użytkownika."),
            )
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            **extra_fields,
        )
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, email, password):
        """Create and return a new superuser."""
        user = self.create_user(username=username, email=email, password=password)
        user.username = username
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""
    id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        primary_key=True,
        editable=False,
    )
    email = models.EmailField(
        _("Adres email"),
        max_length=100,
        unique=True,
        help_text=_("Pole wymagane. Dopuszczalna liczba znaków: 100."),
    )
    username = models.CharField(
        _("Nazwa użytkownika"),
        max_length=100,
        unique=True,
        help_text=_(
            "Pole wymagane. Min. 8 znaków. "
            "Dozwolone są liczby, cyfry oraz znaki @/./+/-/_ (wyłącznie).",
        ),
        validators=[
            UnicodeUsernameValidator(),
            MinLengthValidator(
                8,
                _("Nazwa użytkownika musi się składać min. z 8 znaków."),
            ),
        ],
        error_messages={
            "unique": _("Użytkownik o tej nazwie już istnieje."),
        },
    )
    first_name = models.CharField(_("Imię"), max_length=100, blank=True, null=True)
    last_name = models.CharField(_("Nazwisko"), max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(_("Data rejestracji"), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        MinLengthValidator(
            limit_value=8,
            message=_("Nazwa użytkownika musi się składać min. z 8 znaków."),
        ).__call__(self.username)
        UnicodeUsernameValidator().__call__(self.username)
        EmailValidator().__call__(self.email)
        super().save(*args, **kwargs)


class Profile(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        primary_key=True,
        editable=False,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Użytkownik"),
    )
    username = models.CharField(
        _("Nazwa użytkownika"),
        max_length=100,
        unique=True,
        help_text=_("Pole wymagane."),
    )
    email = models.EmailField(
        _("Adres email"),
        max_length=100,
        unique=True,
        help_text=_("Pole wymagane."),
    )
    slug = models.SlugField(null=False, unique=True)
    first_name = models.CharField(
        _("Imię"),
        max_length=100,
        null=True,
        blank=True,
    )
    last_name = models.CharField(
        _("Nazwisko"),
        max_length=100,
        null=True,
        blank=True,
    )
    phone_number = models.CharField(
        _("Numer telefonu"),
        max_length=20,
        null=True,
        blank=True,
    )
    city = models.CharField(
        _("Miasto"),
        max_length=40,
        null=True,
        blank=True,
    )
    street = models.CharField(
        _("Ulica"),
        max_length=100,
        null=True,
        blank=True,
    )
    building_number = models.PositiveSmallIntegerField(
        _("Numer budynku"), null=True, blank=True
    )
    apartment_number = models.PositiveSmallIntegerField(
        _("Numer mieszkania"), null=True, blank=True
    )
    post_code = models.CharField(
        _("Kod pocztowy"),
        max_length=10,
        null=True,
        blank=True,
    )
    country = models.CharField(
        _("Kraj zamieszkania"), max_length=100,
        null=True, blank=True
    )
    access_granted_to = models.EmailField(
        _("Adres email osoby z dostępem do danych"),
        max_length=250, null=True, blank=True
    )
    created = models.DateTimeField(_("Data dodania"), auto_now_add=True)
    updated = models.DateTimeField(_("Data aktualizacji"), auto_now=True)
    __original_access_granted_to = None

    def __init__(self, *args, **kwargs):
        super(Profile, self).__init__(*args, **kwargs)
        self.__original_access_granted_to = self.access_granted_to

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.username})"
        if self.first_name:
            return f"{self.first_name} ({self.username})"
        if self.last_name:
            return f"{self.last_name} ({self.username})"
        return self.username

    def clean(self):
        if not self.email or not self.username:
            raise ValidationError(
                _("Użytkownik musi posiadać adres email i nazwę użytkownika."),
            )
        try:
            MinLengthValidator(
                limit_value=8,
                message=_("Nazwa użytkownika musi się składać min. z 8 znaków."),
            ).__call__(self.username)
            UnicodeUsernameValidator().__call__(self.username)
            EmailValidator().__call__(self.email)
            if self.access_granted_to:
                EmailValidator().__call__(self.access_granted_to)
        except ValidationError as e:
            raise ValidationError(e)

    def save(self, *args, **kwargs):
        slugs = Profile.objects.all().exclude(id=self.id).values_list("slug", flat=True)
        if not self.slug:
            self.slug = create_slug(self.user)
        while self.slug in slugs:
            self.slug = create_slug(self.user)
        self.full_clean()
        self.__original_access_granted_to = self.access_granted_to
        return super().save(*args, **kwargs)
