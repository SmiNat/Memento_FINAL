import logging
import os
import shutil
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from parameterized import parameterized
from reportlab.pdfgen.canvas import Canvas

from connection.factories import AttachmentFactory
from user.forms import (CustomUserCreationForm, ProfileForm, AddAccessForm,
                        MySetPasswordForm)
from user.models import Profile

User = get_user_model()
logger = logging.getLogger("test")


class BasicUrlsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456",
        )
        self.profile = Profile.objects.get(user=self.user)

    @parameterized.expand(
        [
            ("index", ""),
            ("contact", "/contact/"),
            ("how-it-works", "/how-it-works/"),
            ("terms-conditions", "/terms-conditions/"),
            ("credentials", "/credentials/"),
            ("nav-payments", "/nav-payments/"),
            ("nav-planner", "/nav-planner/"),
            ("nav-medical", "/nav-medical/"),
            ("login", "/login/"),
            ("register", "/register/"),
            ("reset_password", "/reset_password/"),
            ("password_reset_done", "/reset_password_sent/"),
            ("password_reset_complete", "/reset_password_complete/"),
        ],
    )
    def test_view_url_exists_at_desired_location_unauthenticated_user_200(
            self, name: str, location: str):
        """Test if page returns status code 200 for unauthorized user."""
        response_page = self.client.get(location)
        self.assertEqual(response_page.status_code, 200)

    @parameterized.expand(
        [
            ("index", ""),
            ("contact", "/contact/"),
            ("how-it-works", "/how-it-works/"),
            ("terms-conditions", "/terms-conditions/"),
            ("credentials", "/credentials/"),
            ("nav-payments", "/nav-payments/"),
            ("nav-planner", "/nav-planner/"),
            ("nav-medical", "/nav-medical/"),
            ("user-profile", "/user-profile/"),
            ("edit-account", "/edit-account/"),
            ("delete-user", "/delete-user/"),
            ("edit-access", "/edit-access/"),
            ("delete-access", "/delete-access/"),
        ],
    )
    def test_view_url_exists_at_desired_location_authenticated_user_200(
            self, name: str, location: str):
        """Test if page returns status code 200 for authorized user."""
        self.client.force_login(self.user)
        response_page = self.client.get(location)
        self.assertEqual(response_page.status_code, 200)
        self.assertEqual(str(response_page.context["user"]), "johndoe123")

    @parameterized.expand(
        [
            ("logout", "/logout/"),
            ("user-profile", "/user-profile/"),
            ("edit-account", "/edit-account/"),
            ("delete-user", "/delete-user/"),
            ("edit-access", "/edit-access/"),
            ("delete-access", "/delete-access/"),
        ],
    )
    def test_view_url_exists_at_desired_location_unauthenticated_user_302_redirect(
            self, name: str, location: str,):
        """Test if page is unavailable for unauthenticated users."""
        response_page = self.client.get(location)
        self.assertEqual(response_page.status_code, 302)

    @parameterized.expand(
        [
            ("login", "/login/"),
            ("register", "/register/"),
        ],
    )
    def test_view_url_exists_at_desired_location_authenticated_user_302_redirect(
            self, name: str, location: str):
        """Test if page is unavailable for authenticated users."""
        self.client.force_login(self.user)
        response_page = self.client.get(location)
        self.assertEqual(response_page.status_code, 302)

    @parameterized.expand(
        [
            ("index", "index"),
            ("contact", "contact"),
            ("how-it-works", "how-it-works"),
            ("terms-conditions", "terms-conditions"),
            ("credentials", "credentials"),
            ("nav-payments", "nav-payments"),
            ("nav-planner", "nav-planner"),
            ("nav-medical", "nav-medical"),
            ("login", "login"),
            ("register", "register"),
            ("reset_password", "reset_password"),
            ("password_reset_done", "password_reset_done"),
            ("password_reset_complete", "password_reset_complete"),
        ],
    )
    def test_view_url_accessible_by_name_unauthenticated_user_200(
            self, name: str, url: str):
        """Test if page is accessible by name - unauthenticated user,
        response status code: 200."""
        response_page = self.client.get(reverse(url))
        self.assertEqual(response_page.status_code, 200)

    @parameterized.expand(
        [
            ("index", "index"),
            ("contact", "contact"),
            ("how-it-works", "how-it-works"),
            ("terms-conditions", "terms-conditions"),
            ("credentials", "credentials"),
            ("nav-payments", "nav-payments"),
            ("nav-planner", "nav-planner"),
            ("nav-medical", "nav-medical"),
            ("reset_password", "reset_password"),
            ("password_reset_done", "password_reset_done"),
            ("password_reset_complete", "password_reset_complete"),
            # "logout",
            ("user-profile", "user-profile"),
            ("edit-account", "edit-account"),
            ("delete-user", "delete-user"),
            ("edit-access", "edit-access"),
            ("delete-access", "delete-access"),
        ],
    )
    def test_view_url_accessible_by_name_authenticated_user_200(
        self, name: str, url: str):
        """Test if page is accessible by name - authenticated user,
        response status code: 200."""
        self.client.force_login(self.user)
        response_page = self.client.get(reverse(url))
        self.assertEqual(response_page.status_code, 200)
        self.assertEqual(str(response_page.context["user"]), "johndoe123")

    @parameterized.expand(
        [
            ("logout", "logout"),
            ("user-profile", "user-profile"),
            ("edit-account", "edit-account"),
            ("delete-user", "delete-user"),
            ("edit-access", "edit-access"),
            ("delete-access", "delete-access"),
        ],
    )
    def test_view_url_accessible_by_name_unauthenticated_user_302_redirect(
            self, name: str, url: str):
        """Test if page is accessible by name - unauthenticated user,
        response redirect 302."""
        response_page = self.client.get(reverse(url))
        self.assertEqual(response_page.status_code, 302)

    @parameterized.expand(
        [
            ("login", "login"),
            ("register", "register"),
        ],
    )
    def test_view_url_accessible_by_name_authenticated_user_302_redirect(
            self, name: str, url: str):
        """Test if page is accessible by name - authenticated user,
        response 302 redirect."""
        self.client.force_login(self.user)
        response_page = self.client.get(reverse(url))
        self.assertEqual(response_page.status_code, 302)

    @parameterized.expand(
        [
            (False, "index", "index.html"),
            (False, "contact", "contact.html"),
            (False, "how-it-works", "how_it_works.html"),
            (False, "terms-conditions", "terms_conditions.html"),
            (False, "credentials", "credentials.html"),
            (False, "nav-payments", "nav_boxes.html"),
            (False, "nav-planner", "nav_boxes.html"),
            (False, "nav-medical", "nav_boxes.html"),
            (False, "login", "user/login_register.html"),
            (False, "register", "user/login_register.html"),
            (False, "reset_password", "reset_password.html"),
            (False, "password_reset_done", "reset_password_sent.html"),
            (False, "password_reset_complete", "reset_password_complete.html"),
            # "logout",
            (True, "user-profile", "user/user_profile.html"),
            (True, "edit-account", "user/profile_form.html"),
            (True, "delete-user", "user/delete_user.html"),
            (True, "edit-access", "user/manage_access.html"),
            (True, "delete-access", "user/manage_access.html"),
        ],
    )
    def test_view_uses_correct_template(
            self, authorised: bool, name: str, template: str):
        """Test if response returns correct page template."""
        if authorised:
            self.client.force_login(self.user)
        response = self.client.get(reverse(name))
        self.assertTemplateUsed(response, template)


class RegisterUserTests(TestCase):
    """Test register user views."""
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="johndoe123fortestpurposes",
            email="johndoe@example.com",
            password="testpass456",
        )
        self.profile = Profile.objects.get(username=self.user.username)
        self.profile.first_name = "John"
        self.profile.last_name = "Doe"
        self.profile.save()

        self.payload = {
            "username": "newusername123fortestpurposes",
            "email": "test@example.com",
            "password1": "testpass456",
            "password2": "testpass456",
            "terms_and_conditions": True,
            # "captcha": "",    # turned off
        }
        if os.path.exists(os.path.join(settings.MEDIA_ROOT,
                                       "johndoe123uploadfortestpurposes")):
            logger.critical("🛑  Tests on register page suspended due to the "
                            "potential conflict with user registered in database. "
                            "Username 'newusername123fortestpurposes' already in "
                            "database.")
            raise ValidationError("Cannot conduct test on register username "
                                  "because of conflict with already existing "
                                  "folder on server!", "critical")

    # def tearDown(self):
    #     path = os.path.join(settings.TEST_ROOT, "johndoe123uploadfortestpurposes")
    #     if os.path.exists(path):
    #         if os.path.isfile(path) or os.path.islink(path):
    #             os.unlink(path)
    #         else:
    #             shutil.rmtree(path)

    def test_user_and_profile_created(self):
        """Test if user account and profile account was created in setUp."""
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

    """@override_settings(CAPTCHA_TEST_MODE=False)"""

    def test_register_user_200(self):
        """Test if register_user page returns status code 200."""
        response_get = self.client.get(reverse("register"))
        self.assertEqual(response_get.status_code, 200)

    def test_register_user_correct_template(self):
        """Test if register_user page uses correct template."""
        response_get = self.client.get(reverse("register"))
        self.assertTemplateUsed(response_get, "user/login_register.html")

    def test_register_user_initial_values_set_context_data(self):
        """Test if register_user page displays correct context data."""
        response_get = self.client.get(reverse("register"))
        self.assertIsInstance(response_get.context["form"], CustomUserCreationForm)
        self.assertEqual(response_get.context["page"], "register")

    def test_register_user_form_initial_values_set_form_data(self):
        """Test if register_user page displays correct form data."""
        register_fields = ["username", "email", "password1", "password2",
                           "terms_and_conditions"]
        response_get = self.client.get(reverse("register"))
        for field in register_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zarejestruj użytkownika", response_get.content.decode())   # input type="submit"

    def test_register_user_success_and_redirect(self):
        """Test creating a user is successful and redirecting is successful."""
        response = self.client.get(reverse("register"))
        self.assertIn("username", response.content.decode())
        self.assertIn("Nazwa użytkownika", response.content.decode())
        self.assertNotIn("newusername123fortestpurposes", response.content.decode())

        response_post = self.client.post(reverse("register"), self.payload)
        self.assertEqual(response_post.status_code, 302)
        self.assertTemplateUsed(response_post, template_name="welcome_email.html")
        # signals >> AssertionError: False is not true :
        # Template 'user/login_register.html' was not a template used to render the response.
        # Actual template(s) used: welcome_email.txt, welcome_email.html

        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(User.objects.count(), 2)
        user = User.objects.get(email=self.payload["email"])
        self.assertTrue(user.check_password(self.payload["password1"]))

        response_redirect = self.client.get(reverse("user-profile"))
        assert response_redirect, "/user-profile/"
        self.assertInHTML("newusername123fortestpurposes",
                          response_redirect.content.decode())

        messages = list(response_redirect.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Utworzono użytkownika.", str(messages[0]))

    @parameterized.expand(
        [
            ("forbidden characters in username", "^&*()%$@$#",
             "Wprowadź poprawną nazwę użytkownika. Wartość może zawierać "
             "jedynie litery, cyfry i znaki @/./+/-/_."),
            ("too short username", "user",
             "Nazwa użytkownika musi się składać min. z 8 znaków."),
            ("not unique field", "johndoe123fortestpurposes",
             "Użytkownik o tej nazwie istnieje już w bazie danych. "
             "Wprowadź inną nazwę."),
            ("forbidden username", "forbidenusername",
             "Użytkownik o tej nazwie istnieje już w bazie danych. "
             "Wprowadź inną nazwę."),
        ],
    )
    def test_cant_register_with_invalid_username(
            self,
            name: str,
            invalid_username: str,
            error_msg: str,
    ):
        """Test if attempt to create a user with invalid username is forbidden
        and raises error messages."""

        payload = self.payload
        payload["username"] = invalid_username
        response_post = self.client.post(reverse("register"), payload)

        try:
            get_user_model().objects.get(username=payload["username"])
        except User.DoesNotExist:
            self.assertRaises(User.DoesNotExist)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response_post.status_code, 200)
        self.assertInHTML(error_msg, response_post.content.decode())

    @parameterized.expand(
        [
            ("email without @", "testexample.com", "Wprowadź poprawny adres email"),
            ("email without dot (.)", "test@examplecom",
             "Wprowadź poprawny adres email."),
            ("not unique field", "johndoe@example.com",
             "Istnieje już Użytkownik z tą wartością pola adres email."),
            ("empty field", "", "To pole jest wymagane."),
        ],
    )
    def test_cant_register_with_invalid_or_taken_email(
            self,
            name: str,
            invalid_email: str,
            error_msg: str,
    ):
        """Test if attempt to create a user with invalid email is forbidden
        and raises error messages."""
        payload = self.payload
        payload["email"] = invalid_email
        response_post = self.client.post(reverse("register"), payload)
        try:
            get_user_model().objects.get(username=payload["username"])
        except User.DoesNotExist:
            self.assertRaises(User.DoesNotExist)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response_post.status_code, 200)
        self.assertIn(error_msg, response_post.content.decode())

    @parameterized.expand(
        [
            ("password1 and password2 not match", "testpass123", "testpass456",
             "Hasła w obu polach nie są zgodne"),
            ("password contains only numbers", "1133557799", "1133557799",
             "Hasło składa się wyłącznie z cyfr"),
            ("password too common", "zaqwsxcde", "zaqwsxcde",
             "To hasło jest zbyt powszechne"),
            ("password too short (less than 8 characters)", "pass1", "pass1",
             "To hasło jest za krótkie. Musi zawierać co najmniej 8 znaków"),
            ("password too similar to username",
             "johndoe123fortestpurpose", "johndoe123fortestpurpose",
             "Hasło jest zbyt podobne do Nazwa użytkownika."),
        ],
    )
    def test_cant_register_with_invalid_password(
            self,
            name: str,
            password1: str,
            password2: str,
            error_msg: str,
    ):
        """Test if attempt to create a user with invalid password is forbidden
        and raises error messages."""
        payload = self.payload
        payload["password1"] = password1
        payload["password2"] = password2
        response_post = self.client.post(reverse("register"), payload)
        try:
            get_user_model().objects.get(username=payload["username"])
        except User.DoesNotExist:
            self.assertRaises(User.DoesNotExist)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response_post.status_code, 200)
        self.assertIn(error_msg, response_post.content.decode())


class LoginLogoutUserTest(TestCase):
    """Tests for login page and logout."""
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

    def test_user_and_profile_created(self):
        """Test if user account and profile account was created in setUp."""
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

    def test_login_user_200_if_not_logged_in(self):
        """Test if login_user page returns status code 200
        for unauthorized user."""
        response_get = self.client.get(reverse("login"))
        self.assertEqual(response_get.status_code, 200)

    def test_login_user_302_if_logged_in(self):
        """Test if login_user page returns status code 302 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("login"))
        self.assertEqual(response_get.status_code, 302)

    def test_login_user_correct_template(self):
        """Test if renovations page uses correct template."""
        response_get = self.client.get(reverse("login"))
        self.assertTemplateUsed(response_get, "user/login_register.html")

    def test_login_user_form_initial_values_set_form_data(self):
        """Test if login_user page displays correct form data."""
        login_fields = ["username", "password"]
        response_get = self.client.get(reverse("login"))
        for field in login_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zaloguj się", response_get.content.decode())   # input type="submit"

    def test_login_user_successful_and_redirect(self):
        """Test if user registered in database can log in (status code 200) and
        is redirect (status code 302)."""
        self.client.get(reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

        response_login_post = self.client.post(
            reverse("login"),
            {"username": "johndoe123", "password": "testpass456"},
            follow=True,
        )
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(response_login_post.status_code, 200)

        self.assertInHTML("johndoe@example.com",
                          response_login_post.content.decode())
        self.assertRedirects(
            response_login_post,
            reverse("user-profile"),
            status_code=302,
            target_status_code=200,
            msg_prefix="",
            fetch_redirect_response=True,
        )
        self.assertTemplateUsed(response_login_post, "user/user_profile.html")

    def test_login_error_invalid_username(self):
        """Test if user not registered in database cannot login."""
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertFalse(User.objects.filter(username="testuser123").exists())

        response_post = self.client.post(
            reverse("login"),
            {"username": "testuser123", "password": "testpass456"},
            follow=True,
        )
        self.assertEqual(response_post.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTemplateNotUsed(response_post, "user_profile.html")
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Brak użytkownika w bazie danych.", str(messages[0]))

    def test_login_error_invalid_password(self):
        """Test if user with wrong password cannot log in."""
        self.assertNotIn("_auth_user_id", self.client.session)

        response_post = self.client.post(
            reverse("login"),
            {"username": "johndoe123", "password": "wrong987"},
            follow=True,
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response_post.status_code, 200)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nieprawidłowe hasło.", str(messages[0]))
        self.assertTemplateNotUsed(response_post, "user_profile.html")

    def test_logout_user_and_redirect(self):
        """Test logout user successfully and redirect to login page"""
        self.assertNotIn("_auth_user_id", self.client.session)
        response_login_post = self.client.post(
            reverse("login"),
            {"username": "johndoe123", "password": "testpass456"},
            follow=True,
        )
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual("johndoe123", str(response_login_post.context["user"]))

        response_logout = self.client.post(reverse("logout"), follow=True)
        self.assertRedirects(
            response_logout,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        messages = list(response_logout.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Użytkownik został wylogowany.", str(messages[0]))


class ProfileAccountTests(TestCase):
    """Tests for user-profile page."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456",
        )
        self.profile = Profile.objects.get(username=self.user.username)
        self.profile.first_name = "John"
        self.profile.last_name = "Doe"
        self.profile.access_granted_to = "test@example.com"
        self.profile.save()

        self.test_user = User.objects.create_user(
            username="testuser123",
            email="another@example.com",
            password="testpass456",
        )
        self.test_profile = Profile.objects.get(username=self.test_user.username)
        self.test_profile.first_name = "Test"
        self.test_profile.last_name = "Surname"
        self.test_profile.access_granted_to = "someone@example.com"
        self.test_profile.save()

    def test_user_and_profile_created(self):
        """Test if user account and profile account was created in setUp."""
        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(User.objects.count(), 2)

    def test_user_profile_302_redirect_if_unauthorized(self):
        """ Test if user_profile page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(reverse("user-profile"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertRedirects(
            response_get,
            reverse("index"),
            status_code=302,
            target_status_code=200,
            msg_prefix="",
            fetch_redirect_response=True,
        )

    def test_user_profile_200_if_logged_in(self):
        """Test if user_profile page return status code 200 for
        authenticated user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("user-profile"))
        self.assertEqual(response_get.status_code, 200)

    def test_user_profile_correct_template_if_logged_in(self):
        """Test if user_profile page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("user-profile"))
        self.assertTemplateUsed(response_get, "user/user_profile.html")

    def test_user_profile_initial_values_set_context_data(self):
        """Test if user_profile page displays correct context data."""
        access_granted_from_list = Profile.objects.filter(
            access_granted_to=self.profile.email)
        access_granted_emails = []
        if access_granted_from_list:
            for access in access_granted_from_list:
                access_granted_emails.append(access.email)

        self.client.force_login(self.user)
        response_get = self.client.get(reverse("user-profile"))
        self.assertEqual(response_get.context["profile"], self.profile)
        self.assertEqual(response_get.context["access_granted_from"],
                         access_granted_emails)

    def test_user_profile_initial_values_set_user_data(self):
        """Test if user_profile page displays correct user data
        (only data of logged user)."""

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("user-profile"))

        self.assertIn(self.user.email, response_get.content.decode())
        self.assertNotIn(self.test_user.email, response_get.content.decode())
        self.assertIn(self.profile.first_name, response_get.content.decode())
        self.assertNotIn(self.test_profile.first_name, response_get.content.decode())
        self.assertIn(self.profile.access_granted_to, response_get.content.decode())
        self.assertNotIn(self.test_profile.access_granted_to, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("user-profile"))

        self.assertIn(self.test_user.email, response_get.content.decode())
        self.assertNotIn(self.user.email, response_get.content.decode())
        self.assertIn(self.test_profile.first_name, response_get.content.decode())
        self.assertNotIn(self.profile.first_name, response_get.content.decode())
        self.assertIn(self.test_profile.access_granted_to, response_get.content.decode())
        self.assertNotIn(self.profile.access_granted_to, response_get.content.decode())


class EditAccountTests(TestCase):
    """Tests for editing user's account data."""
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

        self.payload = {
            "username": "newusername123fortestpurposes",
            "email": "newuser@example.com",
            "first_name": "Jonathan",
            "last_name": "Smith",
            "phone_number": "123 445 778",
            "city": "Wrocław",
            "street": "Krakowska",
            "building_number": 11,
            "apartment_number": 11,
            "post_code": "50-000",
            "country": "PL",
            "access_granted_to": "jane@example.com",
        }

    def test_user_and_profile_created(self):
        """Test if user account and profile account was created in setUp."""
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

    def test_edit_account_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot edit account
        (user is redirected to login page)."""
        response = self.client.get(reverse("edit-account"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_account_200_if_logged_in(self):
        """Test if edit_account page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("edit-account"))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_account_correct_template_if_logged_in(self):
        """Test if edit_account page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("edit-account"))
        self.assertTemplateUsed(response_get, "user/profile_form.html")

    def test_edit_account_form_initial_values_set_context_data(self):
        """Test if edit_account page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("edit-account"))
        self.assertIsInstance(response_get.context["form"], ProfileForm)

    def test_edit_account_initial_values_set(self):
        """Test if edit_account page displays correct initial data."""
        self.client.login(username="johndoe123", password="testpass456")
        self.assertIn("_auth_user_id", self.client.session)
        response = self.client.get(reverse("edit-account"))
        self.assertEqual(str(response.context["user"]), "johndoe123")

        initial_values = {
            "username": "johndoe123",
            "email": "johndoe@example.com",
            "first_name": "John",
            "last_name": "Doe",
        }
        for key, value in initial_values.items():
            self.assertIn(value, response.content.decode(encoding="UTF-8"))

    def test_edit_account_success_and_redirect(self):
        """Test if updating a profile is successful (status code 200)
                and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        payload = self.payload
        payload["username"] = self.profile.username
        payload["email"] = self.profile.email
        self.assertNotEqual(self.profile.first_name, payload["first_name"])
        self.assertNotEqual(self.profile.access_granted_to,
                            payload["access_granted_to"])

        self.client.login(username="johndoe123", password="testpass456")
        response_post = self.client.post(
            reverse("edit-account"),
            payload,
            instance=self.profile,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("user-profile"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano dane.", str(messages[0]))

        response_get = self.client.get(reverse("user-profile"))
        for key, value in payload.items():
            if key == "country":
                continue
            self.assertInHTML(str(value), response_get.content.decode())

        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

    def test_edit_account_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "first_name": "Someone",
            "access_granted_to": "new@example.com",
        }
        response_patch = self.client.patch(
            reverse("edit-account"),
            data=payload,
            instance=self.profile,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = self.payload
        response_put = self.client.put(
            reverse("edit-account"),
            data=payload,
            instance=self.profile,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("edit-account"),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())


class AccessGrantedTests(TestCase):
    """Tests for editing and deleting access granted data."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456",
        )
        self.profile = Profile.objects.get(username=self.user.username)
        self.profile.first_name = "John"
        self.profile.last_name = "Doe"
        self.profile.access_granted_to = "test@example.com"
        self.profile.save()

        self.test_user = User.objects.create_user(
            username="testuser123",
            email="another@example.com",
            password="testpass456",
        )
        self.test_profile = Profile.objects.get(username=self.test_user.username)
        self.test_profile.first_name = "Test"
        self.test_profile.last_name = "Surname"
        self.test_profile.access_granted_to = "someone@example.com"
        self.test_profile.save()

    def test_user_and_profile_created(self):
        """Test if user account and profile account was created in setUp."""
        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(User.objects.count(), 2)

    def test_edit_access_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot edit access
        (user is redirected to login page)."""
        response = self.client.get(reverse("edit-access"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_access_200_if_logged_in(self):
        """Test if edit_access page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("edit-access"))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_access_correct_template_if_logged_in(self):
        """Test if edit_access page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("edit-access"))
        self.assertTemplateUsed(response_get, "user/manage_access.html")

    def test_edit_access_form_initial_values_set_context_data(self):
        """Test if edit_access page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("edit-access"))
        self.assertEqual(response_get.context["page"], "edit-access")
        self.assertEqual(response_get.context["access"], self.profile.access_granted_to)
        self.assertIsInstance(response_get.context["form"], AddAccessForm)

    def test_edit_access_form_initial_values_set_form_data(self):
        """Test if edit_access page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("edit-access"))
        self.assertIn(self.profile.access_granted_to, response_get.content.decode())

    def test_edit_access_success_and_redirect(self):
        """Test if updating the access is successful (status code 200)
        and redirecting is successful (status code 302)."""
        access_before_change = self.profile.access_granted_to
        payload = {"access_granted_to": "abcd@example.com"}
        self.assertEqual(self.profile.access_granted_to, access_before_change)
        self.assertNotEqual(self.profile.access_granted_to,
                            payload["access_granted_to"])

        self.client.force_login(self.user)

        # user-profile page display before change in access_granted_to
        response_get = self.client.get(reverse("user-profile"))
        self.assertIn(access_before_change, response_get.content.decode())

        # changes in access_granted_to
        response_post = self.client.post(
            reverse("edit-access"),
            data=payload,
            instance=self.profile,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("user-profile"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano dostęp do danych dla zewnętrznego "
                      "użytkownika.", str(messages[0]))
        self.profile.refresh_from_db()
        self.assertEqual(Profile.objects.count(), 2)
        self.assertNotEqual(self.profile.access_granted_to, access_before_change)
        self.assertEqual(self.profile.access_granted_to,
                         payload["access_granted_to"])

        # user-profile page display after change in access_granted_to
        response_get = self.client.get(reverse("user-profile"))
        self.assertIn(payload["access_granted_to"], response_get.content.decode())

    def test_edit_access_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {"access_granted_to": "abcd@example.com"}
        response_patch = self.client.patch(
            reverse("edit-access"),
            data=payload,
            instance=self.profile,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {"access_granted_to": "abcd@example.com"}
        response_put = self.client.put(
            reverse("edit-access"),
            data=payload,
            instance=self.profile,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("edit-access"),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_delete_access_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot delete access
        (user is redirected to login page)."""
        response = self.client.get(reverse("delete-access"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_access_200_if_logged_in(self):
        """Test if delete_access page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("delete-access"))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_access_correct_template_if_logged_in(self):
        """Test if delete_access page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("delete-access"))
        self.assertTemplateUsed(response_get, "user/manage_access.html")

    def test_delete_access_form_initial_values_set_context_data(self):
        """Test if delete_access page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("delete-access"))
        self.assertEqual(response_get.context["page"], "delete-access")
        self.assertEqual(response_get.context["access"],
                         self.profile.access_granted_to)

    def test_delete_access_form_initial_values_set_form_data(self):
        """Test if delete_access page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("delete-access"))
        self.assertIn(self.profile.access_granted_to,
                      response_get.content.decode())

    def test_delete_access_successful_and_redirect(self):
        """Deleting access is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(Profile.objects.count(), 2)
        self.profile.access_granted_to = "abcd@example.com"
        self.profile.save()
        self.assertEqual("abcd@example.com", self.profile.access_granted_to)

        self.client.login(username="johndoe123", password="testpass456")

        response_delete = self.client.post(
            reverse("delete-access"),
            instance=self.profile,
            content_type="text/html",
            follow=True,
        )
        self.assertEqual(response_delete.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(Profile.objects.count(), 2)
        self.assertIsNone(self.profile.access_granted_to)

        self.assertRedirects(
            response_delete,
            reverse("user-profile"),
            status_code=302,
            target_status_code=200,
            msg_prefix="",
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto dostęp do danych dla zewnętrznego użytkownika.",
                      str(messages[0]))

    def test_delete_access_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("delete-access"), follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.", response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("delete-access"), follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.", response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("delete-access"), follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.", response_delete.content.decode())


class DeleteUserTests(TestCase):
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

        self.test_user = User.objects.create_user(
            username="testuser123",
            email="another@example.com",
            password="testpass456",
        )
    #
    #     if not os.path.exists(settings.TEST_ROOT):
    #         os.mkdir(settings.TEST_ROOT)
    #
    # def tearDown(self):
    #     path = os.path.join(settings.TEST_ROOT, str(self.user.id))
    #     if os.path.exists(path):
    #         if os.path.isfile(path) or os.path.islink(path):
    #             os.unlink(path)
    #         else:
    #             shutil.rmtree(path)
    #     os.rmdir(settings.TEST_ROOT)

    def test_user_and_profile_created(self):
        """Test if user account and profile account was created in setUp."""
        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(User.objects.count(), 2)

    def test_delete_user_302_redirect_if_unauthorized(self):
        """Test if delete_user page is unavailable for unauthorized users."""
        response = self.client.get(reverse("delete-user"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_user_200_if_logged_in(self):
        """Test if delete_user page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("delete-user"))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_user_correct_template_if_logged_in(self):
        """Test if delete_user page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("delete-user"))
        self.assertTemplateUsed(response_get, "user/delete_user.html")

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_delete_user_successful_and_redirect(self):
        """Deleting user is successful (status code 200) and redirect
        is successful (status code 302)."""
        credit_directory = str(self.user.id) + "_credit"
        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, credit_directory)):
            os.mkdir(os.path.join(settings.MEDIA_ROOT, credit_directory))
        credit_file_path = os.path.join(settings.MEDIA_ROOT, credit_directory, "credit_temp2.txt")
        if os.path.exists(credit_file_path):
            os.remove(credit_file_path)
            open(credit_file_path, "x").close()
        with open(credit_file_path, "w+") as file:
            file.write("TEST CREDIT FILES")

        self.assertTrue(os.path.exists(credit_file_path))
        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(User.objects.count(), 2)

        self.client.login(username="johndoe123", password="testpass456")
        response = self.client.get(reverse("delete-user"))
        self.assertEqual(str(response.context["user"]), "johndoe123")
        self.assertIn("johndoe123", response.content.decode())

        response_delete = self.client.post(
            reverse("delete-user"),
            data={"username": "johndoe123", "password": "testpass456"},
            content_type="text/html",
            follow=True,
        )
        self.assertEqual(response_delete.status_code, 200)
        self.assertFalse(os.path.exists(credit_file_path))
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 1)

        self.assertRedirects(
            response_delete,
            reverse("index"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Użytkownik został usunięty.", str(messages[0]))

        response = self.client.get(reverse("delete-user"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    # @override_settings(MEDIA_ROOT=settings.TEST_ROOT)  # does not work on test root (invalid request method (required: POST))
    def test_delete_user_and_files(self):
        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(User.objects.count(), 2)
        user = User.objects.create_user(
            username="johndoe123uploadfortestpurposesforbidden",
            email="uploadtest@example.com",
            password="testpass456",
        )
        self.assertEqual(Profile.objects.count(), 3)
        self.assertEqual(User.objects.count(), 3)

        # If tests on MEDIA_ROOT:
        #     Make sure that no user with the same username as test username
        #     has folder with files on server
        #     (override_settings breaks test)
        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, str(user.id))):
            os.mkdir(os.path.join(settings.MEDIA_ROOT, str(user.id)))
        else:
            logger.critical("Unable to conduct test_delete_user_and_files "
                            "due to conflict with real folder on server - "
                            "folder on server has the same name (user id) "
                            "as folder for tests. Cannot delete user's real directory!")
            raise ValidationError(
                "Cannot conduct test on self.user because of conflict "
                "with already existing folder on server with user's id!",
                "critical")

        path = os.path.join(settings.MEDIA_ROOT, str(user.id))    # test on real server
        if os.path.exists(path):
            pass
        else:
            os.mkdir(path)

        # If tests on @override_settings(MEDIA_ROOT=settings.TEST_ROOT):
        # # For testing file attachment
        # if not os.path.exists(settings.TEST_ROOT):
        #     os.mkdir(settings.TEST_ROOT)
        # path = os.path.join(settings.TEST_ROOT, str(user.id))
        # if not os.path.exists(path):
        #     os.mkdir(path)

        canvas = Canvas(path + "/setup1.pdf")
        canvas.drawString(72, 22, "setup = 'setup file'")
        canvas.save()
        attachment_file = os.path.basename(os.path.join(path, "setup1.pdf"))

        self.attachment = AttachmentFactory(
            user=self.user, attachment_name="setup attachment",
            attachment_path=attachment_file)

        self.client.login(username="johndoe123uploadfortestpurposesforbidden",
                          password="testpass456")
        response_delete = self.client.post(
            reverse("delete-user"),
            data={"username": "johndoe123uploadfortestpurposesforbidden",
                  "password": "testpass456"},
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("index"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 2)
        self.assertIn("Usunięto wszystkie pliki użytkownika.", str(messages[0]))
        self.assertIn("Użytkownik został usunięty.", str(messages[1]))

        self.assertFalse(os.path.exists(path))

        self.assertEqual(response_delete.status_code, 200)
        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(User.objects.count(), 2)

        if os.path.exists(path):
            logger.error("🛑 Attempt to delete users file path was unsuccessful. "
                         "Test os path still exists! "
                         "Verify: test_delete_user_and_files.")
            os.rmdir(path)
            shutil.rmtree(path)

    def test_delete_user_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("delete-user"), follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("delete-user"), follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("delete-user"), follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())
