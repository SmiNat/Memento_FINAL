import logging
import shutil
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse
from reportlab.pdfgen.canvas import Canvas
from parameterized import parameterized
from unittest.mock import MagicMock

from access.enums import Access
from connection.factories import CounterpartyFactory, AttachmentFactory
from connection.models import Counterparty, Attachment
from payment.factories import PaymentFactory
from payment.models import Payment
from trip.factories import TripFactory
from trip.models import Trip
from renovation.factories import RenovationFactory
from renovation.models import Renovation
from credit.factories import CreditFactory
from credit.models import Credit
from connection.forms import CounterpartyForm, AttachmentForm
from medical.factories import MedicalVisitFactory, HealthTestResultFactory
from medical.models import MedicalVisit, HealthTestResult

logger = logging.getLogger("test")
User = get_user_model()


class BasicUrlsTests(TestCase):
    """Test Attachment and Counterparty basic urls."""
    # NOTE: Tests without download-attachment (problem with upload file path -
    # additional folder with users id causes FileNotFoundError)!

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.counterparty = Counterparty.objects.create(
            user=self.user, name="setup cp")
        self.attachment = Attachment.objects.create(
            user=self.user, attachment_name="setup attachment")

        # For testing attachments in form of .pdf file
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)
        path_temporary = os.path.join(settings.TEST_ROOT, str("temporary"))
        if not os.path.exists(path_temporary):
            os.mkdir(path_temporary)
        if not os.path.exists(
                os.path.join(path_temporary, str("temporary.pdf"))):
            canvas = Canvas(path_temporary + "/temporary.pdf")
            canvas.drawString(72, 22, "setup = 'temporary file'")
            canvas.save()
        path_user = os.path.join(path_temporary, str("temporary.pdf"))

        self.attachment.attachment_path = path_user
        self.attachment.save()

        self.pages = [
            {"page": "connection:counterparties",
             "args": [], "name": "counterparties",
             "template": "counterparty/counterparties.html"},
            {"page": "connection:single-counterparty",
             "args": [str(self.counterparty.id)], "name": "single-counterparty",
             "template": "counterparty/single_counterparty.html"},
            {"page": "connection:add-counterparty",
             "args": [], "name": "add-counterparty",
             "template": "counterparty/counterparty_form.html"},
            {"page": "connection:edit-counterparty",
             "args": [str(self.counterparty.id)], "name": "edit-counterparty",
             "template": "counterparty/counterparty_form.html"},
            {"page": "connection:delete-counterparty",
             "args": [str(self.counterparty.id)],
             "name": "delete-counterparty",
             "template": "counterparty/counterparty_delete_form.html"},

            {"page": "connection:attachments",
             "args": [], "name": "attachments",
             "template": "attachment/attachments.html"},
            {"page": "connection:add-attachment",
             "args": [], "name": "add-attachment",
             "template": "attachment/attachment_form.html"},
            {"page": "connection:delete-attachment",
             "args": [str(self.attachment.id)], "name": 'delete-attachment',
             "template": "attachment/attachment_delete_form.html"},

            {"page": "connection:download-attachment",
             "args": [str(self.attachment.user.profile.slug),
                      str(self.attachment.id)],
             "name": "download-attachment", "template": ""},
        ]

    def tearDown(self):
        path = os.path.join(settings.TEST_ROOT, str(self.user.id))
        if os.path.exists(path):
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            else:
                shutil.rmtree(path)
        # os.rmdir(settings.TEST_ROOT)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_url_status_code_302_for_unauthenticated_user(self):
        """Test if user is redirected to login page if unauthorised."""
        for page in self.pages:
            url = reverse(page["page"], args=page["args"])
            response_page = self.client.get(url)
            self.assertEqual(response_page.status_code, 302)
            self.assertIn("login", response_page.url)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_url_status_code_200_for_authenticated_user(self):
        """Test if view url exists at desired location for authenticated user."""
        self.client.force_login(self.user)
        for page in self.pages:
            url = reverse(page["page"], args=page["args"])
            response_page = self.client.get(url)
            self.assertEqual(response_page.status_code, 200)
            self.assertIn("_auth_user_id", self.client.session)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_uses_correct_template(self):
        """Test if response returns correct page template."""

        # Test for authenticated user
        self.client.force_login(self.user)
        for page in self.pages:
            if page["page"] == "connection:download-attachment":
                continue
            response = self.client.get(
                reverse(page["page"], args=page["args"]))
            self.assertTemplateUsed(response, page["template"])


class CounterpartyTests(TestCase):
    """Test Counterparty views."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.counterparty = CounterpartyFactory(
            user=self.user, name="setup cp", address="setup address")
        self.payment = PaymentFactory(user=self.user, name="setup payment")
        self.trip = TripFactory(user=self.user, name="setup trip")
        self.renovation = RenovationFactory(
            user=self.user, name="setup renovation",)
        self.credit = CreditFactory(user=self.user, name="setup credit")
        self.payment.counterparties = self.counterparty
        self.payment.save()
        self.counterparty.trips.add(self.trip)
        self.counterparty.renovations.add(self.renovation)
        self.counterparty.credits.add(self.credit)

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com", password="testpass456")
        self.test_counterparty = CounterpartyFactory(
            user=self.test_user, name="test cp", address="test address")
        self.test_payment = PaymentFactory(
            user=self.test_user, name="test payment")
        self.test_trip = TripFactory(user=self.test_user, name="test trip")
        self.test_renovation = RenovationFactory(
            user=self.test_user, name="test renovation")
        self.test_credit = CreditFactory(
            user=self.test_user, name="test credit")
        self.test_payment.counterparty = self.test_counterparty
        self.test_payment.save()

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Payment.objects.count(), 2)
        self.assertEqual(Counterparty.objects.count(), 2)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 2)
        self.assertEqual(Renovation.objects.count(), 2)

    def test_counterparties_302_redirect_if_unauthorized(self):
        """Test if counterparties page is unavailable for unauthorized users."""
        response = self.client.get(reverse("connection:counterparties"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_counterparties_200_if_logged_in(self):
        """Test if counterparties page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:counterparties"))
        self.assertEqual(response_get.status_code, 200)

    def test_counterparties_correct_template_if_logged_in(self):
        """Test if counterparties page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:counterparties"))
        self.assertTemplateUsed(response_get, "counterparty/counterparties.html")

    def test_counterparties_initial_values_set_context_data(self):
        """Test if counterparties page displays correct context data."""
        counterparties = Counterparty.objects.filter(
            user=self.user).order_by("-updated")
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("connection:counterparties"))
        self.assertQuerysetEqual(response_get.context["cps"], counterparties)

    def test_counterparties_initial_values_set_counterparties_data(self):
        """Test if page counterparties displays only counterparties of logged user
        (without counterparties of other users)."""
        user_second_cp = CounterpartyFactory(user=self.user, name="new cp")

        # Test for user "johndoe123"
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:counterparties"))

        self.assertIn(self.counterparty.name, response_get.content.decode())
        self.assertIn(user_second_cp.name, response_get.content.decode())
        self.assertNotIn(self.test_counterparty.name, response_get.content.decode())

        self.client.logout()

        # Test for user "testuser123"
        self.client.login(username="testuser123", password="testpass456")
        response_get = self.client.get(reverse("connection:counterparties"))

        self.assertNotIn(self.counterparty.name, response_get.content.decode())
        self.assertNotIn(user_second_cp.name, response_get.content.decode())
        self.assertIn(self.test_counterparty.name, response_get.content.decode())

    def test_single_counterparty_302_redirect_if_unauthorized(self):
        """ Test if single_counterparty page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("connection:single-counterparty", args=[self.counterparty.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    def test_single_counterparty_200_if_logged_in(self):
        """Test if single_counterparty page return status code 200 for
        authenticated user."""
        self.client.login(username="johndoe123", password="testpass456")

        response_get = self.client.get(
            reverse("connection:single-counterparty", args=[self.counterparty.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_single_counterparty_correct_template_if_logged_in(self):
        """Test if single_counterparty page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("connection:single-counterparty", args=[self.counterparty.id]))
        self.assertTemplateUsed(
            response_get, "counterparty/single_counterparty.html")

    def test_single_counterparty_initial_values_set_context_data(self):
        """Test if single_counterparty page displays correct context data."""
        attachments = Attachment.objects.filter(counterparties=self.counterparty.id)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("connection:single-counterparty",
                    args=[str(self.counterparty.id)]))
        self.assertQuerysetEqual(response_get.context["attachments"],
                                 attachments)
        self.assertEqual(response_get.context["cp"], self.counterparty)
        self.assertEqual(response_get.context["profile"],
                         self.counterparty.user.profile)

    def test_single_counterparty_initial_values_set_single_counterparty_data(self):
        """Test if single_counterparty page displays correct data
        (only data of logged user)."""
        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("connection:single-counterparty", args=[self.counterparty.id]))

        self.assertIn(self.counterparty.name, response_get.content.decode())
        self.assertNotIn(self.test_counterparty.name,
                         response_get.content.decode())
        self.assertIn(self.counterparty.address,
                      response_get.content.decode())
        self.assertNotIn(self.test_counterparty.address,
                         response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("connection:single-counterparty",
                    args=[self.test_counterparty.id]))

        self.assertIn(self.test_counterparty.name,
                      response_get.content.decode())
        self.assertNotIn(self.counterparty.name,
                         response_get.content.decode())
        self.assertIn(self.test_counterparty.address,
                      response_get.content.decode())
        self.assertNotIn(self.counterparty.address,
                         response_get.content.decode())

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_single_counterparty_initial_values_set_attachments(self):
        """Test if single counterparty page displays correct attachments
        (only data of logged user)."""

        # For testing file attachment
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)
        path_temporary = os.path.join(settings.TEST_ROOT, str("temporary"))
        if not os.path.exists(path_temporary):
            os.mkdir(path_temporary)
        if not os.path.exists(
                os.path.join(path_temporary, str("temporary.pdf"))):
            canvas = Canvas(path_temporary + "/temporary.pdf")
            canvas.drawString(72, 22, "setup = 'temporary file'")
            canvas.save()
        if not os.path.exists(
                os.path.join(path_temporary, str("test_temporary.pdf"))):
            canvas = Canvas(path_temporary + "/test_temporary.pdf")
            canvas.drawString(72, 22, "TEST = 'temporary file'")
            canvas.save()
        path_user = os.path.join(path_temporary, str("temporary.pdf"))
        path_test_user = os.path.join(path_temporary,
                                      str("test_temporary.pdf"))

        self.attachment = AttachmentFactory(
            user=self.user, attachment_name="setup attachment",
            attachment_path=path_user)
        self.test_attachment = AttachmentFactory(
            user=self.test_user, attachment_name="test attachment",
            attachment_path=path_test_user)
        self.attachment.counterparties.add(self.counterparty)
        self.test_attachment.counterparties.add(self.test_counterparty)

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("connection:single-counterparty",
                    args=[self.counterparty.id]))
        counterparty_id = response_get.request["PATH_INFO"].split("/")[-2]
        self.assertQuerysetEqual(self.counterparty,
                                 Counterparty.objects.get(id=counterparty_id))
        self.assertIn(self.counterparty.name, response_get.content.decode())
        self.assertNotIn(self.test_counterparty.name,
                         response_get.content.decode())
        self.assertIn(self.attachment.attachment_name,
                      response_get.content.decode())
        self.assertNotIn(self.test_attachment.attachment_name,
                         response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("connection:single-counterparty",
                    args=[self.test_counterparty.id]))

        self.assertIn(self.test_counterparty.name, response_get.content.decode())
        self.assertNotIn(self.counterparty.name, response_get.content.decode())
        self.assertIn(self.test_attachment.attachment_name,
                      response_get.content.decode())
        self.assertNotIn(self.attachment.attachment_name,
                         response_get.content.decode())

        users = [str(self.user.id), str(self.test_user.id)]
        for user in users:
            path = os.path.join(settings.TEST_ROOT, user)
            if os.path.exists(path):
                if os.path.isfile(path) or os.path.islink(path):
                    os.unlink(path)
                else:
                    shutil.rmtree(path)
        # os.rmdir(settings.TEST_ROOT)

    def test_single_counterparty_forced_logout_if_security_breach(self):
        """Attempt to overview counterparty of another user is forbidden and
        triggers logout."""

        # Attempt to see self.test_user data by self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("connection:single-counterparty",
                    args=[self.test_counterparty.id]), follow=True)
        self.assertIn(self.test_counterparty.name,
                      response_get.content.decode())
        self.client.logout()

        # Attempt to see self.test_user data by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("connection:single-counterparty",
                    args=[self.test_counterparty.id]), follow=True)
        self.assertNotIn(self.test_counterparty.name,
                         response_get.content.decode())
        self.assertRedirects(
            response_get,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_get.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do przeglądania tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

    def test_add_counterparty_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add counterparty
        (user is redirected to login page)."""
        response = self.client.get(reverse("connection:add-counterparty"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_counterparties_200_if_logged_in(self):
        """Test if add_counterparties page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:add-counterparty"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_counterparty_correct_template_if_logged_in(self):
        """Test if add_counterparty page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:add-counterparty"))
        self.assertTemplateUsed(response_get,
                                "counterparty/counterparty_form.html")

    def test_add_counterparty_form_initial_values_set_context_data(self):
        """Test if add_counterparty page displays correct context data."""
        cp_names = list(
            Counterparty.objects.filter(
                user=self.user).values_list("name", flat=True))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:add-counterparty"))
        self.assertEqual(response_get.context["page"], "add-counterparty")
        self.assertQuerysetEqual(response_get.context["cp_names"], cp_names)
        self.assertIsInstance(response_get.context["form"], CounterpartyForm)

    def test_add_counterparty_form_initial_values_set_form_data(self):
        """Test if add_counterparty page displays correct form data."""
        counterparty_fields = ["payments", "credits", "renovations", "trips",
                               "name", "phone_number", "email", "address",
                               "www", "bank_account", "app", "client_number",
                               "primary_contact_name",
                               "primary_contact_phone_number",
                               "primary_contact_email", "secondary_contact_name",
                               "secondary_contact_phone_number",
                               "secondary_contact_email", "notes",
                               "access_granted"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:add-counterparty"))
        for field in counterparty_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_counterparty_form_has_only_single_user_data_in_queryset_fields(self):
        """Test if add/edit form does not contain other user's data."""
        PaymentFactory(user=self.test_user, name="New test")
        CreditFactory(user=self.test_user, name="New test")
        RenovationFactory(user=self.test_user, name="New test")
        TripFactory(user=self.test_user, name="New test")

        # Test on user_setup
        self.client.force_login(self.user)
        cp_names = []
        form = CounterpartyForm(cp_names=cp_names)
        form.fields["payments"].queryset = Payment.objects.filter(user=self.user)
        form.fields["credits"].queryset = Credit.objects.filter(user=self.user)
        form.fields["renovations"].queryset = Renovation.objects.filter(user=self.user)
        form.fields["trips"].queryset = Trip.objects.filter(user=self.user)
        payment_choices_in_form_field = (list(field[1] for field in
                                              form.fields["payments"].choices))
        credit_choices_in_form_field = (list(field[1] for field in
                                             form.fields["credits"].choices))
        renovation_choices_in_form_field = (list(field[1] for field in
                                                 form.fields["renovations"].choices))
        trip_choices_in_form_field = (list(field[1] for field in
                                           form.fields["trips"].choices))

        self.assertIn(self.payment.name, payment_choices_in_form_field)
        self.assertNotIn(self.test_payment.name, payment_choices_in_form_field)
        self.assertEqual(len(payment_choices_in_form_field), 1)
        self.assertIn(self.credit.name, credit_choices_in_form_field)
        self.assertNotIn(self.test_credit.name, credit_choices_in_form_field)
        self.assertEqual(len(credit_choices_in_form_field), 1)
        self.assertIn(self.renovation.name, renovation_choices_in_form_field)
        self.assertNotIn(self.test_renovation.name, renovation_choices_in_form_field)
        self.assertEqual(len(renovation_choices_in_form_field), 1)
        self.assertIn(self.trip.name, trip_choices_in_form_field)
        self.assertNotIn(self.test_trip.name, trip_choices_in_form_field)
        self.assertEqual(len(trip_choices_in_form_field), 1)

        # Test on user_test
        self.client.force_login(self.test_user)
        cp_names = []
        form = CounterpartyForm(cp_names=cp_names)
        form.fields["payments"].queryset = Payment.objects.filter(user=self.test_user)
        form.fields["credits"].queryset = Credit.objects.filter(user=self.test_user)
        form.fields["renovations"].queryset = Renovation.objects.filter(user=self.test_user)
        form.fields["trips"].queryset = Trip.objects.filter(user=self.test_user)
        payment_choices_in_form_field = (list(field[1] for field in
                                              form.fields["payments"].choices))
        credit_choices_in_form_field = (list(field[1] for field in
                                             form.fields["credits"].choices))
        renovation_choices_in_form_field = (list(field[1] for field in
                                                 form.fields["renovations"].choices))
        trip_choices_in_form_field = (list(field[1] for field in
                                           form.fields["trips"].choices))
        self.assertIn(self.test_payment.name, payment_choices_in_form_field)
        self.assertNotIn(self.payment.name, payment_choices_in_form_field)
        self.assertEqual(len(payment_choices_in_form_field), 2)
        self.assertIn(self.test_credit.name, credit_choices_in_form_field)
        self.assertNotIn(self.credit.name, credit_choices_in_form_field)
        self.assertEqual(len(credit_choices_in_form_field), 2)
        self.assertIn(self.test_renovation.name, renovation_choices_in_form_field)
        self.assertNotIn(self.renovation.name, renovation_choices_in_form_field)
        self.assertEqual(len(renovation_choices_in_form_field), 2)
        self.assertIn(self.test_trip.name, trip_choices_in_form_field)
        self.assertNotIn(self.trip.name, trip_choices_in_form_field)
        self.assertEqual(len(trip_choices_in_form_field), 2)

    def test_add_counterparty_success_and_redirect(self):
        """Test if creating a counterparty is successful (status code 200) and
        redirecting is successful (status code 302)."""
        payload = {
            "name": "New counterparty name",
            "email": "add@example.com",
            "access_granted": Access.NO_ACCESS_GRANTED
        }
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "connection:add-counterparty"),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("connection:counterparties"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano kontrahenta.",
                      str(messages[0]))
        self.assertInHTML("New counterparty name",
                          response_post.content.decode())
        self.assertEqual(Counterparty.objects.count(), 3)
        self.assertTrue(Counterparty.objects.filter(
            user=self.user, email=payload["email"]).exists())

    @parameterized.expand(
        [
            ("Empty field: name",
             {"access_granted": "Brak dostępu"},
             "To pole jest wymagane."),
            ("Empty field: access_granted",
             {"name": "Brak dostępu"},
             "To pole jest wymagane."),
            ("Not unique field: name",
             {"name": "setup cp", "access_granted": "Brak dostępu"},
             "Istnieje już kontrahent o podanej nazwie w bazie danych."),
            ("Incorrect email field",
             {"name": "New cp", "access_granted": "Brak dostępu",
              "email": "ma$t&@examplecom"},
             "Wprowadź poprawny adres email."),
            ("Incorrect url field",
             {"name": "New cp", "access_granted": "Brak dostępu",
              "www": "youtube"},
             "Wpisz poprawny URL."),
            ("Incorrect bank_account field",
             {"name": "New cp", "access_granted": "Brak dostępu",
              "bank_account": "SOME 1234"},
             "Wpisz poprawną wartość."),
        ]
    )
    def test_add_counterparty_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a counterparty is not successful if data is incorrect."""
        self.client.force_login(self.user)
        cp_names = ["setup cp"]
        response_post = self.client.post(
            reverse("connection:add-counterparty"), payload, cp_names=cp_names)
        self.assertEqual(Counterparty.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_counterparty_302_redirect_if_unauthorized(self):
        """Test if edit_counterparty page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("connection:edit-counterparty", args=[self.counterparty.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_counterparty_200_if_logged_in(self):
        """Test if edit_counterparty page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("connection:edit-counterparty", args=[self.counterparty.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_counterparty_correct_template_if_logged_in(self):
        """Test if edit_counterparty page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("connection:edit-counterparty", args=[self.counterparty.id]))
        self.assertTemplateUsed(response_get, "counterparty/counterparty_form.html")

    def test_edit_counterparty_form_initial_values_set_context_data(self):
        """Test if edit_counterparty page displays correct context data."""
        cp_names = list(Counterparty.objects.filter(
            user=self.user).exclude(
            id=self.counterparty.id).values_list("name", flat=True))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("connection:edit-counterparty", args=[str(self.counterparty.id)]))
        self.assertEqual(response_get.context["page"], "edit-counterparty")
        self.assertEqual(response_get.context["cp"], self.counterparty)
        self.assertQuerysetEqual(response_get.context["cp_names"], cp_names)
        self.assertIsInstance(response_get.context["form"], CounterpartyForm)

    def test_edit_counterparty_form_initial_values_set_form_data(self):
        """Test if edit_counterparty page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("connection:edit-counterparty",
                    args=[str(self.counterparty.id)]))

        self.assertIn(self.counterparty.email, response_get.content.decode())
        self.assertIn(self.counterparty.name, response_get.content.decode())

    def test_edit_counterparty_success_and_redirect(self):
        """Test if updating a counterparty is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        counterparty = self.counterparty
        cp_names = list(Counterparty.objects.filter(
            user=self.user).exclude(
            id=counterparty.id).values_list("name", flat=True))

        payload = {
            "name": counterparty.name,
            "phone_number": counterparty.phone_number,
            "email": "crazy@example.com",
            "address": counterparty.address,
            "www": counterparty.www,
            "bank_account": counterparty.bank_account,
            "client_number": counterparty.client_number,
            "access_granted": Access.NO_ACCESS_GRANTED
        }
        self.assertNotEqual(counterparty.email, payload["email"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("connection:edit-counterparty",
                    args=[str(self.counterparty.id)]),
            data=payload,
            instance=counterparty,
            cp_names=cp_names,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("connection:single-counterparty", args=[str(counterparty.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dane kontrahenta zostały zaktualizowane.", str(messages[0]))
        counterparty.refresh_from_db()
        self.assertEqual(Counterparty.objects.count(), 2)
        self.assertEqual(counterparty.email, payload["email"])

    def test_edit_counterparty_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        counterparty = self.counterparty
        cp_names = list(Counterparty.objects.filter(
            user=self.user).exclude(
            id=counterparty.id).values_list("name", flat=True))
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "New name as update",
            "access_granted": Access.NO_ACCESS_GRANTED
        }
        response_patch = self.client.patch(
            reverse("connection:edit-counterparty",
                    args=[str(self.counterparty.id)]),
            data=payload,
            instance=counterparty,
            cp_names=cp_names,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "name": "New name as update",
            "phone_number": counterparty.phone_number,
            "email": counterparty.email,
            "address": counterparty.address,
            "www": counterparty.www,
            "bank_account": counterparty.bank_account,
            "client_number": counterparty.client_number,
            "access_granted": Access.NO_ACCESS_GRANTED
        }
        response_put = self.client.put(
            reverse("connection:edit-counterparty",
                    args=[str(self.counterparty.id)]),
            data=payload,
            instance=counterparty,
            cp_names=cp_names,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("connection:edit-counterparty",
                    args=[str(self.counterparty.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_counterparty_logout_if_security_breach(self):
        """Editing counterparty of another user is unsuccessful and triggers logout."""
        test_counterparty = self.test_counterparty
        cp_names = list(Counterparty.objects.filter(
            user=self.user).exclude(
            id=test_counterparty.id).values_list("name", flat=True))

        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_counterparty.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "phone_number": "666 666 666",
            "email": "security_breach@example.com",
            "address": "Security breach",
            "www": test_counterparty.www,
            "bank_account": test_counterparty.bank_account,
            "client_number": "Security breach",
            "access_granted": Access.NO_ACCESS_GRANTED
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("connection:edit-counterparty",
                    args=[str(self.test_counterparty.id)]),
            data=payload,
            content_type="text/html",
            cp_names=cp_names,
            follow=True,
        )
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(Counterparty.objects.count(), 2)
        self.assertNotIn(test_counterparty.name, payload["name"])

    def test_delete_counterparty_302_redirect_if_unauthorized(self):
        """Test if delete_counterparty page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("connection:delete-counterparty",
                    args=[self.counterparty.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_counterparty_200_if_logged_in(self):
        """Test if delete_counterparty page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("connection:delete-counterparty",
                    args=[self.counterparty.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_counterparty_correct_template_if_logged_in(self):
        """Test if delete_counterparty page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("connection:delete-counterparty",
                    args=[self.counterparty.id]))
        self.assertTemplateUsed(response_get,
                                "counterparty/counterparty_delete_form.html")

    def test_delete_counterparty_initial_values_set_context_data(self):
        """Test if delete_counterparty page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("connection:delete-counterparty",
                    args=[str(self.counterparty.id)]))
        self.assertIn(str(self.counterparty), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-counterparty")
        self.assertEqual(response_get.context["counterparty"], self.counterparty)

    def test_delete_counterparty_successful_and_redirect(self):
        """Deleting counterparty is successful (status code 200) and redirect
        is successful (status code 302)."""
        counterparty = self.counterparty
        self.assertEqual(Counterparty.objects.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(reverse("connection:counterparties"))
        self.assertIn(str(counterparty), response.content.decode())

        response_delete = self.client.post(
            reverse("connection:delete-counterparty",
                    args=[str(self.counterparty.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("connection:counterparties"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto kontrahenta.", str(messages[0]))

        response = self.client.get(reverse("connection:counterparties"))
        self.assertEqual(Counterparty.objects.count(), 1)
        self.assertNotIn(self.counterparty.name, response.content.decode())
        self.assertNotIn(self.test_counterparty.name, response.content.decode())

    def test_delete_counterparty_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("connection:delete-counterparty",
                    args=[str(self.counterparty.id)]),
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("connection:delete-counterparty",
                    args=[str(self.counterparty.id)]),
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("connection:delete-counterparty",
                    args=[str(self.counterparty.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_counterparty_logout_if_security_breach(self):
        """Deleting counterparty of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(Counterparty.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_counterparty.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("connection:delete-counterparty",
                    args=[str(self.test_counterparty.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do usunięcia tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(Counterparty.objects.count(), 2)


class AttachmentTests(TestCase):
    """Test Attachment views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com",
            password="testpass456")

        self.attachment = Attachment.objects.create(
            user=self.user, attachment_name="setup attachment",)
        self.test_attachment = Attachment.objects.create(
            user=self.test_user, attachment_name="test attachment",)

        # For testing file attachment
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)
        path_temporary = os.path.join(settings.TEST_ROOT, str("temporary"))
        if not os.path.exists(path_temporary):
            os.mkdir(path_temporary)
        if not os.path.exists(
                os.path.join(path_temporary, str("temporary.pdf"))):
            canvas = Canvas(path_temporary + "/temporary.pdf")
            canvas.drawString(72, 22, "setup = 'temporary file'")
            canvas.save()
        if not os.path.exists(
                os.path.join(path_temporary, str("test_temporary.pdf"))):
            canvas = Canvas(path_temporary + "/test_temporary.pdf")
            canvas.drawString(72, 22, "TEST = 'temporary file'")
            canvas.save()
        path_user = os.path.join(path_temporary, str("temporary.pdf"))
        path_test_user = os.path.join(path_temporary, str("test_temporary.pdf"))

        self.attachment.attachment_path = path_user
        self.attachment.save()
        self.test_attachment.attachment_path = path_test_user
        self.test_attachment.save()

        self.attachment.refresh_from_db()

        self.counterparty = CounterpartyFactory(user=self.user)
        self.payment = PaymentFactory(user=self.user)
        self.trip = TripFactory(user=self.user)
        self.renovation = RenovationFactory(user=self.user)
        self.credit = CreditFactory(user=self.user)
        self.health_result = HealthTestResultFactory(user=self.user)
        self.medical = MedicalVisitFactory(user=self.user)

        self.attachment_fields = [
            "payments",
            "counterparties",
            "credits",
            "renovations",
            "trips",
            "health_results",
            "medical_visits",
            "attachment_name",
            "attachment_path",
            "file_date",
            "file_info",
            "access_granted",
        ]

    def tearDown(self):
        users = [str(self.user.id), str(self.test_user.id)]
        for user in users:
            path = os.path.join(settings.TEST_ROOT, user)
            if os.path.exists(path):
                if os.path.isfile(path) or os.path.islink(path):
                    os.unlink(path)
                else:
                    shutil.rmtree(path)
        path_temp = os.path.join(settings.TEST_ROOT, "temporary")
        if os.path.exists(path_temp):
            if os.path.isfile(path_temp) or os.path.islink(path_temp):
                os.unlink(path_temp)
            # else:
            #     shutil.rmtree(path_temp)  # PermissionError: [WinError 32] The process cannot access the file because it is being used by another process
        # os.rmdir(settings.TEST_ROOT)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Counterparty.objects.count(), 1)
        self.assertEqual(Credit.objects.count(), 1)
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(Renovation.objects.count(), 1)
        self.assertEqual(MedicalVisit.objects.count(), 1)
        self.assertEqual(HealthTestResult.objects.count(), 1)
        self.assertEqual(Attachment.objects.count(), 2)

    def test_attachments_302_redirect_if_unauthorized(self):
        """Test if attachments page is unavailable for unauthorized users."""
        response = self.client.get(reverse("connection:attachments"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_attachments_200_if_logged_in(self):
        """Test if attachments page returns status code 200 for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:attachments"))
        self.assertEqual(response_get.status_code, 200)

    def test_attachments_correct_template_if_logged_in(self):
        """Test if attachments page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:attachments"))
        self.assertTemplateUsed(response_get, "attachment/attachments.html")

    def test_attachments_initial_values_set_context_data(self):
        """Test if attachments page displays correct context data."""
        attachments = Attachment.objects.filter(user=self.user)
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("connection:attachments"))
        self.assertIn(str(self.attachment), response_get.content.decode())
        self.assertEqual(response_get.context["attachments"][0], attachments[0])
        self.assertEqual(response_get.context["profile"],
                         self.attachment.user.profile)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_attachments_initial_values_set_attachments_data(self):
        """Test if page attachments displays only attachments of logged user
        (without attachments of other users)."""
        user_second_attachment = AttachmentFactory(
            user=self.user, attachment_name="new attachment")

        # Test for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("connection:attachments"))

        self.assertIn(self.attachment.attachment_name,
                      response_get.content.decode())
        self.assertIn(user_second_attachment.attachment_name,
                      response_get.content.decode())
        self.assertNotIn(self.test_attachment.attachment_name,
                         response_get.content.decode())

        self.client.logout()

        # Test for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("connection:attachments"))

        self.assertNotIn(self.attachment.attachment_name,
                         response_get.content.decode())
        self.assertNotIn(user_second_attachment.attachment_name,
                         response_get.content.decode())
        self.assertIn(self.test_attachment.attachment_name,
                      response_get.content.decode())

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_download_attachment_302_redirect_if_unauthorized(self):
        """Test if download_attachment page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("connection:download-attachment",
                    args=[self.user.profile.slug, self.attachment.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_download_attachment_200_if_logged_in(self):
        """Test if download_attachment page return status code 200 for
        authenticated user."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("connection:download-attachment",
                    args=[self.user.profile.slug, self.attachment.id]))
        self.assertEqual(response_get.status_code, 200)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_download_attachment_forced_logout_if_security_breach(self):
        """Attempt to download attachment of another user is forbidden and
        triggers logout."""

        # Attempt to download attachment owned by self.test_user by
        # self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("connection:download-attachment",
                    args=[self.test_user.profile.slug, self.test_attachment.id]),
            follow=True)
        self.assertEqual(response_get.status_code, 200)
        self.client.logout()

        # Attempt to download attachment of self.test_user by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("connection:download-attachment",
                    args=[self.test_user.profile.slug, self.test_attachment.id]),
            follow=True)

        self.assertRedirects(
            response_get,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_get.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

    def test_add_attachment_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add attachment
        (user is redirected to login page)."""
        response = self.client.get(reverse("connection:add-attachment"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_attachment_200_if_logged_in(self):
        """Test if add_attachment page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:add-attachment"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_attachment_correct_template_if_logged_in(self):
        """Test if add_attachment page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:add-attachment"))
        self.assertTemplateUsed(response_get, "attachment/attachment_form.html")

    def test_add_attachment_form_initial_values_set_context_data(self):
        """Test if add_attachment page displays correct context data."""
        attachment_names = list(Attachment.objects.filter(
            user=self.user).values_list("attachment_name", flat=True))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:add-attachment"))
        self.assertEqual(response_get.context["page"], "add-attachment")
        self.assertEqual(response_get.context["attachment_names"], attachment_names)
        self.assertIsInstance(response_get.context["form"], AttachmentForm)

    def test_add_attachment_form_initial_values_set_form_data(self):
        """Test if add_attachment page displays correct form data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("connection:add-attachment"))

        for field in self.attachment_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_add_attachment_form_has_only_single_user_data_in_queryset_fields(self):
        """Test if add/edit form does not contain other user's data."""
        test_payment = PaymentFactory(user=self.test_user, name="Test one")
        PaymentFactory(user=self.test_user, name="New test")
        test_credit = CreditFactory(user=self.test_user, name="Test one")
        CreditFactory(user=self.test_user, name="New test")
        test_renovation = RenovationFactory(user=self.test_user, name="Test one")
        RenovationFactory(user=self.test_user, name="New test")
        test_trip = TripFactory(user=self.test_user, name="Test one")
        TripFactory(user=self.test_user, name="New test")
        test_health_result = HealthTestResultFactory(user=self.test_user,
                                                     name="Test one")
        HealthTestResultFactory(user=self.test_user,
                                                       name="New test")
        test_visit = MedicalVisitFactory(user=self.test_user,
                                         specialization="Test one")
        MedicalVisitFactory(user=self.test_user,
                                           specialization="New test")

        # Test on user
        self.client.force_login(self.user)
        attachment_names = []
        form = AttachmentForm(attachment_names=attachment_names)
        form.fields["payments"].queryset = Payment.objects.filter(user=self.user)
        form.fields["credits"].queryset = Credit.objects.filter(user=self.user)
        form.fields["renovations"].queryset = Renovation.objects.filter(user=self.user)
        form.fields["trips"].queryset = Trip.objects.filter(user=self.user)
        form.fields["health_results"].queryset = HealthTestResult.objects.filter(user=self.user)
        form.fields["medical_visits"].queryset = MedicalVisit.objects.filter(user=self.user)
        payment_choices_in_form_field = (list(field[1] for field in
                                              form.fields["payments"].choices))
        credit_choices_in_form_field = (list(field[1] for field in
                                             form.fields["credits"].choices))
        renovation_choices_in_form_field = (list(field[1] for field in
                                                 form.fields["renovations"].choices))
        trip_choices_in_form_field = (list(field[1] for field in
                                           form.fields["trips"].choices))
        health_result_choices_in_form_field = (list(field[1] for field in
                                                    form.fields["health_results"].choices))
        visit_choices_in_form_field = (list(field[1] for field in
                                            form.fields["medical_visits"].choices))

        self.assertIn(self.payment.name, payment_choices_in_form_field)
        self.assertNotIn(test_payment.name, payment_choices_in_form_field)
        self.assertEqual(len(payment_choices_in_form_field), 1)
        self.assertIn(self.credit.name, credit_choices_in_form_field)
        self.assertNotIn(test_credit.name, credit_choices_in_form_field)
        self.assertEqual(len(credit_choices_in_form_field), 1)
        self.assertIn(self.renovation.name, renovation_choices_in_form_field)
        self.assertNotIn(test_renovation.name, renovation_choices_in_form_field)
        self.assertEqual(len(renovation_choices_in_form_field), 1)
        self.assertIn(self.trip.name, trip_choices_in_form_field)
        self.assertNotIn(test_trip.name, trip_choices_in_form_field)
        self.assertEqual(len(trip_choices_in_form_field), 1)
        self.assertNotIn(test_health_result.name, health_result_choices_in_form_field)
        self.assertEqual(len(health_result_choices_in_form_field), 1)
        self.assertNotIn(test_visit.specialization, visit_choices_in_form_field)
        self.assertEqual(len(visit_choices_in_form_field), 1)

        # Test on test_user
        self.client.force_login(self.test_user)
        attachment_names = []
        form = AttachmentForm(attachment_names=attachment_names)
        form.fields["payments"].queryset = Payment.objects.filter(user=self.test_user)
        form.fields["credits"].queryset = Credit.objects.filter(user=self.test_user)
        form.fields["renovations"].queryset = Renovation.objects.filter(user=self.test_user)
        form.fields["trips"].queryset = Trip.objects.filter(user=self.test_user)
        form.fields["health_results"].queryset = HealthTestResult.objects.filter(user=self.test_user)
        form.fields["medical_visits"].queryset = MedicalVisit.objects.filter(user=self.test_user)
        payment_choices_in_form_field = (list(field[1] for field in
                                              form.fields["payments"].choices))
        credit_choices_in_form_field = (list(field[1] for field in
                                             form.fields["credits"].choices))
        renovation_choices_in_form_field = (list(field[1] for field in
                                                 form.fields["renovations"].choices))
        trip_choices_in_form_field = (list(field[1] for field in
                                           form.fields["trips"].choices))
        health_result_choices_in_form_field = (list(field[1] for field in
                                                    form.fields["health_results"].choices))
        visit_choices_in_form_field = (list(field[1] for field in
                                            form.fields["medical_visits"].choices))
        self.assertIn(test_payment.name, payment_choices_in_form_field)
        self.assertNotIn(self.payment.name, payment_choices_in_form_field)
        self.assertEqual(len(payment_choices_in_form_field), 2)
        self.assertIn(test_credit.name, credit_choices_in_form_field)
        self.assertNotIn(self.credit.name, credit_choices_in_form_field)
        self.assertEqual(len(credit_choices_in_form_field), 2)
        self.assertIn(test_renovation.name, renovation_choices_in_form_field)
        self.assertNotIn(self.renovation.name, renovation_choices_in_form_field)
        self.assertEqual(len(renovation_choices_in_form_field), 2)
        self.assertIn(test_trip.name, trip_choices_in_form_field)
        self.assertNotIn(self.trip.name, trip_choices_in_form_field)
        self.assertEqual(len(trip_choices_in_form_field), 2)
        self.assertIn(test_health_result.name, health_result_choices_in_form_field)
        self.assertNotIn(self.health_result.name, health_result_choices_in_form_field)
        self.assertEqual(len(health_result_choices_in_form_field), 2)
        self.assertIn(test_visit.__str__(), visit_choices_in_form_field)
        self.assertNotIn(self.medical.specialization, visit_choices_in_form_field)
        self.assertEqual(len(visit_choices_in_form_field), 2)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_add_attachment_success_and_redirect(self):
        """Test if creating attachment is successful (status code 200) and
        redirecting is successful (status code 302)."""
        image_mock = MagicMock(spec=File)
        image_mock.name = "image.png"
        payload = {
            "attachment_name": "New attachment name",
            "attachment_path": image_mock,
            "access_granted": Access.NO_ACCESS_GRANTED
        }
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "connection:add-attachment"),
            data=payload,
            format="multipart",
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("connection:attachments"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Plik został dodany do bazy danych.",
                      str(messages[0]))
        self.assertInHTML("New attachment name",
                          response_post.content.decode())
        self.assertEqual(Attachment.objects.count(), 3)
        self.assertTrue(Attachment.objects.filter(
            user=self.user, attachment_name=payload["attachment_name"]).exists())

    def test_delete_attachment_302_redirect_if_unauthorized(self):
        """Test if delete_attachment page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("connection:delete-attachment", args=[self.attachment.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_attachment_200_if_logged_in(self):
        """Test if delete_attachment page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("connection:delete-attachment", args=[self.attachment.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_attachment_correct_template_if_logged_in(self):
        """Test if delete_attachment page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("connection:delete-attachment", args=[self.attachment.id]))
        self.assertTemplateUsed(response_get,
                                "attachment/attachment_delete_form.html")

    def test_delete_attachment_initial_values_set_context_data(self):
        """Test if delete_attachment page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("connection:delete-attachment", args=[str(self.attachment.id)]))
        self.assertIn(str(self.attachment), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-attachment")
        self.assertEqual(response_get.context["attachment"], self.attachment)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_delete_attachment_and_redirect(self):
        """Deleting attachment is successful (status code 200) and redirect
        is successful (status code 302)."""
        attachment = self.attachment
        self.assertEqual(Attachment.objects.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(reverse("connection:attachments"))
        self.assertIn(str(attachment), response.content.decode())

        response = self.client.get(reverse(
            "connection:delete-attachment", args=[str(self.attachment.id)]))
        self.assertEqual(response.context["attachment"], self.attachment)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                template_name="attachment/attachment_delete_form.html")

        response_delete = self.client.post(
            reverse("connection:delete-attachment", args=[str(self.attachment.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("connection:attachments"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Załącznik został usunięty.", str(messages[0]))

        response = self.client.get(reverse("connection:attachments"))
        self.assertEqual(Attachment.objects.count(), 1)
        self.assertNotIn(self.attachment.attachment_name, response.content.decode())
        self.assertNotIn(self.test_attachment.attachment_name, response.content.decode())

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_delete_attachment_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("connection:delete-attachment",
                    args=[str(self.attachment.id)]),
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("connection:delete-attachment",
                    args=[str(self.attachment.id)]),
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("connection:delete-attachment",
                    args=[str(self.attachment.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_attachment_logout_if_security_breach(self):
        """Deleting attachment of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(Attachment.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_attachment.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("connection:delete-attachment",
                    args=[str(self.test_attachment.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do usunięcia tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(Attachment.objects.count(), 2)
