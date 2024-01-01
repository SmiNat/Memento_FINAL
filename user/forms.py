# from captcha.fields import ReCaptchaField
# from captcha.widgets import ReCaptchaV2Checkbox

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinLengthValidator, ValidationError
from django.forms import BooleanField, EmailField, ModelForm, CharField, widgets
from django.utils.translation import gettext_lazy as _

from .handlers import FORBIDDEN_USERNAME_LIST
from .models import Profile, User


class CustomUserCreationForm(UserCreationForm):
    username = CharField(
        label=_("Nazwa użytkownika"),
        max_length=100,
        required=True,
        help_text=_(
            "Pole wymagane. Min. 8 znaków. "
            "Dozwolone są liczby, cyfry oraz znaki @/./+/-/_ (wyłącznie)."
        ),
        validators=[
            UnicodeUsernameValidator(),
            MinLengthValidator(
                8, _("Nazwa użytkownika musi się składać min. z 8 znaków.")
            ),
        ],
        error_messages={
            "unique": _("Użytkownik o tej nazwie już istnieje."),
        },
    )
    email = EmailField(
        max_length=100, required=True,
        label=_("Adres email"), help_text=_("Pole wymagane."),
    )
    terms_and_conditions = BooleanField(
        required=True,
        initial=False,
        disabled=False,
        error_messages={"required": _("Proszę zaznaczyć to pole, aby kontynuować.")},
        widget=widgets.CheckboxInput(
            attrs={"class": "checkbox-inline", "type": "checkbox", "id": "box"}
        ),
        label=_("Zaakceptuj regulamin strony i politykę ochrony danych osobowych"),
    )
    # captcha = ReCaptchaField(
    #     widget=ReCaptchaV2Checkbox(attrs={"id": "recaptcha"}),
    #     public_key=os.environ.get("RECAPTCHA_PUBLIC_KEY"),
    #     private_key=os.environ.get("RECAPTCHA_PRIVATE_KEY"),
    #     label=_("Nie jestem robotem"),
    # )

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password1",
            "password2",
        ]
        labels = {
            "email": _("Adres email"),
            "username": _("Nazwa użytkownika"),
            "password1": _("Hasło"),
            "password2": _("Powtórz hasło"),
        }

    field_order = [
        "username",
        "email",
        "password1",
        "password2",
        "terms_and_conditions",
        # "captcha",
    ]

    def __init__(self, *args, **kwargs):
        self.user_usernames = kwargs.pop("user_usernames")
        self.user_emails = kwargs.pop("user_emails")
        self.user_usernames = list(
            name.lower() for name in self.user_usernames)
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in ["username", "email", "password1", "password2"]:
                field.widget.attrs.update({"class": "input"})

    def create(self, validated_data):
        """Create and return a user with encrypted password"""
        return get_user_model().objects.create_user(**validated_data)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if not username:
            self.add_error("required",
                           "To pole jest wymagane.")
        elif username.lower() in self.user_usernames:
            self.add_error(
                "username",
                _("Użytkownik o tej nazwie istnieje już w bazie danych. "
                  "Wprowadź inną nazwę.")
            )
        elif username.lower() in FORBIDDEN_USERNAME_LIST:
            self.add_error(
                "username",
                _("Użytkownik o tej nazwie istnieje już w bazie danych. "
                  "Wprowadź inną nazwę.")
            )
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not email:
            self.add_error("required",
                           "To pole jest wymagane.")
        elif email in self.user_emails:
            self.add_error(
                "email",
                _("Istnieje już Użytkownik z tą wartością pola adres email.")
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504


class ProfileForm(ModelForm):
    username = CharField(
        max_length=100,
        required=True,
        label=_("Nazwa użytkownika"),
        help_text=_(
            "Pole wymagane. Min. 8 znaków. "
            "Dozwolone są liczby, cyfry oraz znaki @/./+/-/_ (wyłącznie).",
        ),
        validators=[
            UnicodeUsernameValidator(),
            MinLengthValidator(
                8,
                _("Nazwa użytkownika musi się składać min. z 8 znaków"),
            ),

        ],
        error_messages={
            "unique": _("Użytkownik o tej nazwie już istnieje."),
        },
    )

    class Meta:
        model = Profile
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "city",
            "street",
            "building_number",
            "apartment_number",
            "post_code",
            "country",
            "access_granted_to",
        ]

    def __init__(self, *args, **kwargs):
        self.profile_emails = kwargs.pop("profile_emails")
        self.profile_usernames = kwargs.pop("profile_usernames")
        self.profile_usernames = list(name.lower() for name in self.profile_usernames)
        super(ProfileForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if not username:
            self.add_error("required",
                           "To pole jest wymagane.")
        elif username.lower() in self.profile_usernames:
            self.add_error(
                "username",
                _("Istnieje już profil o podanej nazwie użytkownika w bazie danych. "
                  "Podaj inną nazwę.")
            )
        if username.lower() in FORBIDDEN_USERNAME_LIST:
            self.add_error(
                "username",
                _("Użytkownik o tej nazwie istnieje już w bazie danych. "
                  "Wprowadź inną nazwę.")
            )
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not email:
            self.add_error("required",
                           "To pole jest wymagane.")
        elif email in self.profile_emails:
            self.add_error(
                "email",
                _("Istnieje już profil z tą wartością pola adres email.")
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504


class AddAccessForm(ModelForm):
    class Meta:
        model = Profile
        fields = ["access_granted_to"]

    def __init__(self, *args, **kwargs):
        super(AddAccessForm, self).__init__(*args, **kwargs)
        self.fields["access_granted_to"].widget.attrs.update({"autofocus": True})

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data  # noqa: RET504


class MySetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_("Podaj nowe hasło"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("Powtórz nowe hasło"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
