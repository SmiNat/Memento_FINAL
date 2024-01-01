import logging

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from parameterized import parameterized

from user.forms import (CustomUserCreationForm, MySetPasswordForm,
                        ProfileForm, AddAccessForm)
from user.handlers import FORBIDDEN_USERNAME_LIST
from user.models import Profile

User = get_user_model()
logger = logging.getLogger("test")

"""
NOTE: Messages, help text and other communication information are in Polish
(see: settings/LANGUAGE_CODE).
For full translation see django documentation:
django/django/contrib/auth/locale/pl/LC_MESSAGES/django.po
"""


class CustomUserCreationFormTest(TestCase):
    def test_custom_user_creation_form_empty_fields(self):
        """Test if fields in form are correct."""
        form = CustomUserCreationForm(user_usernames=[], user_emails=[])
        # self.assertIn("captcha", form.fields)   # turned off
        self.assertIn("username", form.fields)
        self.assertIn("email", form.fields)
        self.assertIn("terms_and_conditions", form.fields)
        self.assertIn(("password1" and "password2"), form.fields)

    def test_custom_user_form_empty_fields(self):
        """Test if form has all fields."""
        form = CustomUserCreationForm(user_usernames=[], user_emails=[])
        fields = ["email", "username", "password1", "password2",
                  "terms_and_conditions"]
        for field in fields:
            self.assertIn(field, form.fields)

    def test_custom_user_creation_form_field_labels(self):
        """Test if fields have correct labels."""
        form = CustomUserCreationForm(user_usernames=[], user_emails=[])
        # self.assertEqual(form.fields["captcha"].label, _("Nie jestem robotem"))  # turned off
        self.assertEqual(form.fields["email"].label, _("Adres email"))
        self.assertEqual(form.fields["terms_and_conditions"].label,
                         _("Zaakceptuj regulamin strony i politykę ochrony "
                           "danych osobowych"))
        self.assertEqual(form.fields["username"].label, _("Nazwa użytkownika"))
        self.assertEqual(form.fields["password1"].label, _("Hasło"))
        self.assertEqual(form.fields["password2"].label, _("Potwierdzenie hasła"))  # django translate (>> vs forms.py: "Powtórz hasło")

    def test_custom_user_creation_form_help_text(self):
        """Test if fields have correct help text."""
        form = CustomUserCreationForm(user_usernames=[], user_emails=[])

        # self.assertEqual(form.fields["captcha"].help_text, "")     # turned off
        self.assertEqual(form.fields["email"].help_text, _("Pole wymagane."))
        self.assertEqual(form.fields["terms_and_conditions"].help_text, _(""))
        self.assertEqual(form.fields["username"].help_text,
                         _("Pole wymagane. Min. 8 znaków. Dozwolone są liczby, "
                           "cyfry oraz znaki @/./+/-/_ (wyłącznie)."))
        self.assertEqual(form.fields["password1"].help_text,
                         _("<ul><li>Twoje hasło nie może być zbyt podobne do "
                           "twoich innych danych osobistych."
                           "</li><li>Twoje hasło musi zawierać co najmniej "
                           "8 znaków.</li>"
                           "<li>Twoje hasło nie może być powszechnie używanym "
                           "hasłem.</li>"
                           "<li>Twoje hasło nie może składać się tylko z "
                           "cyfr.</li></ul>"))
        self.assertEqual(form.fields["password2"].help_text,
                         _("Wprowadź to samo hasło ponownie, dla weryfikacji."))

    def test_custom_user_creation_form_error_messages(self):
        """Test if fields have correct error messages."""
        form = CustomUserCreationForm(user_usernames=[], user_emails=[])

        # logger.info("📂 Captcha error message: %s", form.fields["captcha"].error_messages)

        # self.assertEqual(form.fields["captcha"].error_messages, {
        #     "required": _("To pole jest wymagane."),
        #     "captcha_invalid": "Error verifying reCAPTCHA, please try again.",
        #     "captcha_error": "Error verifying reCAPTCHA, please try again.",
        # })     # turned off
        self.assertEqual(form.fields["email"].error_messages,
                         {"required": _("To pole jest wymagane.")})
        self.assertEqual(form.fields["terms_and_conditions"].error_messages,
                         {"required": _("Proszę zaznaczyć to pole, aby "
                                        "kontynuować.")})
        self.assertEqual(form.fields["username"].error_messages, {
            "required": _("To pole jest wymagane."),
            "unique": _("Użytkownik o tej nazwie już istnieje."),
        })
        self.assertEqual(form.fields["password1"].error_messages,
                         {"required": _("To pole jest wymagane.")})
        self.assertEqual(form.fields["password2"].error_messages,
                         {"required": _("To pole jest wymagane.")})

    def test_custom_user_creation_form_widgets(self):
        """Test if fields have correct widgets."""
        form = CustomUserCreationForm(user_usernames=[], user_emails=[])

        # logger.info("📂 Captcha widget: %s", form.fields["captcha"].widget.__class__.__name__)

        # self.assertEqual(form.fields["captcha"].widget.__class__.__name__, "ReCaptchaV2Checkbox")  # turned off
        self.assertEqual(form.fields["email"].widget.__class__.__name__,
                         "EmailInput")
        self.assertEqual(
            form.fields["terms_and_conditions"].widget.__class__.__name__,
            "CheckboxInput")
        self.assertEqual(form.fields["username"].widget.__class__.__name__,
                         "TextInput")
        self.assertEqual(form.fields["password1"].widget.__class__.__name__,
                         form.fields["password2"].widget.__class__.__name__,
                         "PasswordInput")

    def test_custom_user_creation_form_widget_class(self):
        """Test if fields have correct class for widgets."""
        form = CustomUserCreationForm(user_usernames=[], user_emails=[])
        # logger.info("📂 email widget class: %s", form.fields["captcha"].widget.attrs["class"])

        fields = [
            "email",
            "terms_and_conditions",
            # "captcha",    # turned off
            "username",
            "password1",
            "password2",
        ]
        for field in fields:
            if field == "terms_and_conditions":
                self.assertEqual(form.fields[field].widget.attrs["class"],
                                 "checkbox-inline")
            else:
                self.assertEqual(form.fields[field].widget.attrs["class"],
                                 "input")

    def test_custom_user_creation_form_recaptcha(self):
        pass  # turned off

    def test_custom_user_clean_username_method(self):
        """Test if clean method validates username if username is not one of
        the forbidden usernames.
        """
        payload = {
            "username": FORBIDDEN_USERNAME_LIST[0],
            "email": "johndoe@example.com",
            "password1": "testpass456",
            "password2": "testpass456",
            "terms_and_conditions": "on",
            # "captcha": "on",
        }
        form = CustomUserCreationForm(data=payload, user_usernames=[], user_emails=[])
        self.assertFalse(form.is_valid())
        self.assertIn("Użytkownik o tej nazwie istnieje już w bazie danych. "
                      "Wprowadź inną nazwę.", form.errors["username"])

    def test_custom_user_creation_form_is_form_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "username": "johndoe123",
            "email": "johndoe@example.com",
            "password1": "testpass456",
            "password2": "testpass456",
            "terms_and_conditions": "on",
            "captcha": "on",
        }
        form = CustomUserCreationForm(data=payload, user_usernames=[], user_emails=[])
        self.assertTrue(form.is_valid())


class ProfileFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456",
        )
        self.profile = Profile.objects.get(username=self.user.username)
        self.profile.first_name = "John"
        self.profile.last_name = "Doe"
        self.profile.save()

        self.profile_usernames = list(Profile.objects.all().exclude(
            username=self.profile.username).values_list("username", flat=True))
        self.profile_emails = list(Profile.objects.all().exclude(
            email=self.profile.email).values_list("email", flat=True))
        self.form = ProfileForm(profile_usernames=self.profile_usernames,
                                profile_emails=self.profile_emails)
        self.fields = [
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
        self.payload = {
            "username": "janedoe123",
            "email": "janedoe@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "111 222 333",
            "city": "NY",
            "street": "Pułaskiego",
            "building_number": 13,
            "apartment_number": 13,
            "post_code": "10001",
            "country": "US",
            "access_granted_to": "access@example.com",
        }

    def test_profile_form_empty_fields(self):
        """Test if form has all fields."""
        for field in self.fields:
            self.assertIn(field, self.form.fields)

    def test_profile_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["username"].label,
                         _("Nazwa użytkownika"))
        self.assertEqual(self.form.fields["email"].label, _("Adres email"))
        self.assertEqual(self.form.fields["first_name"].label, _("Imię"))
        self.assertEqual(self.form.fields["last_name"].label, _("Nazwisko"))
        self.assertEqual(self.form.fields["phone_number"].label,
                         _("Numer telefonu"))
        self.assertEqual(self.form.fields["city"].label, _("Miasto"))
        self.assertEqual(self.form.fields["street"].label, _("Ulica"))
        self.assertEqual(self.form.fields["building_number"].label,
                         _("Numer budynku"))
        self.assertEqual(self.form.fields["apartment_number"].label,
                         _("Numer mieszkania"))
        self.assertEqual(self.form.fields["post_code"].label, _("Kod pocztowy"))
        self.assertEqual(self.form.fields["country"].label,
                         _("Kraj zamieszkania"))
        self.assertEqual(self.form.fields["access_granted_to"].label, _(
            "Adres email osoby z dostępem do danych",
        ))

    def test_profile_form_help_text(self):
        """Test if fields have correct help text."""
        for field in self.fields:
            if field == "username":
                self.assertEqual(self.form.fields["username"].help_text,
                                 _("Pole wymagane. Min. 8 znaków. Dozwolone są "
                                   "liczby, cyfry oraz znaki @/./+/-/_ "
                                   "(wyłącznie)."))
            elif field == "email":
                self.assertEqual(self.form.fields["email"].help_text,
                                 _("Pole wymagane."))
            else:
                self.assertEqual(self.form.fields[field].help_text, "")

    def test_profile_form_error_messages(self):
        """Test if fields have correct error messages."""
        for field in self.fields:
            if field == "username":
                self.assertEqual(self.form.fields["username"].error_messages,
                                 {"required": "To pole jest wymagane.",
                                  "unique": "Użytkownik o tej nazwie już istnieje."})
            elif field == "building_number" or field == "apartment_number":
                self.assertEqual(self.form.fields[field].error_messages,
                                 {"required": "To pole jest wymagane.",
                                  "invalid": "Wpisz liczbę całkowitą."})
            else:
                self.assertEqual(self.form.fields[field].error_messages,
                                 {"required": "To pole jest wymagane."})

    def test_profile_form_widgets(self):
        """Test if fields have correct widgets."""

        charfields = ["username", "first_name", "last_name", "phone_number",
                      "city", "street", "post_code", "country"]
        for charfield in charfields:
            self.assertEqual(self.form.fields[charfield].widget.__class__.__name__,
                             "TextInput")
        self.assertEqual(self.form.fields["email"].widget.__class__.__name__,
                         "EmailInput")
        self.assertEqual(
            self.form.fields["access_granted_to"].widget.__class__.__name__,
            "EmailInput")
        self.assertEqual(
            self.form.fields["building_number"].widget.__class__.__name__,
            self.form.fields["apartment_number"].widget.__class__.__name__,
            "NumberInput")

    def test_cprofile_clean_username_method(self):
        """Test if clean method validates username if username is not one of
        the forbidden usernames.
        """
        payload = self.payload
        payload["username"] = FORBIDDEN_USERNAME_LIST[0]
        form = ProfileForm(data=payload,
                           profile_usernames=self.profile_usernames,
                           profile_emails=self.profile_emails)
        self.assertFalse(form.is_valid())
        self.assertIn("Użytkownik o tej nazwie istnieje już w bazie danych. "
                      "Wprowadź inną nazwę.", form.errors["username"])

    def test_profile_form_is_valid(self):
        """Test if form is valid with valid data."""
        form = ProfileForm(data=self.payload,
                           profile_usernames=self.profile_usernames,
                           profile_emails=self.profile_emails)
        self.assertTrue(form.is_valid())

    @parameterized.expand(
        [
            ("All good data (checkup)", "", {}, ""),
            ("Not unique field: username", "username", {"username": "johndoe123"},
             "Istnieje już profil o podanej nazwie użytkownika w bazie danych. "
             "Podaj inną nazwę."),
            ("Not unique field: email", "email", {"email": "johndoe@example.com"},
             "Istnieje już profil z tą wartością pola adres email."),
            ("Empty field: username", "username", {"username": ""},
             "To pole jest wymagane."),
            ("Empty field: email", "email", {"email": ""},
             "To pole jest wymagane."),
            ("Too short field: username (min 8 char)", "username",
             {"username": "user12"},
             "Nazwa użytkownika musi się składać min. z 8 znaków"),
            ("Invalid field: username (forbidden char in username)", "username",
             {"username": "user12e%^&"},
             "Wprowadź poprawną nazwę użytkownika. Wartość może zawierać "
             "jedynie litery, cyfry i znaki @/./+/-/_."),
            ("Invalid field 'access_granted_to' (missing '@')", "access_granted_to",
             {"access_granted_to": "accessexample.com"},
             "Wprowadź poprawny adres email."),
            ("Invalid field 'access_granted_to' (missing '.')", "access_granted_to",
             {"access_granted_to": "access@examplecom"},
             "Wprowadź poprawny adres email."),
            ("Invalid field 'apartment_number' (incorrect value)", "apartment_number",
             {"apartment_number": "incorrect"}, "Wpisz liczbę całkowitą."),
            ("Invalid field 'building_number' (negative value are not allowed)",
             "building_number", {"building_number": -12},
             "Upewnij się, że ta wartość jest większa lub równa 0."),
        ]
    )
    def test_profile_form_is_not_valid(
            self, name: str, field: str, new_data: dict, error_msg: str):
        """Test if form is not valid with invalid data."""
        payload = self.payload
        for key, value in new_data.items():
            payload[key] = value
        form = ProfileForm(data=payload,
                           profile_usernames=["johndoe123"],
                           profile_emails=["johndoe@example.com"])
        if name == "All good data (checkup)":
            self.assertTrue(form.is_valid())
        else:
            self.assertFalse(form.is_valid())
            self.assertIn(error_msg, form.errors[field])


class MySetPasswordFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456",
        )
        self.form = MySetPasswordForm(user=self.user)

    def test_profile_form_empty_fields(self):
        """Test if form has all fields."""
        self.assertIn(("new_password1" and "new_password2"), self.form.fields)

    def test_my_set_password_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["new_password1"].label,
                         _("Podaj nowe hasło"))
        self.assertEqual(self.form.fields["new_password2"].label,
                         _("Powtórz nowe hasło"))

    def test_my_set_password_form_error_messages(self):
        """Test if fields have correct error messages."""
        self.assertEqual(
            self.form.fields["new_password1"].error_messages,
            self.form.fields["new_password2"].error_messages,
            {"required": "To pole jest wymagane."}
        )

    def test_my_set_password_form_widgets(self):
        """Test if fields have correct widgets."""
        self.assertEqual(
            self.form.fields["new_password1"].widget.__class__.__name__,
            self.form.fields["new_password2"].widget.__class__.__name__,
            "PasswordInput"
        )

    def test_my_set_password_form_widget_attrs(self):
        """Test if fields have correct widgets."""
        self.assertEqual(
            self.form.fields["new_password1"].widget.attrs,
            self.form.fields["new_password2"].widget.attrs,
            {"autocomplete": "new-password"}
        )

    def test_my_set_password_form_help_text(self):
        """Test if fields have correct help text."""
        self.assertEqual(self.form.fields["new_password1"].help_text,
                         _("<ul><li>Twoje hasło nie może być zbyt podobne do "
                           "twoich innych danych osobistych."
                           "</li><li>Twoje hasło musi zawierać co najmniej "
                           "8 znaków.</li>"
                           "<li>Twoje hasło nie może być powszechnie "
                           "używanym hasłem.</li>"
                           "<li>Twoje hasło nie może składać się tylko "
                           "z cyfr.</li></ul>"))
        self.assertEqual(self.form.fields["new_password2"].help_text, "")

    def test_my_set_password_form_is_valid(self):
        """Test if form is valid with valid data."""
        password_data = {
            "new_password1": "testpass123",
            "new_password2": "testpass123",
        }
        form = MySetPasswordForm(user=self.user, data=password_data)
        self.assertTrue(form.is_valid())


class AddAccessFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456",
        )
        self.profile = Profile.objects.get(username=self.user.username)
        self.profile.access_granted_to = None
        self.profile.save()
        self.form = AddAccessForm()

    def test_add_access_form_empty_fields(self):
        """Test if form has all fields."""
        self.assertIn("access_granted_to", self.form.fields)
        self.assertEqual(len(self.form.fields), 1)

    def test_add_access_form_field_labels(self):
        """Test if fields have correct labels."""
        self.assertEqual(self.form.fields["access_granted_to"].label,
                         _("Adres email osoby z dostępem do danych"))

    def test_add_access_form_error_messages(self):
        """Test if fields have correct error messages."""
        self.assertEqual(
            self.form.fields["access_granted_to"].error_messages,
            {"required": "To pole jest wymagane."}
        )

    def test_add_access_form_widgets(self):
        """Test if fields have correct widgets."""
        self.assertEqual(
            self.form.fields["access_granted_to"].widget.__class__.__name__,
            "EmailInput"
        )

    def test_add_access_form_widget_attrs(self):
        """Test if fields have correct widgets."""
        self.assertEqual(
            self.form.fields["access_granted_to"].widget.attrs,
            {"maxlength": "250", "autofocus": True}
        )

    def test_add_access_form_help_text(self):
        """Test if fields have correct help text."""
        self.assertEqual(self.form.fields["access_granted_to"].help_text, "")

    def test_add_access_form_is_valid(self):
        """Test if form is valid with valid data."""
        payload = {
            "access_granted_to": "some@example.com",
        }
        form = AddAccessForm(data=payload, instance=self.profile)
        self.assertTrue(form.is_valid())
