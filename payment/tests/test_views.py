import datetime
import logging
import shutil
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from parameterized import parameterized
from reportlab.pdfgen.canvas import Canvas

from access.enums import Access
from connection.factories import AttachmentFactory, CounterpartyFactory
from connection.models import Attachment, Counterparty
from payment.factories import PaymentFactory
from payment.forms import PaymentForm
from payment.models import Payment

logger = logging.getLogger("test")
User = get_user_model()


class BasicUrlsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.payment = PaymentFactory(user=self.user, name="setup payment",)

        self.pages = [
            {"page": "payment:payments", "args": [],
             "template": "payment/payments.html"},
            {"page": "payment:single-payment", "args": [str(self.payment.id)],
             "template": "payment/single_payment.html"},
            {"page": "payment:add-payment", "args": [],
             "template": "payment/payment_form.html"},
            {"page": "payment:edit-payment", "args": [str(self.payment.id)],
             "template": "payment/payment_form.html"},
            {"page": "payment:delete-payment", "args": [str(self.payment.id)],
             "template": "payment/payment_delete_form.html"},
        ]

    def test_view_url_status_code_302_for_unauthenticated_user(self):
        """Test if user is redirected to login page if unauthorised."""
        for page in self.pages:
            url = reverse(page["page"], args=page["args"])
            response_page = self.client.get(url)
            self.assertEqual(response_page.status_code, 302)
            self.assertIn("login", response_page.url)

    def test_view_url_status_code_200_for_authenticated_user(self):
        """Test if view url exists at desired location for authenticated user."""
        self.client.force_login(self.user)
        for page in self.pages:
            url = reverse(page["page"], args=page["args"])
            response_page = self.client.get(url)
            self.assertEqual(response_page.status_code, 200)
            self.assertEqual(str(response_page.context["user"]), "johndoe123")

    def test_view_uses_correct_template(self):
        """Test if response returns correct page template."""

        # Test for authenticated user
        self.client.force_login(self.user)
        for page in self.pages:
            response = self.client.get(
                reverse(page["page"], args=page["args"]))
            self.assertTemplateUsed(response, page["template"])


class PaymentsTests(TestCase):
    """Test Payment views."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com",
            password="testpass456")
        self.payment = PaymentFactory(
            user=self.user,
            name="setup payment",
            payment_type=_("Czynsz"),
            payment_months="5",     # as a payload for PaymentForm
            payment_day=11,
            access_granted=_("Brak dostępu")
        )
        self.test_payment = PaymentFactory(
            user=self.test_user,
            name="test payment",
            payment_type=_("Media"),
            payment_status=_("Brak informacji"),
            payment_frequency=_("Rocznie"),
            payment_months="2",
            payment_day=22,
            access_granted=_("Brak dostępu")
        )

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Payment.objects.count(), 2)

    def test_payments_302_redirect_if_unauthorized(self):
        """Test if payments page is unavailable for unauthorized users."""
        response = self.client.get(reverse("payment:payments"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_payments_200_if_logged_in(self):
        """Test if payments page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("payment:payments"))
        self.assertEqual(response_get.status_code, 200)

    def test_payments_correct_template_if_logged_in(self):
        """Test if payments page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("payment:payments"))
        self.assertTemplateUsed(response_get, "payment/payments.html")

    def test_payments_initial_values_set_context_data(self):
        """Test if payments page displays correct context data."""
        payments = Payment.objects.filter(user=self.user).order_by("-updated")
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("payment:payments"))
        self.assertQuerysetEqual(response_get.context["payments"], payments)

    def test_payments_initial_values_set_payments_data(self):
        """Test if logged user can see data for payments without seeing
        payments of other users."""

        # Test payments content for self.user "johndoe123"
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("payment:payments"))

        self.assertIn(self.payment.name, response_get.content.decode())
        self.assertNotIn(self.test_payment.name,
                         response_get.content.decode())

        self.client.logout()

        # Test payments content for se;f.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("payment:payments"))

        self.assertNotIn(self.payment.name, response_get.content.decode())
        self.assertIn(self.test_payment.name, response_get.content.decode())

    def test_single_payment_302_redirect_if_unauthorized(self):
        """ Test if single_payment page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("payment:single-payment", args=[self.payment.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    def test_single_payment_200_if_logged_in(self):
        """Test if single_payment page return status code 200 for
        authenticated user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("payment:single-payment", args=[self.payment.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_single_payment_correct_template_if_logged_in(self):
        """Test if single_payment page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("payment:single-payment", args=[self.payment.id]))
        self.assertTemplateUsed(response_get, "payment/single_payment.html")

    def test_single_payment_initial_values_set_context_data(self):
        """Test if single_payment page displays correct context data."""
        attachments = Attachment.objects.filter(payments=self.payment.id)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("payment:single-payment", args=[str(self.payment.id)]))
        self.assertQuerySetEqual(response_get.context["payment"], self.payment)
        self.assertQuerysetEqual(response_get.context["attachments"], attachments)
        self.assertEqual(response_get.context["profile"], self.payment.user.profile)

    def test_single_payment_initial_values_set_payment_data(self):
        """Test if single_payment page displays correct payment data
        (only data of logged user)."""

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("payment:single-payment", args=[self.payment.id]))

        self.assertIn(self.payment.name, response_get.content.decode())
        self.assertNotIn(self.test_payment.name,
                         response_get.content.decode())
        self.assertIn(str(self.payment.payment_type),
                      response_get.content.decode())
        self.assertNotIn(str(self.test_payment.payment_type),
                         response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("payment:single-payment",
                    args=[self.test_payment.id]))

        self.assertIn(self.test_payment.name, response_get.content.decode())
        self.assertNotIn(self.payment.name, response_get.content.decode())
        self.assertIn(str(self.test_payment.payment_type),
                      response_get.content.decode())
        self.assertNotIn(str(self.payment.payment_type),
                         response_get.content.decode())

    def test_single_payment_initial_values_set_counterparties_data(self):
        """Test if single_payment page displays correct counterparty data
        (only data of logged user)."""
        user_counterparty_1 = CounterpartyFactory(user=self.user, name="cp 1")
        user_counterparty_2 = CounterpartyFactory(user=self.user, name="cp 2")
        test_user_counterparty = CounterpartyFactory(user=self.test_user, name="test cp")
        self.assertEqual(Counterparty.objects.filter(user=self.user).count(), 2)
        self.assertEqual(Counterparty.objects.filter(user=self.test_user).count(), 1)
        user_counterparty_1.payments.add(self.payment)
        user_counterparty_1.save()
        user_counterparty_2.payments.add(self.payment)
        user_counterparty_2.save()
        test_user_counterparty.payments.add(self.test_payment)
        test_user_counterparty.save()

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("payment:single-payment", args=[self.payment.id]))

        self.assertIn(user_counterparty_1.name, response_get.content.decode())
        self.assertIn(user_counterparty_2.name, response_get.content.decode())
        self.assertNotIn(test_user_counterparty.name, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("payment:single-payment",
                    args=[self.test_payment.id]))

        self.assertIn(test_user_counterparty.name, response_get.content.decode())
        self.assertNotIn(user_counterparty_1.name, response_get.content.decode())
        self.assertNotIn(user_counterparty_2.name, response_get.content.decode())

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_single_payment_initial_values_set_attachments(self):
        """Test if single_payment page displays correct attachments
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
        self.attachment.payments.add(self.payment)
        self.test_attachment.payments.add(self.test_payment)

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("payment:single-payment", args=[self.payment.id]))
        payment_id = response_get.request["PATH_INFO"].split("/")[-2]
        self.assertQuerySetEqual(self.payment, Payment.objects.get(id=payment_id))
        self.assertIn(self.payment.name, response_get.content.decode())
        self.assertNotIn(self.test_payment.name, response_get.content.decode())
        self.assertIn(self.attachment.attachment_name, response_get.content.decode())
        self.assertNotIn(self.test_attachment.attachment_name,
                         response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("payment:single-payment", args=[self.test_payment.id]))

        self.assertIn(self.test_payment.name, response_get.content.decode())
        self.assertNotIn(self.payment.name, response_get.content.decode())
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

    def test_single_payment_forced_logout_if_security_breach(self):
        """Attempt to overview payment of another user is forbidden and
        triggers logout."""

        # Attempt to see self.test_user data by self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("payment:single-payment",
                    args=[self.test_payment.id]), follow=True)
        self.assertIn(self.test_payment.name, response_get.content.decode())
        self.client.logout()

        # Attempt to see self.test_user data by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("payment:single-payment",
                    args=[self.test_payment.id]), follow=True)
        self.assertNotIn(self.test_payment.name, response_get.content.decode())
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

    def test_add_payment_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add payment
        (user is redirected to login page)."""
        response = self.client.get(reverse("payment:add-payment"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_payment_200_if_logged_in(self):
        """Test if add_payment page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("payment:add-payment"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_payment_correct_template_if_logged_in(self):
        """Test if add_payment page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("payment:add-payment"))
        self.assertTemplateUsed(response_get, "payment/payment_form.html")

    def test_add_payment_form_initial_values_set_context_data(self):
        """Test if add_payment page displays correct context data."""
        payment_names = list(Payment.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("payment:add-payment"))
        self.assertEqual(response_get.context["page"], "add-payment")
        self.assertQuerysetEqual(response_get.context["payment_names"], payment_names)
        self.assertIsInstance(response_get.context["form"], PaymentForm)

    def test_add_payment_initial_values_set_form_data(self):
        """Test if add_payment page displays correct form data."""
        payment_fields = ["name", "payment_type", "payment_method",
                          "payment_status", "payment_frequency",
                          "payment_months", "payment_day", "payment_value",
                          "notes", "start_of_agreement", "end_of_agreement",
                          "access_granted"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("payment:add-payment"))
        for field in payment_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())    # input type="submit"

    def test_add_payment_success_and_redirect(self):
        """Test if creating a payment is successful (status code 200) and
        redirecting is successful (status code 302)."""
        payment_names = list(Payment.objects.filter(
            user=self.user).values_list("name", flat=True))

        payload = {
            "name": "new payment",
            "payment_type": [_("Media")],
            "payment_method": "",
            "payment_status": [_("Brak informacji")],
            "payment_frequency": [_("Rocznie")],
            "payment_months": ["8"],
            "payment_day": 27,
            "payment_value": 222,
            "notes": "",
            "start_of_agreement": "",
            "end_of_agreement": "",
            "access_granted": [_("Brak dostępu")],
        }
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("payment:add-payment"),
            payload, payment_names=payment_names, follow=True)  # with follow=True status code should be 200 and site message: "Dodano płatność"
        self.assertEqual(response_post.status_code, 200)  # with follow=True in response (status code is 200 for follow=True as page is already redirected)
        self.assertRedirects(
            response_post,
            reverse("payment:payments"),
            status_code=302,
            target_status_code=200,
            msg_prefix="",
            fetch_redirect_response=True,
        )
        self.assertTemplateUsed(response_post, "payment/payments.html")
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano płatność.", str(messages[0]))
        self.assertInHTML("new payment", response_post.content.decode())
        self.assertEqual(Payment.objects.count(), 3)
        self.assertTrue(Payment.objects.filter(
            user=self.user, name=payload["name"]).exists())

    def test_add_payment_successful_with_correct_user(self):
        """Test if creating a payment successfully has correct user."""
        payment_names = list(Payment.objects.filter(
            user=self.user).values_list("name", flat=True))

        payload = {
            "name": "new payment for testing user",
            "payment_type": [_("Media")],
            "payment_method": "",
            "payment_status": [_("Brak informacji")],
            "payment_frequency": [_("Rocznie")],
            "payment_months": ["8"],
            "payment_day": 27,
            "payment_value": 222,
            "notes": "",
            "start_of_agreement": "",
            "end_of_agreement": "",
            "access_granted": [_("Brak dostępu")],
        }
        self.client.force_login(self.user)

        self.client.post(
            reverse("payment:add-payment"),
            payload, payment_names=payment_names, follow=True)

        payment = Payment.objects.get(name=payload["name"])
        self.assertEqual(payment.user, self.user)

    @parameterized.expand(
        [
            ("Empty field: access_granted",
             {"name": "new pmt"},
             "To pole jest wymagane."),
            ("Empty field: name",
             {"access_granted": "Brak dostępu"},
             "To pole jest wymagane."),
            ("Not unique field: name",
             {"name": "setup payment", "access_granted": "Brak dostępu"},
             "Istnieje już płatność o podanej nazwie w bazie danych."),
            ("Incorrect date field",
             {"name": "new payment", "access_granted": "Brak dostępu",
              "start_of_agreement": "2020/1/1"},
             "Wpisz poprawną datę."),
            ("End date before start date",
             {"name": "new payment", "access_granted": "Brak dostępu",
              "start_of_agreement": datetime.date(2020, 2, 2),
              "end_of_agreement": datetime.date(2020, 1, 1)},
             "Data wygaśnięcia umowy nie może przypadać wcześniej "
             "niż data jej zawarcia."),
            ("Incorrect payment_value field (negative value not allowed)",
             {"name": "new payment", "access_granted": "Brak dostępu",
              "payment_value": -12, },
             "Wystąpił błąd podczas zapisu formularza. Sprawdź poprawność danych."),
        ]
    )
    def test_add_payment_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a payment is not successful if data is incorrect."""
        self.client.force_login(self.user)
        payment_names = list(Payment.objects.filter(
            user=self.payment.user).values_list("name", flat=True))
        response_post = self.client.post(
            reverse("payment:add-payment"), payload, payment_names=payment_names)
        self.assertEqual(Payment.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_payment_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot edit payment
        (user is redirected to login page)."""
        response = self.client.get(
            reverse("payment:edit-payment", args=[self.payment.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_payment_200_if_logged_in(self):
        """Test if edit_payment page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("payment:edit-payment", args=[self.payment.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_payment_correct_template_if_logged_in(self):
        """Test if edit_payment page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("payment:edit-payment", args=[self.payment.id]))
        self.assertTemplateUsed(response_get, "payment/payment_form.html")

    def test_edit_payment_form_initial_values_set_context_data(self):
        """Test if edit_payment page displays correct context data."""
        payment_names = list(
            Payment.objects.filter(user=self.user).exclude(
                id=self.payment.id).values_list(
                "name", flat=True))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("payment:edit-payment", args=[str(self.payment.id)]))
        self.assertEqual(response_get.context["page"], "edit-payment")
        self.assertQuerysetEqual(response_get.context["payment"], self.payment)
        self.assertQuerysetEqual(response_get.context["payment_names"],
                                 payment_names)
        self.assertIsInstance(response_get.context["form"], PaymentForm)

    def test_edit_payment_form_initial_values_set_form_data(self):
        """Test if edit_payment page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("payment:edit-payment", args=[str(self.payment.id)]))
        self.assertIn(self.payment.notes, response_get.content.decode())
        self.assertIn(self.payment.name, response_get.content.decode())

    def test_edit_payment_success_and_redirect(self):
        """Test if updating a payment is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        payment_names = list(Payment.objects.filter(
            user=self.user).exclude(
            id=self.payment.id).values_list("name", flat=True))

        payload = {
            "name": "New payment test name",
            "payment_type": "Media",
            "payment_method": self.payment.payment_method,
            "payment_status": "Zapłacone",
            "payment_frequency": "Inne",
            "payment_months": self.payment.payment_months,
            "payment_day": self.payment.payment_day,
            "payment_value": self.payment.payment_value,
            "notes": "New med for new disease",
            "start_of_agreement": self.payment.start_of_agreement,
            "end_of_agreement": self.payment.end_of_agreement,
            "access_granted": Access.ACCESS_GRANTED,
        }
        self.assertNotEqual(self.payment.notes, payload["notes"])
        self.assertNotEqual(self.payment.name, payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("payment:edit-payment",
                    args=[str(self.payment.id)]),
            data=payload,
            instance=self.payment,
            payment_names=payment_names,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("payment:single-payment", args=[str(self.payment.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Płatność została zaktualizowana.", str(messages[0]))
        self.payment.refresh_from_db()
        self.assertEqual(Payment.objects.count(), 2)
        self.assertEqual(self.payment.name, payload["name"])
        self.assertEqual(self.payment.notes, payload["notes"])

    def test_edit_payment_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        payment_names = list(Payment.objects.filter(
            user=self.user).exclude(
            id=self.payment.id).values_list("name", flat=True))
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "New name as update",
            "access_granted": Access.ACCESS_GRANTED,
        }
        response_patch = self.client.patch(
            reverse("payment:edit-payment",
                    args=[str(self.payment.id)]),
            data=payload,
            instance=self.payment,
            payment_names=payment_names,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "name": "New payment test name",
            "payment_type": self.payment.payment_type,
            "payment_method": self.payment.payment_method,
            "payment_status": self.payment.payment_status,
            "payment_frequency": self.payment.payment_frequency,
            "payment_months": self.payment.payment_months,
            "payment_day": self.payment.payment_day,
            "payment_value": self.payment.payment_value,
            "notes": "New med for new disease",
            "start_of_agreement": self.payment.start_of_agreement,
            "end_of_agreement": self.payment.end_of_agreement,
            "access_granted": Access.ACCESS_GRANTED,
        }
        response_put = self.client.put(
            reverse("payment:edit-payment",
                    args=[str(self.payment.id)]),
            data=payload,
            instance=self.payment,
            payment_names=payment_names,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("payment:edit-payment",
                    args=[str(self.payment.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_payment_logout_if_security_breach(self):
        """Editing payment of another user is unsuccessful and triggers logout."""
        payment_names = list(Payment.objects.filter(
            user=self.user).exclude(
            id=self.test_payment.id).values_list("name", flat=True))

        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_payment.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "payment_type": self.payment.payment_type,
            "payment_method": self.payment.payment_method,
            "payment_status": self.payment.payment_status,
            "payment_frequency": self.payment.payment_frequency,
            "payment_months": self.payment.payment_months,
            "payment_day": self.payment.payment_day,
            "payment_value": self.payment.payment_value,
            "notes": "SECURITY BREACH",
            "start_of_agreement": self.payment.start_of_agreement,
            "end_of_agreement": self.payment.end_of_agreement,
            "access_granted": Access.ACCESS_GRANTED,
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("payment:edit-payment",
                    args=[str(self.test_payment.id)]),
            data=payload,
            content_type="text/html",
            payment_names=payment_names,
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
        self.assertEqual(Payment.objects.count(), 2)
        self.assertNotIn(self.test_payment.name, payload["name"])

    def test_delete_payment_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot delete payment
        (user is redirected to login page)."""
        response = self.client.get(
            reverse("payment:delete-payment", args=[self.payment.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_payment_200_if_logged_in(self):
        """Test if delete_payment page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("payment:delete-payment", args=[self.payment.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_payment_correct_template_if_logged_in(self):
        """Test if delete_payment page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("payment:delete-payment", args=[self.payment.id]))
        self.assertTemplateUsed(response_get,
                                "payment/payment_delete_form.html")

    def test_delete_payment_initial_values_set_context_data(self):
        """Test if delete_payment page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("payment:delete-payment", args=[str(self.payment.id)]))
        self.assertIn(str(self.payment), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-payment")
        self.assertQuerysetEqual(response_get.context["payment"], self.payment)

    def test_delete_payment_success_and_redirect(self):
        """Deleting payment is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(Payment.objects.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(reverse("payment:payments"))
        self.assertIn(str(self.payment), response.content.decode())

        response_delete = self.client.post(
            reverse("payment:delete-payment", args=[str(self.payment.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("payment:payments"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Płatność została usunięta.", str(messages[0]))

        response = self.client.get(reverse("payment:payments"))
        self.assertEqual(Payment.objects.count(), 1)
        self.assertNotIn(self.payment.name, response.content.decode())
        self.assertNotIn(self.test_payment.name, response.content.decode())

    def test_delete_payment_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("payment:delete-payment",
                    args=[str(self.payment.id)]),
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("payment:delete-payment",
                    args=[str(self.payment.id)]),
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("payment:delete-payment",
                    args=[str(self.payment.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_payment_logout_if_security_breach(self):
        """Deleting payment of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(Payment.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_payment.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("payment:delete-payment",
                    args=[str(self.test_payment.id)]),
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
        self.assertEqual(Payment.objects.count(), 2)
