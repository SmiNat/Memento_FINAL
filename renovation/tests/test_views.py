import datetime
import logging
import shutil
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from parameterized import parameterized
from reportlab.pdfgen.canvas import Canvas

from access.enums import Access
from connection.factories import AttachmentFactory, CounterpartyFactory
from connection.models import Attachment, Counterparty
from renovation.factories import RenovationFactory, RenovationCostFactory
from renovation.forms import RenovationForm, RenovationCostForm
from renovation.models import Renovation, RenovationCost

logger = logging.getLogger("test")
User = get_user_model()


class BasicUrlsTests(TestCase):
    """Test Renovation, RenovationCost basic urls."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.renovation = RenovationFactory(user=self.user)
        self.renovation_cost = RenovationCostFactory(user=self.user)

        self.pages = [
            {"page": "renovation:renovations",
             "args": [], "name": "renovations",
             "template": "renovation/renovations.html"},
            {"page": "renovation:single-renovation",
             "args": [str(self.renovation.id)], "name": "single-renovation",
             "template": "renovation/single_renovation.html"},

            {"page": "renovation:add-renovation",
             "args": [], "name": "add-renovation",
             "template": "renovation/renovation_form.html"},
            {"page": "renovation:edit-renovation",
             "args": [str(self.renovation.id)], "name": "edit-renovation",
             "template": "renovation/renovation_form.html"},
            {"page": "renovation:delete-renovation",
             "args": [str(self.renovation.id)], "name": "delete-renovation",
             "template": "renovation/renovation_delete_form.html"},

            {"page": "renovation:add-renovation-cost",
             "args": [str(self.renovation.id)], "name": "add-renovation-cost",
             "template": "renovation/renovation_form.html"},
            {"page": "renovation:edit-renovation-cost",
             "args": [str(self.renovation_cost.id)], "name": "edit-renovation-cost",
             "template": "renovation/renovation_form.html"},
            {"page": "renovation:delete-renovation-cost",
             "args": [str(self.renovation_cost.id)], "name": "delete-renovation-cost",
             "template": "renovation/renovation_delete_form.html"},
        ]

    def test_view_url_accessible_by_name_for_unauthenticated_user(self):
        """Test if view url is accessible by its name
        and returns redirect (302) for unauthenticated user."""
        for page in self.pages:
            response_page = self.client.get(
                reverse(page["page"], args=page["args"]))
            self.assertEqual(response_page.status_code, 302)
            self.assertIn("login", response_page.url)

    def test_view_url_accessible_by_name_for_authenticated_user(self):
        """Test if view url is accessible by its name
         and returns desired page (200) for authenticated user."""
        self.client.force_login(self.user)
        for page in self.pages:
            response_page = self.client.get(
                reverse(page["page"], args=page["args"]))
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


class RenovationTests(TestCase):
    """Test Renovation views."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.renovation = RenovationFactory(
            user=self.user, name="setup name", description="setup notes")

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com", password="testpass456")
        self.test_renovation = RenovationFactory(
            user=self.test_user, name="test name", description="test notes")

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Renovation.objects.count(), 2)

    def test_renovations_302_redirect_if_unauthorized(self):
        """Test if renovations page is unavailable for unauthorized users."""
        response = self.client.get(reverse("renovation:renovations"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_renovations_200_if_logged_in(self):
        """Test if renovations page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("renovation:renovations"))
        self.assertEqual(response_get.status_code, 200)

    def test_renovations_correct_template_if_logged_in(self):
        """Test if renovations page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("renovation:renovations"))
        self.assertTemplateUsed(response_get, "renovation/renovations.html")

    def test_renovations_initial_values_set_context_data(self):
        """Test if renovations page displays correct context data."""
        renovations = Renovation.objects.filter(user=self.user).order_by("-updated")
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("renovation:renovations"))
        self.assertQuerysetEqual(response_get.context["renovations"], renovations)

    def test_renovations_initial_values_set_renovations_data(self):
        """Test if page renovations displays only renovations of logged user
        (without renovations of other users)."""
        new_renovation = RenovationFactory(user=self.user, name="new name")

        # Test for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("renovation:renovations"))

        self.assertIn(self.renovation.name, response_get.content.decode())
        self.assertIn(new_renovation.name, response_get.content.decode())
        self.assertNotIn(self.test_renovation.name, response_get.content.decode())

        self.client.logout()

        # Test for user self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("renovation:renovations"))

        self.assertNotIn(self.renovation.name, response_get.content.decode())
        self.assertNotIn(new_renovation.name, response_get.content.decode())
        self.assertIn(self.test_renovation.name, response_get.content.decode())

    def test_single_renovation_302_redirect_if_unauthorized(self):
        """ Test if single_renovation page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("renovation:single-renovation", args=[self.renovation.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    def test_single_renovation_200_if_logged_in(self):
        """Test if single_renovation page return status code 200 for
        authenticated user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("renovation:single-renovation", args=[self.renovation.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_single_renovation_correct_template_if_logged_in(self):
        """Test if single_renovation page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("renovation:single-renovation", args=[self.renovation.id]))
        self.assertTemplateUsed(
            response_get, "renovation/single_renovation.html")

    def test_single_renovation_initial_values_set_context_data(self):
        """Test if single_renovation page displays correct context data."""
        renovation_costs = RenovationCost.objects.filter(renovation=self.renovation)
        attachments = Attachment.objects.filter(renovations=self.renovation.id)
        if not self.renovation.get_all_costs():
            costs_to_budget = 0
        else:
            costs_to_budget = round(
                (self.renovation.get_all_costs() / self.renovation.estimated_cost) * 100, 2)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:single-renovation", args=[str(self.renovation.id)]))
        self.assertEqual(response_get.context["renovation"], self.renovation)
        self.assertEqual(response_get.context["profile"], self.renovation.user.profile)
        self.assertQuerysetEqual(response_get.context["renovation_costs"], renovation_costs)
        self.assertQuerysetEqual(response_get.context["attachments"], attachments)
        self.assertEqual(response_get.context["sum_of_costs"], self.renovation.get_all_costs())
        self.assertEqual(response_get.context["costs_to_budget"], costs_to_budget)

    def test_single_renovation_initial_values_set_renovation_data(self):
        """Test if single_renovation page displays correct renovation data
        (only data of logged user)."""

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:single-renovation", args=[self.renovation.id]))

        self.assertIn(self.renovation.name, response_get.content.decode())
        self.assertNotIn(self.test_renovation.name, response_get.content.decode())
        self.assertIn(self.renovation.description, response_get.content.decode())
        self.assertNotIn(self.test_renovation.description, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("renovation:single-renovation",
                    args=[self.test_renovation.id]))

        self.assertIn(self.test_renovation.name, response_get.content.decode())
        self.assertNotIn(self.renovation.name, response_get.content.decode())
        self.assertIn(self.test_renovation.description, response_get.content.decode())
        self.assertNotIn(self.renovation.description, response_get.content.decode())

    def test_single_renovation_initial_values_set_renovation_costs_data(self):
        """Test if single_renovation page displays correct renovation costs data
        (only data of logged user)."""
        user_cost_1 = RenovationCostFactory(
            user=self.user, renovation=self.renovation, name="cost 1")
        user_cost_2 = RenovationCostFactory(
            user=self.user, renovation=self.renovation, name="cost 2")
        test_user_cost = RenovationCostFactory(
            user=self.test_user, renovation=self.test_renovation, name="test cost")
        self.assertEqual(RenovationCost.objects.filter(user=self.user).count(), 2)
        self.assertEqual(RenovationCost.objects.filter(user=self.test_user).count(), 1)

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:single-renovation", args=[self.renovation.id]))

        self.assertIn(user_cost_1.name,
                      response_get.content.decode(encoding="UTF-8"))
        self.assertIn(user_cost_2.name,
                      response_get.content.decode(encoding="UTF-8"))
        self.assertNotIn(test_user_cost.name,
                         response_get.content.decode(encoding="UTF-8"))

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("renovation:single-renovation",
                    args=[self.test_renovation.id]))

        self.assertIn(test_user_cost.name,
                      response_get.content.decode(encoding="UTF-8"))
        self.assertNotIn(user_cost_1.name,
                         response_get.content.decode(encoding="UTF-8"))
        self.assertNotIn(user_cost_2.name,
                         response_get.content.decode(encoding="UTF-8"))

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_single_renovation_initial_values_set_attachments(self):
        """Test if single_renovation page displays correct attachments
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
        self.attachment.renovations.add(self.renovation)
        self.test_attachment.renovations.add(self.test_renovation)

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:single-renovation", args=[self.renovation.id]))
        renovation_id = response_get.request["PATH_INFO"].split("/")[-2]
        self.assertEqual(self.renovation, Renovation.objects.get(id=renovation_id))
        self.assertIn(self.renovation.name, response_get.content.decode())
        self.assertNotIn(self.test_renovation.name, response_get.content.decode())
        self.assertIn(self.attachment.attachment_name,
                      response_get.content.decode(encoding="UTF-8"))
        self.assertNotIn(self.test_attachment.attachment_name,
                         response_get.content.decode(encoding="UTF-8"))

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("renovation:single-renovation", args=[self.test_renovation.id]))

        self.assertIn(self.test_renovation.name, response_get.content.decode())
        self.assertNotIn(self.renovation.name, response_get.content.decode())
        self.assertIn(self.test_attachment.attachment_name,
                      response_get.content.decode(encoding="UTF-8"))
        self.assertNotIn(self.attachment.attachment_name,
                         response_get.content.decode(encoding="UTF-8"))

        users = [str(self.user.id), str(self.test_user.id)]
        for user in users:
            path = os.path.join(settings.TEST_ROOT, user)
            if os.path.exists(path):
                if os.path.isfile(path) or os.path.islink(path):
                    os.unlink(path)
                else:
                    shutil.rmtree(path)
        # os.rmdir(settings.TEST_ROOT)

    def test_single_renovation_initial_values_set_counterparties_data(self):
        """Test if single_renovation page displays correct counterparty data
        (only data of logged user)."""
        user_counterparty_1 = CounterpartyFactory(user=self.user, name="cp 1")
        user_counterparty_2 = CounterpartyFactory(user=self.user, name="cp 2")
        test_user_counterparty = CounterpartyFactory(user=self.test_user, name="test cp")
        self.assertEqual(Counterparty.objects.filter(user=self.user).count(), 2)
        self.assertEqual(Counterparty.objects.filter(user=self.test_user).count(), 1)
        user_counterparty_1.renovations.add(self.renovation)
        user_counterparty_1.save()
        user_counterparty_2.renovations.add(self.renovation)
        user_counterparty_2.save()
        test_user_counterparty.renovations.add(self.test_renovation)
        test_user_counterparty.save()

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:single-renovation", args=[self.renovation.id]))

        self.assertIn(user_counterparty_1.name, response_get.content.decode())
        self.assertIn(user_counterparty_2.name, response_get.content.decode())
        self.assertNotIn(test_user_counterparty.name, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("renovation:single-renovation",
                    args=[self.test_renovation.id]))

        self.assertIn(test_user_counterparty.name, response_get.content.decode())
        self.assertNotIn(user_counterparty_1.name, response_get.content.decode())
        self.assertNotIn(user_counterparty_2.name, response_get.content.decode())

    def test_single_renovation_forced_logout_if_security_breach(self):
        """Attempt to overview single renovation of another user is forbidden and
        triggers logout."""

        # Attempt to see self.test_user data by self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("renovation:single-renovation",
                    args=[self.test_renovation.id]), follow=True)
        self.assertIn(self.test_renovation.name,
                      response_get.content.decode(encoding="UTF-8"))
        self.client.logout()

        # Attempt to see self.test_user data by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:single-renovation",
                    args=[self.test_renovation.id]), follow=True)
        self.assertNotIn(self.test_renovation.name,
                         response_get.content.decode(encoding="UTF-8"))
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

    def test_add_renovation_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add renovation
        (user is redirected to login page)."""
        response = self.client.get(reverse("renovation:add-renovation"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_renovation_200_if_logged_in(self):
        """Test if add_renovation page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("renovation:add-renovation"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_renovation_correct_template_if_logged_in(self):
        """Test if add_renovation page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("renovation:add-renovation"))
        self.assertTemplateUsed(response_get, "renovation/renovation_form.html")

    def test_add_renovation_form_initial_values_set_context_data(self):
        """Test if add_renovation page displays correct context data."""
        renovation_names = list(Renovation.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("renovation:add-renovation"))
        self.assertEqual(response_get.context["page"], "add-renovation")
        self.assertQuerysetEqual(response_get.context["renovation_names"],
                                 renovation_names)
        self.assertIsInstance(response_get.context["form"], RenovationForm)

    def test_add_renovation_form_initial_values_set_form_data(self):
        """Test if add_renovation page displays correct form data."""
        renovation_fields = ["name", "description", "estimated_cost",
                             "start_date", "end_date", "access_granted"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("renovation:add-renovation"))
        for field in renovation_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_renovation_success_and_redirect(self):
        """Test if creating a renovation is successful (status code 200) and
        redirecting is successful (status code 302)."""
        payload = {
            "name": "Family room renovation",
            "description": "all new",
            "start_date": datetime.date(2020, 12, 10),
            "access_granted": Access.ACCESS_GRANTED,
        }
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "renovation:add-renovation"),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("renovation:renovations"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano remont.", str(messages[0]))
        self.assertInHTML("Family room renovation",
                          response_post.content.decode())
        self.assertEqual(Renovation.objects.count(), 3)
        self.assertTrue(Renovation.objects.filter(
            user=self.user, name=payload["name"]).exists())

    def test_add_renovation_successful_with_correct_user(self):
        """Test if creating a renovation successfully has correct user."""
        renovation_names = list(Renovation.objects.filter(
            user=self.user).values_list("name", flat=True))

        payload = {
            "name": "Name for testing user",
            "description": "all new",
            "start_date": datetime.date(2020, 12, 10),
            "access_granted": Access.ACCESS_GRANTED,
        }
        self.client.force_login(self.user)

        self.client.post(reverse("renovation:add-renovation"),
                         payload,
                         prenovation_names=renovation_names,
                         follow=True)

        renovation = Renovation.objects.get(name=payload["name"])
        self.assertEqual(renovation.user, self.user)

    @parameterized.expand(
        [
            ("Empty field: name",
             {"access_granted": Access.ACCESS_GRANTED},
             "To pole jest wymagane."),
            ("Empty field: access_granted",
             {"name": "New name for renovation"},
             "To pole jest wymagane."),
            ("Not unique fields (unique together): name",
             {"name": "setup name", "access_granted": Access.ACCESS_GRANTED},
             "Istnieje już remont o podanej nazwie w bazie danych. "
             "Podaj inną nazwę."),
            ("Incorrect date field",
             {"name": "some new name", "access_granted": Access.ACCESS_GRANTED,
              "start_date": "2020/11/11"},
             "Wpisz poprawną datę."),
            ("Incorrect estimated_cost field (negative values are not allowed)",
             {"name": "some new name", "access_granted": Access.ACCESS_GRANTED,
              "estimated_cost": -100},
             "Wartość nie może być liczbą ujemną."),
        ]
    )
    def test_add_renovation_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a renovation is not successful if data is incorrect."""
        self.client.force_login(self.user)
        renovation_names = list(Renovation.objects.filter(
            user=self.renovation.user).values_list("name", flat=True))
        response_post = self.client.post(
            reverse("renovation:add-renovation"),
            data=payload,
            renovation_names=renovation_names)
        self.assertEqual(Renovation.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())
        self.assertTemplateNotUsed(response_post, "renovation/renovations.html")

    def test_edit_renovation_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot edit renovation
        (user is redirected to login page)."""
        response = self.client.get(
            reverse("renovation:edit-renovation", args=[self.renovation.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_renovation_200_if_logged_in(self):
        """Test if edit_renovation page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("renovation:edit-renovation", args=[self.renovation.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_renovation_correct_template_if_logged_in(self):
        """Test if edit_renovation page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("renovation:edit-renovation", args=[self.renovation.id]))
        self.assertTemplateUsed(response_get, "renovation/renovation_form.html")

    def test_edit_renovation_form_initial_values_set_context_data(self):
        """Test if edit_renovation page displays correct context data."""
        renovation_names = list(Renovation.objects.filter(
            user=self.user).exclude(id=self.renovation.id).values_list(
            "name", flat=True))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:edit-renovation", args=[str(self.renovation.id)]))
        self.assertEqual(response_get.context["page"], "edit-renovation")
        self.assertEqual(response_get.context["renovation"], self.renovation)
        self.assertQuerysetEqual(response_get.context["renovation_names"],
                                 renovation_names)
        self.assertIsInstance(response_get.context["form"], RenovationForm)

    def test_edit_renovation_form_initial_values_set_form_data(self):
        """Test if edit_renovation page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:edit-renovation",
                    args=[str(self.renovation.id)]))
        self.assertIn(self.renovation.description, response_get.content.decode())
        self.assertIn(self.renovation.name, response_get.content.decode())

    def test_edit_renovation_success_and_redirect(self):
        """Test if updating a renovation is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        renovation_names = list(Renovation.objects.filter(
            user=self.user).exclude(
            id=self.renovation.id).values_list(
            "name", flat=True))

        payload = {
            "name": "yet another one",
            "description": "New renovation for new room",
            "estimated_cost": self.renovation.estimated_cost,
            "start_date": self.renovation.start_date,
            "end_date": self.renovation.end_date,
            "access_granted": Access.ACCESS_GRANTED,
        }
        self.assertNotEqual(self.renovation.name, payload["name"])
        self.assertNotEqual(self.renovation.description, payload["description"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("renovation:edit-renovation",
                    args=[str(self.renovation.id)]),
            data=payload,
            instance=self.renovation,
            renovation_names=renovation_names,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("renovation:single-renovation", args=[str(self.renovation.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano remont.", str(messages[0]))
        self.renovation.refresh_from_db()
        self.assertEqual(Renovation.objects.count(), 2)
        self.assertEqual(self.renovation.description,
                         payload["description"])
        self.assertEqual(self.renovation.name, payload["name"])

    def test_edit_renovation_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)
        renovation_names = list(Renovation.objects.filter(
            user=self.user).exclude(
            id=self.renovation.id).values_list(
            "name", flat=True))

        # PATCH
        payload = {
            "name": "yet another one",
            "description": "New renovation for new room",
            "access_granted": Access.ACCESS_GRANTED,
        }
        response_patch = self.client.patch(
            reverse("renovation:edit-renovation",
                    args=[str(self.renovation.id)]),
            data=payload,
            instance=self.renovation,
            renovation_names=renovation_names,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "name": "yet another one",
            "description": "New renovation for new room",
            "estimated_cost": self.renovation.estimated_cost,
            "start_date": self.renovation.start_date,
            "end_date": self.renovation.end_date,
            "access_granted": Access.ACCESS_GRANTED,
        }
        response_put = self.client.put(
            reverse("renovation:edit-renovation",
                    args=[str(self.renovation.id)]),
            data=payload,
            instance=self.renovation,
            renovation_names=renovation_names,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("renovation:edit-renovation",
                    args=[str(self.renovation.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_renovation_logout_if_security_breach(self):
        """Editing renovation of another user is unsuccessful and triggers logout."""
        renovation_names = list(Renovation.objects.filter(
            user=self.user).exclude(
            id=self.renovation.id).values_list(
            "name", flat=True))

        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_renovation.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "description": "SECURITY BREACH",
            "estimated_cost": self.renovation.estimated_cost,
            "start_date": self.renovation.start_date,
            "end_date": self.renovation.end_date,
            "access_granted": Access.ACCESS_GRANTED,
        }

        # Attempt to change data that belongs to test_user by user
        response_post = self.client.post(
            reverse("renovation:edit-renovation",
                    args=[str(self.test_renovation.id)]),
            data=payload,
            content_type="text/html",
            renovation_names=renovation_names,
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
        self.assertEqual(Renovation.objects.count(), 2)
        self.assertNotIn(self.test_renovation.description, payload["description"])

    def test_delete_renovation_302_redirect_if_unauthorized(self):
        """Test if delete_renovation page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("renovation:delete-renovation", args=[self.renovation.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_renovation_200_if_logged_in(self):
        """Test if delete_renovation page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("renovation:delete-renovation", args=[self.renovation.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_renovation_correct_template_if_logged_in(self):
        """Test if delete_renovation page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("renovation:delete-renovation", args=[self.renovation.id]))
        self.assertTemplateUsed(response_get,
                                "renovation/renovation_delete_form.html")

    def test_delete_renovation_initial_values_set_context_data(self):
        """Test if delete_renovation page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:delete-renovation", args=[str(self.renovation.id)]))
        self.assertIn(str(self.renovation), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-renovation")
        self.assertEqual(response_get.context["renovation"], self.renovation)

    def test_delete_renovation_successful_and_redirect(self):
        """Deleting renovation is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(
            Renovation.objects.filter(user=self.user).count(), 1)
        renovation_cost = RenovationCost.objects.create(
            user=self.user, renovation=self.renovation, name="cost 1", unit_price=100)
        self.assertEqual(
            RenovationCost.objects.filter(renovation=self.renovation).count(), 1)

        # Checking if pages has correct data before deleting an instance
        self.assertEqual(Renovation.objects.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(reverse("renovation:renovations"))
        self.assertIn(str(self.renovation.name), response.content.decode())
        response_single_page = self.client.get(
            reverse("renovation:single-renovation",
                    args=[str(self.renovation.id)]))
        self.assertIn(str(self.renovation.name), response_single_page.content.decode())
        self.assertIn(str(renovation_cost.name), response_single_page.content.decode())

        # Deleting renovation instance with related renovation costs instances
        response = self.client.get(reverse(
            "renovation:delete-renovation", args=[str(self.renovation.id)]))
        self.assertEqual(response.context["renovation"], self.renovation)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                template_name="renovation/renovation_delete_form.html")

        response_delete = self.client.post(
            reverse("renovation:delete-renovation", args=[str(self.renovation.id)]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("renovation:renovations"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto remont wraz z informacjami dodatkowymi.",
                      str(messages[0]))

        response = self.client.get(reverse("renovation:renovations"))
        self.assertEqual(Renovation.objects.count(), 1)
        self.assertNotIn(self.renovation.name, response.content.decode())
        self.assertNotIn(self.test_renovation.name, response.content.decode())

        self.assertEqual(
            Renovation.objects.filter(user=self.user).count(), 0)
        self.assertEqual(
            RenovationCost.objects.filter(renovation=self.renovation).count(),
            0)

    def test_delete_renovation_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("renovation:delete-renovation",
                    args=[str(self.renovation.id)]),
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("renovation:delete-renovation",
                    args=[str(self.renovation.id)]),
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("renovation:delete-renovation",
                    args=[str(self.renovation.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_renovation_logout_if_security_breach(self):
        """Deleting renovation of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(Renovation.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_renovation.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("renovation:delete-renovation",
                    args=[str(self.test_renovation.id)]),
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
        self.assertEqual(Renovation.objects.count(), 2)


class RenovationCostTests(TestCase):
    """Test RenovationCost views."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.renovation = RenovationFactory(
            user=self.user, name="setup name", description="setup notes")
        self.cost = RenovationCostFactory(
            user=self.user, renovation=self.renovation, name="setup cost")
        self.cost_2 = RenovationCostFactory(
            user=self.user, renovation=self.renovation,
            name="setup additional", unit_price=200, units=2)

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com", password="testpass456")
        self.test_renovation = RenovationFactory(
            user=self.test_user, name="setup name", description="setup notes")
        self.test_cost = RenovationCostFactory(
            user=self.test_user, renovation=self.test_renovation,
            name="test cost", unit_price=300, units=3)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Renovation.objects.count(), 2)
        self.assertEqual(RenovationCost.objects.count(), 3)

    def test_add_renovation_cost_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add renovation cost
        (user is redirected to login page)."""
        response = self.client.get(reverse("renovation:add-renovation-cost",
                                           args=[str(self.renovation.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_renovation_cost_result_200_if_logged_in(self):
        """Test if add_renovation_cost page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("renovation:add-renovation-cost",
                                               args=[str(self.renovation.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_renovation_cost_correct_template_if_logged_in(self):
        """Test if add_renovation_cost page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("renovation:add-renovation-cost",
                                               args=[str(self.renovation.id)]))
        self.assertTemplateUsed(response_get, "renovation/renovation_form.html")

    def test_add_renovation_cost_form_initial_values_set_context_data(self):
        """Test if add_renovation_cost page displays correct context data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("renovation:add-renovation-cost",
                                               args=[str(self.renovation.id)]))
        self.assertEqual(response_get.context["page"], "add-renovation-cost")
        self.assertEqual(response_get.context["renovation"], self.renovation)
        self.assertEqual(response_get.context["renovation_id"], self.renovation.id)
        self.assertIsInstance(response_get.context["form_cost"], RenovationCostForm)

    def test_add_renovation_cost_form_initial_values_set_form_data(self):
        """Test if add_renovation_cost page displays correct form data."""
        cost_fields = ["name", "unit_price", "units", "description", "order"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("renovation:add-renovation-cost",
                                               args=[str(self.renovation.id)]))
        for field in cost_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_renovation_cost_success_and_redirect(self):
        """Test if creating a renovation cost is successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(RenovationCost.objects.count(), 3)
        payload = {
            "name": "New cost",
            "unit_price": 500,
            "units": 1,
        }
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "renovation:add-renovation-cost", args=[str(self.renovation.id)]),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("renovation:single-renovation",
                    args=[str(self.renovation.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano koszty remontu.",
                      str(messages[0]))
        self.assertInHTML("New cost",
                          response_post.content.decode())
        self.assertEqual(RenovationCost.objects.count(), 4)
        self.assertTrue(RenovationCost.objects.filter(
            user=self.user, name=payload["name"]).exists())

    def test_add_renovation_cost_successful_with_correct_user(self):
        """Test if creating a renovation cost successfully has correct user."""
        payload = {
            "name": "New cost",
            "unit_price": 500,
            "units": 1,
        }
        self.client.force_login(self.user)

        self.client.post(
            reverse("renovation:add-renovation-cost",
                    args=[str(self.renovation.id)]),
            payload,
            follow=True)

        cost = RenovationCost.objects.get(name=payload["name"])
        self.assertEqual(cost.user, self.user)

    def test_add_renovation_cost_successful_with_correct_renovation(self):
        """Test if creating a renovation cost successfully has correct
        renovation as foreign key."""
        payload = {
            "name": "New cost",
            "unit_price": 500,
            "units": 1,
        }
        self.client.force_login(self.user)

        self.client.post(
            reverse("renovation:add-renovation-cost",
                    args=[str(self.renovation.id)]),
            payload,
            follow=True)

        cost = RenovationCost.objects.get(name=payload["name"])
        self.assertEqual(cost.renovation, self.renovation)
        self.assertNotEqual(cost.renovation, self.test_renovation)

    @parameterized.expand(
        [
            ("Empty field: name",
             {"unit_price": 300, "units": 5},
             "To pole jest wymagane."),
            ("Empty field: unit_price",
             {"name": "New cost", "units": 10},
             "To pole jest wymagane."),
            ("Empty field: units",
             {"name": "New cost", "unit_price": 40},
             "To pole jest wymagane."),
            ("Incorrect unit_price field (negative value is not allowed)",
             {"name": "OB test", "unit_price": -50, "units": 3},
             "Wartość pola nie może być liczbą ujemną."),
            ("Incorrect units field (negative value is not allowed)",
             {"name": "OB test", "unit_price": 50, "units": -3},
             "Wartość nie może być liczbą ujemną."),
        ]
    )
    def test_add_renovation_cost_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a renovation_cost is not successful if data is incorrect."""
        self.assertEqual(RenovationCost.objects.count(), 3)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("renovation:add-renovation-cost",
                    args=[str(self.renovation.id)]),
            payload)
        self.assertEqual(RenovationCost.objects.count(), 3)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_renovation_cost_302_redirect_if_unauthorized(self):
        """Test if edit_renovation_cost page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("renovation:edit-renovation-cost", args=[self.cost.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_renovation_cost_200_if_logged_in(self):
        """Test if edit_renovation_cost page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("renovation:edit-renovation-cost", args=[self.cost.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_renovation_cost_correct_template_if_logged_in(self):
        """Test if edit_renovation_cost page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("renovation:edit-renovation-cost", args=[self.cost.id]))
        self.assertTemplateUsed(response_get, "renovation/renovation_form.html")

    def test_edit_renovation_cost_form_initial_values_set_context_data(self):
        """Test if edit_renovation_cost page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:edit-renovation-cost", args=[str(self.cost.id)]))
        self.assertEqual(response_get.context["page"], "edit-renovation-cost")
        self.assertEqual(response_get.context["cost"], self.cost)
        self.assertEqual(response_get.context["renovation"], self.renovation)
        self.assertEqual(response_get.context["renovation_id"], self.renovation.id)
        self.assertIsInstance(response_get.context["form_cost"], RenovationCostForm)

    def test_edit_renovation_cost_form_initial_values_set(self):
        """Test if edit_renovation_cost page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:edit-renovation-cost", args=[str(self.cost.id)]))
        self.assertIn(self.cost.description, response_get.content.decode())
        self.assertIn(self.cost.name, response_get.content.decode())

    def test_edit_renovation_cost_success_and_redirect(self):
        """Test if updating a renovation_cost is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        payload = {
            "name": "New cost name",
            "unit_price": self.cost.unit_price,
            "units": self.cost.units,
            "description": self.cost.description,
            "order": "Before midnight",
        }
        self.assertNotEqual(self.cost.order, payload["order"])
        self.assertNotEqual(self.cost.name, payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("renovation:edit-renovation-cost",
                    args=[str(self.cost.id)]),
            data=payload,
            instance=self.cost,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("renovation:single-renovation",
                    args=[str(self.renovation.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono remont.", str(messages[0]))
        self.cost.refresh_from_db()
        self.assertEqual(RenovationCost.objects.count(), 3)
        self.assertEqual(self.cost.name, payload["name"])
        self.assertEqual(self.cost.order, payload["order"])

    def test_edit_renovation_cost_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "New cost name",
            "unit_price": self.cost.unit_price,
            "units": self.cost.units,
            "description": self.cost.description,
            "order": "Before midnight",
        }
        response_patch = self.client.patch(
            reverse("renovation:edit-renovation-cost",
                    args=[str(self.cost.id)]),
            data=payload,
            instance=self.cost,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "name": "New cost name",
            "unit_price": self.cost.unit_price,
            "units": self.cost.units,
            "description": self.cost.description,
            "order": "Before midnight",
        }
        response_put = self.client.put(
            reverse("renovation:edit-renovation-cost",
                    args=[str(self.cost.id)]),
            data=payload,
            instance=self.cost,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("renovation:edit-renovation-cost",
                    args=[str(self.cost.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_renovation_cost_logout_if_security_breach(self):
        """Editing renovation_cost of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_cost.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "unit_price": self.cost.unit_price,
            "units": self.cost.units,
            "description": self.cost.description,
            "order": "SECURITY BREACH",
        }

        # Attempt to change data that belongs to test_user by user
        response_post = self.client.post(
            reverse("renovation:edit-renovation-cost",
                    args=[str(self.test_cost.id)]),
            data=payload,
            content_type="text/html",
            instance=self.test_cost,
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
        self.assertEqual(RenovationCost.objects.count(), 3)
        self.assertNotIn(self.test_cost.name, payload["name"])

    def test_delete_renovation_cost_302_redirect_if_unauthorized(self):
        """Test if delete_renovation_cost page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("renovation:delete-renovation-cost", args=[self.cost.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_renovation_cost_200_if_logged_in(self):
        """Test if delete_renovation_cost page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("renovation:delete-renovation-cost", args=[self.cost.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_renovation_cost_correct_template_if_logged_in(self):
        """Test if delete_renovation_cost page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("renovation:delete-renovation-cost", args=[self.cost.id]))
        self.assertTemplateUsed(response_get,
                                "renovation/renovation_delete_form.html")

    def test_delete_renovation_cost_initial_values_set_context_data(self):
        """Test if delete_renovation_cost page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("renovation:delete-renovation-cost", args=[str(self.cost.id)]))
        self.assertIn(self.cost.name, response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-renovation-cost")
        self.assertEqual(response_get.context["cost"], self.cost)

    def test_delete_renovation_cost_successful_and_redirect(self):
        """Deleting renovation cost is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(RenovationCost.objects.count(), 3)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("renovation:single-renovation",
                    args=[str(self.renovation.id)]))
        self.assertIn(str(self.cost), response.content.decode())
        self.assertIn(str(self.cost_2), response.content.decode())

        response_delete = self.client.post(
            reverse("renovation:delete-renovation-cost", args=[str(self.cost.id)]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("renovation:renovations"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto koszt remontu.", str(messages[0]))

        response = self.client.get(
            reverse("renovation:single-renovation",
                    args=[str(self.renovation.id)]))
        self.assertEqual(RenovationCost.objects.count(), 2)
        self.assertNotIn(self.cost.name, response.content.decode())
        self.assertIn(self.cost_2.name, response.content.decode())
        self.assertNotIn(self.test_cost.name, response.content.decode())

    def test_delete_renovation_cost_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("renovation:delete-renovation-cost",
                    args=[str(self.cost.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("renovation:delete-renovation-cost",
                    args=[str(self.cost.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("renovation:delete-renovation-cost",
                    args=[str(self.cost.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_renovation_cost_logout_if_security_breach(self):
        """Deleting renovation cost of another user is unsuccessful and
        triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(RenovationCost.objects.count(), 3)
        self.assertNotEqual(self.user, self.test_cost.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("renovation:delete-renovation-cost",
                    args=[str(self.test_cost.id)]),
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_delete,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do usunięcia tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(RenovationCost.objects.count(), 3)
