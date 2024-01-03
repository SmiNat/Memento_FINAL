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
from connection.factories import AttachmentFactory
from medical.factories import (MedCardFactory, MedicineFactory,
                               MedicalVisitFactory, HealthTestResultFactory)
from medical.forms import (MedCardForm, MedicineForm, MedicalVisitForm,
                           HealthTestResultForm)
from medical.models import MedCard, Medicine, MedicalVisit, HealthTestResult

logger = logging.getLogger("test")
User = get_user_model()


class BasicUrlsTests(TestCase):
    """Test MedCard, Medicine, MedicalVisit and HealthTestResult basic urls."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.medcard = MedCardFactory(user=self.user)
        self.medicine = MedicineFactory(user=self.user)
        self.visit = MedicalVisitFactory(user=self.user)
        self.test_result = HealthTestResultFactory(user=self.user)

        self.pages = [
            {"page": "medical:medcard",
             "args": [], "name": "medcard",
             "template": "medical/medcard.html"},
            {"page": "medical:add-medcard",
             "args": [], "name": "add-medcard",
             "template": "medical/medical_form.html"},
            {"page": "medical:edit-medcard",
             "args": [str(self.medcard.id)], "name": "edit-medcard",
             "template": "medical/medical_form.html"},
            {"page": "medical:delete-medcard",
             "args": [str(self.medcard.id)], "name": "delete-medcard",
             "template": "medical/medical_delete_form.html"},

            {"page": "medical:medicines",
             "args": [], "name": "medicines",
             "template": "medical/medical.html"},
            {"page": "medical:single-medicine",
             "args": [str(self.medicine.id)], "name": "single-medicine",
             "template": "medical/single_medical.html"},
            {"page": "medical:add-medicine",
             "args": [], "name": "add-medicine",
             "template": "medical/medical_form.html"},
            {"page": "medical:edit-medicine",
             "args": [str(self.medicine.id)], "name": 'edit-medicine',
             "template": "medical/medical_form.html"},
            {"page": "medical:delete-medicine",
             "args": [str(self.medicine.id)], "name": 'delete-medicine',
             "template": "medical/medical_delete_form.html"},

            {"page": "medical:medical-visits",
             "args": [], "name": "medical-visits",
             "template": "medical/medical.html"},
            {"page": "medical:single-visit",
             "args": [str(self.visit.id)], "name": "single-visit",
             "template": "medical/single_medical.html"},
            {"page": "medical:add-visit",
             "args": [], "name": "add-visit",
             "template": "medical/medical_form.html"},
            {"page": "medical:edit-visit",
             "args": [str(self.visit.id)], "name": 'edit-visit',
             "template": "medical/medical_form.html"},
            {"page": "medical:delete-visit",
             "args": [str(self.visit.id)], "name": 'delete-visit',
             "template": "medical/medical_delete_form.html"},

            {"page": "medical:test-results",
             "args": [], "name": "test-results",
             "template": "medical/medical.html"},
            {"page": "medical:single-test-result",
             "args": [str(self.test_result.id)], "name": "single-test-result",
             "template": "medical/single_medical.html"},
            {"page": "medical:add-test-result",
             "args": [], "name": "add-test-result",
             "template": "medical/medical_form.html"},
            {"page": "medical:edit-test-result",
             "args": [str(self.test_result.id)], "name": 'edit-test-result',
             "template": "medical/medical_form.html"},
            {"page": "medical:delete-test-result",
             "args": [str(self.test_result.id)], "name": 'delete-test-result',
             "template": "medical/medical_delete_form.html"},
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


class MedCardTests(TestCase):
    """Test MedCard views."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com", password="testpass456")
        self.medcard = MedCardFactory(user=self.user)
        self.test_medcard = MedCardFactory(
            user=self.test_user, age=45, weight=100, height=175,
            blood_type="A+", allergies=None, diseases="High blood pressure",
            permanent_medications=None, additional_medications=None,
            main_doctor="Dr Strange", emergency_contact=None)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(MedCard.objects.count(), 2)

    def test_medcard_302_redirect_if_unauthorized(self):
        """Test if medcard page is unavailable for unauthorized users."""
        response = self.client.get(reverse("medical:medcard"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_medcard_200_if_logged_in(self):
        """Test if medcard page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:medcard"))
        self.assertEqual(response_get.status_code, 200)

    def test_medcard_correct_template_if_logged_in(self):
        """Test if medcard page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:medcard"))
        self.assertTemplateUsed(response_get, "medical/medcard.html")

    def test_medcard_initial_values_set_context_data(self):
        """Test if medcard page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("medical:medcard"))
        self.assertIn(str(self.medcard), response_get.content.decode())
        self.assertEqual(response_get.context["medcard"], self.medcard)
        self.assertEqual(response_get.context["profile"],
                         self.medcard.user.profile)

    def test_medcard_initial_values_set_medcard_data(self):
        """Test if page medcard displays only data of logged user
        (without data of other users)."""

        # Test for user "johndoe123"
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:medcard"))

        self.assertIn(self.medcard.diseases, response_get.content.decode())
        self.assertNotIn(self.test_medcard.diseases, response_get.content.decode())

        self.client.logout()

        # Test for user "testuser123"
        self.client.login(username="testuser123", password="testpass456")
        response_get = self.client.get(reverse("medical:medcard"))

        self.assertNotIn(self.medcard.diseases, response_get.content.decode())
        self.assertIn(self.test_medcard.diseases, response_get.content.decode())

    def test_add_medcard_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add medcard
        (user is redirected to login page)."""
        response = self.client.get(reverse("medical:add-medcard"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_medcard_200_if_logged_in(self):
        """Test if add_medcard page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-medcard"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_medcard_correct_template_if_logged_in(self):
        """Test if add_medcard page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-medcard"))
        self.assertTemplateUsed(response_get, "medical/medical_form.html")

    def test_add_medcard_form_initial_values_set_context_data(self):
        """Test if add_medcard page displays correct context data."""
        queryset = list(HealthTestResult.objects.filter(
            user=self.user).values_list("name", "test_date"))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-medcard"))
        self.assertEqual(response_get.context["page"], "add-medcard")
        self.assertIsInstance(response_get.context["form"], MedCardForm)

    def test_add_medcard_form_initial_values_set_form_data(self):
        """Test if add_medcard page displays correct form data."""
        medcard_fields = [
            # "name", "slug",
            "age", "weight", "height", "blood_type", "allergies", "diseases",
            "permanent_medications", "additional_medications",
            "main_doctor", "other_doctors", "emergency_contact", "notes",
            "access_granted", "access_granted_medicines",
            "access_granted_test_results", "access_granted_visits",
        ]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-medcard"))
        for field in medcard_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_medcard_success_and_redirect(self):
        """Test if creating a medcard is successful (status code 200) and
        redirecting is successful (status code 302)."""

        # Deleting self.user medcard (model allows more than one medcard
        # per user (foreignkey) but view is constructed for only one medcard per user)
        self.medcard.delete()
        self.assertEqual(MedCard.objects.filter(user=self.user).count(), 0)

        payload = {
            "blood_type": "0-",
            "main_doctor": "Dr Dolittle",
            "access_granted": Access.NO_ACCESS_GRANTED,
            "access_granted_medicines": Access.NO_ACCESS_GRANTED,
            "access_granted_test_results": Access.NO_ACCESS_GRANTED,
            "access_granted_visits": Access.NO_ACCESS_GRANTED,
        }
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "medical:add-medcard"),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("medical:medcard"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano kartę medyczną.",
                      str(messages[0]))
        self.assertInHTML("Dr Dolittle",
                          response_post.content.decode())
        self.assertEqual(MedCard.objects.count(), 2)
        self.assertTrue(MedCard.objects.filter(
            user=self.user, blood_type=payload["blood_type"]).exists())

    def test_add_medcard_successful_with_correct_user(self):
        """Test if creating a medcard successfully has correct user."""
        self.medcard.delete()
        self.assertEqual(MedCard.objects.filter(user=self.user).count(), 0)
        payload = {
            "blood_type": "0-",
            "main_doctor": "ABCDEFGH",
            "access_granted": Access.NO_ACCESS_GRANTED,
            "access_granted_medicines": Access.NO_ACCESS_GRANTED,
            "access_granted_test_results": Access.NO_ACCESS_GRANTED,
            "access_granted_visits": Access.NO_ACCESS_GRANTED,
        }
        self.client.force_login(self.user)

        self.client.post(reverse("medical:add-medcard"),
                         payload, follow=True)

        medcard = MedCard.objects.get(main_doctor="ABCDEFGH")
        self.assertEqual(medcard.user, self.user)

    @parameterized.expand(
        [
            ("Empty field: access_granted_medicines",
             {"access_granted": "Brak dostępu",
              "access_granted_test_results": "Brak dostępu",
              "access_granted_visits": "Brak dostępu"},
             "To pole jest wymagane."),
            ("Empty field: access_granted",
             {"access_granted_test_results": "Brak dostępu",
              "access_granted_medicines": "Brak dostępu",
              "access_granted_visits": "Brak dostępu"},
             "To pole jest wymagane."),
            ("Empty field: access_granted_test_results",
             {"access_granted": "Brak dostępu",
              "access_granted_medicines": "Brak dostępu",
              "access_granted_visits": "Brak dostępu"},
             "To pole jest wymagane."),
            ("Empty field: access_granted_visits",
             {"access_granted": "Brak dostępu",
              "access_granted_test_results": "Brak dostępu",
              "access_granted_medicines": "Brak dostępu"},
             "To pole jest wymagane."),
        ]
    )
    def test_add_medcard_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a medcard is not successful if data is incorrect."""
        self.client.force_login(self.user)
        response_post = self.client.post(
            reverse("medical:add-medcard"), payload)
        self.assertEqual(MedCard.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_medcard_302_redirect_if_unauthorized(self):
        """Test if edit_medcard page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("medical:edit-medcard", args=[self.medcard.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_medcard_200_if_logged_in(self):
        """Test if edit_medcard page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:edit-medcard", args=[self.medcard.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_medcard_correct_template_if_logged_in(self):
        """Test if edit_medcard page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:edit-medcard", args=[self.medcard.id]))
        self.assertTemplateUsed(response_get, "medical/medical_form.html")

    def test_edit_medcard_form_initial_values_set_context_data(self):
        """Test if edit_medcard page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:edit-medcard", args=[str(self.medcard.id)]))
        self.assertEqual(response_get.context["page"], "edit-medcard")
        self.assertEqual(response_get.context["medcard"], self.medcard)
        self.assertIsInstance(response_get.context["form"], MedCardForm)

    def test_edit_medcard_form_initial_values_set_form_data(self):
        """Test if edit_medcard page displays correct form data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:edit-medcard",
                    args=[str(self.medcard.id)]))
        self.assertIn(self.medcard.blood_type, response_get.content.decode())
        self.assertIn(self.medcard.main_doctor, response_get.content.decode())

    def test_edit_medcard_success_and_redirect(self):
        """Test if updating a medcard is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        medcard = self.medcard

        payload = {
            "age": medcard.age,
            "weight": medcard.weight,
            "height": medcard.height,
            "blood_type": "AB+",
            "allergies": "sun",
            "diseases": "diabetic",
            "permanent_medications": "glucophage 750",
            "additional_medications": medcard.additional_medications,
            "main_doctor": medcard.main_doctor,
            "other_doctors": medcard.other_doctors,
            "emergency_contact": medcard.emergency_contact,
            "notes": "eat more fruits",
            "access_granted": medcard.access_granted,
            "access_granted_medicines": medcard.access_granted_medicines,
            "access_granted_test_results": medcard.access_granted_test_results,
            "access_granted_visits": medcard.access_granted_visits,
        }
        self.assertNotEqual(medcard.blood_type, payload["blood_type"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("medical:edit-medcard",
                    args=[str(self.medcard.id)]),
            data=payload,
            instance=medcard,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("medical:medcard"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano kartę medyczną.", str(messages[0]))
        medcard.refresh_from_db()
        self.assertEqual(MedCard.objects.count(), 2)
        self.assertEqual(medcard.blood_type, payload["blood_type"])

    def test_edit_medcard_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        medcard = self.medcard
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "blood_type": "AB+",
            "access_granted": Access.NO_ACCESS_GRANTED,
            "access_granted_test_results": Access.NO_ACCESS_GRANTED,
            "access_granted_medicines": Access.NO_ACCESS_GRANTED,
            "access_granted_visits": Access.NO_ACCESS_GRANTED,
        }
        response_patch = self.client.patch(
            reverse("medical:edit-medcard",
                    args=[str(self.medcard.id)]),
            data=payload,
            instance=medcard,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "age": medcard.age,
            "weight": medcard.weight,
            "height": medcard.height,
            "blood_type": "0+",
            "allergies": None,
            "diseases": None,
            "permanent_medications": None,
            "additional_medications": medcard.additional_medications,
            "main_doctor": medcard.main_doctor,
            "other_doctors": medcard.other_doctors,
            "emergency_contact": medcard.emergency_contact,
            "notes": "Invalid data",
            "access_granted": medcard.access_granted,
            "access_granted_medicines": medcard.access_granted_medicines,
            "access_granted_test_results": medcard.access_granted_test_results,
            "access_granted_visits": medcard.access_granted_visits,
        }
        response_put = self.client.put(
            reverse("medical:edit-medcard",
                    args=[str(self.medcard.id)]),
            data=payload,
            instance=medcard,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("medical:edit-medcard",
                    args=[str(self.medcard.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_medcard_logout_if_security_breach(self):
        """Editing medcard of another user is unsuccessful and triggers logout."""
        test_medcard = self.test_medcard

        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_medcard.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "age": test_medcard.age,
            "weight": test_medcard.weight,
            "height": test_medcard.height,
            "blood_type": "0+",
            "allergies": "SECURITY BREACH",
            "diseases": None,
            "permanent_medications": None,
            "additional_medications": test_medcard.additional_medications,
            "main_doctor": "SECURITY BREACH",
            "other_doctors": test_medcard.other_doctors,
            "emergency_contact": test_medcard.emergency_contact,
            "notes": "SECURITY BREACH",
            "access_granted": test_medcard.access_granted,
            "access_granted_medicines": test_medcard.access_granted_medicines,
            "access_granted_test_results": test_medcard.access_granted_test_results,
            "access_granted_visits": test_medcard.access_granted_visits,
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("medical:edit-medcard",
                    args=[str(self.test_medcard.id)]),
            data=payload,
            content_type="text/html",
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
        self.assertEqual(MedCard.objects.count(), 2)
        self.assertNotIn(test_medcard.notes, payload["notes"])

    def test_delete_medcard_302_redirect_if_unauthorized(self):
        """Test if delete_medcard page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("medical:delete-medcard", args=[self.medcard.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_medcard_200_if_logged_in(self):
        """Test if delete_medcard page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response = self.client.get(reverse(
            "medical:delete-medcard", args=[str(self.medcard.id)]))
        self.assertEqual(response.status_code, 200)

    def test_delete_medcard_correct_template_if_logged_in(self):
        """Test if delete_medcard page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response = self.client.get(reverse(
            "medical:delete-medcard", args=[str(self.medcard.id)]))
        self.assertTemplateUsed(response,
                                template_name="medical/medical_delete_form.html")

    def test_delete_medcard_initial_values_set_context_data(self):
        """Test if delete_medcard page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(reverse(
            "medical:delete-medcard", args=[str(self.medcard.id)]))
        self.assertIn(str(self.medcard), response_get.content.decode())
        self.assertEqual(response_get.context["medcard"], self.medcard)
        self.assertEqual(response_get.context["page"], "delete-medcard")

    def test_delete_medcard_and_redirect(self):
        """Deleting medcard is successful (status code 200) and redirect
        is successful (status code 302)."""
        medcard = self.medcard
        self.assertEqual(MedCard.objects.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(reverse("medical:medcard"))
        self.assertIn(str(medcard.age), response.content.decode())

        response_delete = self.client.post(
            reverse("medical:delete-medcard", args=[str(self.medcard.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("medical:medcard"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto kartę medyczną.", str(messages[0]))

        response = self.client.get(reverse("medical:medcard"))
        self.assertEqual(MedCard.objects.count(), 1)
        self.assertNotIn(self.medcard.blood_type, response.content.decode())
        self.assertNotIn(self.test_medcard.blood_type, response.content.decode())

    def test_delete_medcard_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("medical:delete-medcard",
                    args=[str(self.medcard.id)]),
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("medical:delete-medcard",
                    args=[str(self.medcard.id)]),
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("medical:delete-medcard",
                    args=[str(self.medcard.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_medcard_logout_if_security_breach(self):
        """Deleting medcard of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(MedCard.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_medcard.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("medical:delete-medcard",
                    args=[str(self.test_medcard.id)]),
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
        self.assertEqual(MedCard.objects.count(), 2)


class MedicineTests(TestCase):
    """Test Medicine views."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.medicine = MedicineFactory(user=self.user, drug_name_and_dose="setup drug")

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com", password="testpass456")
        self.test_medicine = MedicineFactory(
            user=self.test_user, drug_name_and_dose="test drug", notes="test notes")

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Medicine.objects.count(), 2)

    def test_medicines_302_redirect_if_unauthorized(self):
        """Test if medicines page is unavailable for unauthorized users."""
        response = self.client.get(reverse("medical:medicines"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_medicines_200_if_logged_in(self):
        """Test if medicines page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:medicines"))
        self.assertEqual(response_get.status_code, 200)

    def test_medicines_correct_template_if_logged_in(self):
        """Test if medicines page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:medicines"))
        self.assertTemplateUsed(response_get, "medical/medical.html")

    def test_medicines_initial_values_set_context_data(self):
        """Test if medicines page displays correct context data."""
        MedCardFactory(user=self.user)
        medicines = Medicine.objects.filter(user=self.user).order_by("-updated")
        medcard = MedCard.objects.get(user=self.user)
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("medical:medicines"))
        self.assertIn(str(self.medicine), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "medicines-page")
        self.assertQuerysetEqual(response_get.context["medicines"], medicines)
        self.assertEqual(response_get.context["medcard"], medcard)
        self.assertEqual(response_get.context["profile"],
                         self.medicine.user.profile)

    def test_medicines_initial_values_set_medicines_data(self):
        """Test if page medicines displays only medicines of logged user
        (without medicines of other users)."""
        new_user = MedicineFactory(user=self.user, drug_name_and_dose="new drug")

        # Test for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("medical:medicines"))

        self.assertIn(self.medicine.drug_name_and_dose, response_get.content.decode())
        self.assertIn(new_user.drug_name_and_dose, response_get.content.decode())
        self.assertNotIn(self.test_medicine.drug_name_and_dose, response_get.content.decode())

        self.client.logout()

        # Test for user "testuser123"
        self.client.login(username="testuser123", password="testpass456")
        response_get = self.client.get(reverse("medical:medicines"))

        self.assertNotIn(self.medicine.drug_name_and_dose, response_get.content.decode())
        self.assertNotIn(new_user.drug_name_and_dose, response_get.content.decode())
        self.assertIn(self.test_medicine.drug_name_and_dose, response_get.content.decode())

    def test_single_medicine_302_redirect_if_unauthorized(self):
        """ Test if single_medicine page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("medical:single-medicine", args=[self.medicine.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    def test_single_medicine_200_if_logged_in(self):
        """Test if single_medicine page return status code 200 for
        authenticated user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:single-medicine", args=[self.medicine.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_single_medicine_correct_template_if_logged_in(self):
        """Test if single_medicine page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:single-medicine", args=[self.medicine.id]))
        self.assertTemplateUsed(
            response_get, "medical/single_medical.html")

    def test_single_medicine_initial_values_set_context_data(self):
        """Test if single_medicine page displays correct context data."""
        MedCardFactory(user=self.user)
        medcard = MedCard.objects.get(user=self.user)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-medicine", args=[str(self.medicine.id)]))
        self.assertIn(str(self.medicine), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "single-medicine")
        self.assertEqual(response_get.context["medicine"], self.medicine)
        self.assertEqual(response_get.context["medcard"], medcard)
        self.assertEqual(response_get.context["profile"], self.medicine.user.profile)

    def test_single_medicine_initial_values_set_medicine_data(self):
        """Test if single_medicine page displays correct medicine data
        (only data of logged user)."""
        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-medicine", args=[self.medicine.id]))

        self.assertIn(self.medicine.drug_name_and_dose, response_get.content.decode())
        self.assertNotIn(self.test_medicine.drug_name_and_dose, response_get.content.decode())
        self.assertIn(self.medicine.notes, response_get.content.decode())
        self.assertNotIn(self.test_medicine.notes, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("medical:single-medicine", args=[self.test_medicine.id]))

        self.assertIn(self.test_medicine.drug_name_and_dose, response_get.content.decode())
        self.assertNotIn(self.medicine.drug_name_and_dose, response_get.content.decode())
        self.assertIn(self.test_medicine.notes, response_get.content.decode())
        self.assertNotIn(self.medicine.notes, response_get.content.decode())

    def test_single_medicine_forced_logout_if_security_breach(self):
        """Attempt to overview medicine of another user is forbidden and
        triggers logout."""

        # Attempt to see self.test_user data by self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("medical:single-medicine",
                    args=[self.test_medicine.id]), follow=True)
        self.assertIn(self.test_medicine.drug_name_and_dose,
                      response_get.content.decode())
        self.client.logout()

        # Attempt to see self.test_user data by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-medicine",
                    args=[self.test_medicine.id]), follow=True)
        self.assertNotIn(self.test_medicine.drug_name_and_dose,
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

    def test_add_medicine_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add medicine
        (user is redirected to login page)."""
        response = self.client.get(reverse("medical:add-medicine"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_medicine_200_if_logged_in(self):
        """Test if add_medicine page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-medicine"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_medicine_correct_template_if_logged_in(self):
        """Test if add_medicine page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-medicine"))
        self.assertTemplateUsed(response_get, "medical/medical_form.html")

    def test_add_medicine_form_initial_values_set_context_data(self):
        """Test if add_medicine page displays correct context data."""
        drug_names = list(Medicine.objects.filter(
            user=self.user).values_list("drug_name_and_dose", flat=True))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-medicine"))
        self.assertEqual(response_get.context["page"], "add-medicine")
        self.assertQuerysetEqual(response_get.context["drug_names"], drug_names)
        self.assertIsInstance(response_get.context["form"], MedicineForm)

    def test_add_medicine_form_initial_values_set_form_data(self):
        """Test if add_medicine page displays correct form data."""
        medicine_fields = ["drug_name_and_dose", "daily_quantity",
                           "disease", "medication_frequency", "medication_days",
                           "exact_frequency", "medication_hours", "start_date",
                           "end_date", "notes"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-medicine"))
        for field in medicine_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_medicine_success_and_redirect(self):
        """Test if creating a medicine is successful (status code 200) and
        redirecting is successful (status code 302)."""
        payload = {
            "drug_name_and_dose": "Brand new drug name",
            "daily_quantity": 2,
        }
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "medical:add-medicine"),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("medical:medicines"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano lek do bazy danych.",
                      str(messages[0]))
        self.assertInHTML("Brand new drug name",
                          response_post.content.decode())
        self.assertEqual(Medicine.objects.count(), 3)
        self.assertTrue(Medicine.objects.filter(
            user=self.user, drug_name_and_dose=payload["drug_name_and_dose"]).exists())

    def test_add_medicine_successful_with_correct_user(self):
        """Test if creating a medicine successfully has correct user."""
        drug_names = list(Medicine.objects.filter(
            user=self.user).values_list("drug_name_and_dose", flat=True))
        payload = {
            "drug_name_and_dose": "New drug for user test",
            "daily_quantity": 2,
        }
        self.client.force_login(self.user)
        self.client.post(reverse("medical:add-medicine"),
                         payload,
                         drug_names=drug_names,
                         follow=True)
        medicine = Medicine.objects.get(drug_name_and_dose=payload["drug_name_and_dose"])
        self.assertEqual(medicine.user, self.user)

    @parameterized.expand(
        [
            ("Empty field: drug_name_and_dose",
             {"daily_quantity": 3},
             "To pole jest wymagane."),
            ("Empty field: daily_quantity",
             {"drug_name_and_dose": "Some drug"},
             "To pole jest wymagane."),
            ("Not unique field: drug_name_and_dose",
             {"drug_name_and_dose": "setup drug", "daily_quantity": 1},
             "Istnieje już lek o podanej nazwie w bazie danych."),
            ("Incorrect date field",
             {"drug_name_and_dose": "new drug name", "daily_quantity": 1,
              "start_date": "2020/1/1"},
             "Wpisz poprawną datę."),
            ("End date before start date",
             {"drug_name_and_dose": "new drug name", "daily_quantity": 1,
              "start_date": datetime.date(2020, 2, 2),
              "end_date": datetime.date(2020, 1, 1)},
             "Data zakończenia przyjmowania leku nie może przypadać "
             "wcześniej niż data rozpoczęcia przyjmowania leku"),
            ("Incorrect medication_hours field",
             {"drug_name_and_dose": "new drug name", "daily_quantity": 1,
              "medication_hours": "8,11"},
             "Wystąpił błąd podczas zapisu formularza. Sprawdź poprawność danych."),
            ("Incorrect daily_quantity field - negative value is not allowed",
             {"drug_name_and_dose": "new drug name", "daily_quantity": -2},
             "Wartość nie może być liczbą ujemną."),
        ]
    )
    def test_add_medicine_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a medicine is not successful if data is incorrect."""
        self.client.force_login(self.user)
        drug_names = list(Medicine.objects.filter(
            user=self.medicine.user).values_list(
            "drug_name_and_dose", flat=True))
        response_post = self.client.post(
            reverse("medical:add-medicine"), payload, drug_names=drug_names)
        self.assertEqual(Medicine.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_medicine_302_redirect_if_unauthorized(self):
        """Test if edit_medicine page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("medical:edit-medicine", args=[self.medicine.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_medicine_200_if_logged_in(self):
        """Test if edit_medicine page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:edit-medicine", args=[self.medicine.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_medicine_correct_template_if_logged_in(self):
        """Test if edit_medicine page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:edit-medicine", args=[self.medicine.id]))
        self.assertTemplateUsed(response_get, "medical/medical_form.html")

    def test_edit_medicine_form_initial_values_context_data(self):
        """Test if edit_medicine page displays correct context data."""
        drug_names = list(Medicine.objects.filter(
            user=self.user).exclude(id=self.medicine.id).values_list(
            "drug_name_and_dose", flat=True))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:edit-medicine", args=[str(self.medicine.id)]))
        self.assertQuerysetEqual(response_get.context["drug_names"], drug_names)
        self.assertEqual(response_get.context["page"], "edit-medicine")
        self.assertEqual(response_get.context["medicine"], self.medicine)
        self.assertIsInstance(response_get.context["form"], MedicineForm)

    def test_edit_medicine_form_initial_values_set_form_data(self):
        """Test if edit_medicine page displays correct form data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:edit-medicine", args=[str(self.medicine.id)]))
        self.assertIn(self.medicine.notes, response_get.content.decode())
        self.assertIn(self.medicine.drug_name_and_dose,
                      response_get.content.decode())

    def test_edit_medicine_success_and_redirect(self):
        """Test if updating a medicine is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        drug_names = list(Medicine.objects.filter(
            user=self.user).exclude(
            id=self.medicine.id).values_list("drug_name_and_dose", flat=True))

        payload = {
            "drug_name_and_dose": self.medicine.drug_name_and_dose,
            "daily_quantity": self.medicine.daily_quantity,
            "medication_days": ["Poniedziałek", "Piątek"],
            "medication_frequency": self.medicine.medication_frequency,
            "exact_frequency": self.medicine.exact_frequency,
            "medication_hours": ["8:00", "20:00"],
            "start_date": self.medicine.end_date,
            "end_date": self.medicine.end_date,
            "disease": self.medicine.disease,
            "notes": "New med for new disease",
        }
        self.assertNotEqual(self.medicine.notes, payload["notes"])
        self.assertNotEqual(self.medicine.medication_days, payload["medication_days"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("medical:edit-medicine",
                    args=[str(self.medicine.id)]),
            data=payload,
            instance=self.medicine,
            drug_names=drug_names,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("medical:single-medicine", args=[str(self.medicine.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano informacje o leku.", str(messages[0]))
        self.medicine.refresh_from_db()
        self.assertEqual(Medicine.objects.count(), 2)
        self.assertEqual(self.medicine.notes, payload["notes"])

    def test_edit_medicine_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        drug_names = list(Medicine.objects.filter(
            user=self.user).exclude(
            id=self.medicine.id).values_list("drug_name_and_dose", flat=True))
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "drug_name_and_dose": "New name as update",
            "daily_quantity": 5
        }
        response_patch = self.client.patch(
            reverse("medical:edit-medicine",
                    args=[str(self.medicine.id)]),
            data=payload,
            instance=self.medicine,
            drug_names=drug_names,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "drug_name_and_dose": self.medicine.drug_name_and_dose,
            "daily_quantity": self.medicine.daily_quantity,
            "medication_days": ["Poniedziałek", "Piątek"],
            "medication_frequency": self.medicine.medication_frequency,
            "exact_frequency": self.medicine.exact_frequency,
            "medication_hours": self.medicine.medication_hours,
            "start_date": self.medicine.end_date,
            "end_date": self.medicine.end_date,
            "disease": self.medicine.disease,
            "notes": "New med for new disease",
        }
        response_put = self.client.put(
            reverse("medical:edit-medicine",
                    args=[str(self.medicine.id)]),
            data=payload,
            instance=self.medicine,
            drug_names=drug_names,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("medical:edit-medicine",
                    args=[str(self.medicine.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_medicine_logout_if_security_breach(self):
        """Editing medicine of another user is unsuccessful and triggers logout."""
        drug_names = list(Medicine.objects.filter(
            user=self.user).exclude(
            id=self.test_medicine.id).values_list("drug_name_and_dose", flat=True))

        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_medicine.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "drug_name_and_dose": "SECURITY BREACH",
            "daily_quantity": 666,
            "medication_days": self.medicine.medication_days,
            "medication_frequency": self.medicine.medication_frequency,
            "exact_frequency": self.medicine.exact_frequency,
            "medication_hours": self.medicine.medication_hours,
            "start_date": self.medicine.end_date,
            "end_date": self.medicine.end_date,
            "disease": self.medicine.disease,
            "notes": "SECURITY BREACH",
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("medical:edit-medicine",
                    args=[str(self.test_medicine.id)]),
            data=payload,
            content_type="text/html",
            drug_names=drug_names,
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
        self.assertEqual(Medicine.objects.count(), 2)
        self.assertNotIn(self.test_medicine.drug_name_and_dose, payload["drug_name_and_dose"])

    def test_delete_medicine_302_redirect_if_unauthorized(self):
        """Test if delete_medicine page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("medical:delete-medicine", args=[self.medicine.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_medicine_200_if_logged_in(self):
        """Test if delete_medicine page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response = self.client.get(reverse(
            "medical:delete-medicine", args=[str(self.medicine.id)]))
        self.assertEqual(response.status_code, 200)

    def test_delete_medicine_result_correct_template_if_logged_in(self):
        """Test if delete_medicine page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response = self.client.get(reverse(
            "medical:delete-medicine", args=[str(self.medicine.id)]))
        self.assertTemplateUsed(response,
                                template_name="medical/medical_delete_form.html")

    def test_delete_medicine_initial_values_set_context_data(self):
        """Test if delete_medicine page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(reverse(
            "medical:delete-medicine", args=[str(self.medicine.id)]))
        self.assertIn(str(self.medicine.drug_name_and_dose), response_get.content.decode())
        self.assertEqual(response_get.context["medicine"], self.medicine)
        self.assertEqual(response_get.context["page"], "delete-medicine")

    def test_delete_medicine_success_and_redirect(self):
        """Deleting medicine is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(Medicine.objects.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(reverse("medical:medicines"))
        self.assertIn(str(self.medicine), response.content.decode())

        response_delete = self.client.post(
            reverse("medical:delete-medicine", args=[str(self.medicine.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("medical:medicines"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto lek z bazy danych.", str(messages[0]))

        response = self.client.get(reverse("medical:medicines"))
        self.assertEqual(Medicine.objects.count(), 1)
        self.assertNotIn(self.medicine.drug_name_and_dose, response.content.decode())
        self.assertNotIn(self.test_medicine.drug_name_and_dose, response.content.decode())

    def test_delete_medicine_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("medical:delete-medicine",
                    args=[str(self.medicine.id)]),
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("medical:delete-medicine",
                    args=[str(self.medicine.id)]),
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("medical:delete-medicine",
                    args=[str(self.medicine.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_medicine_logout_if_security_breach(self):
        """Deleting medicine of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(Medicine.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_medicine.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("medical:delete-medicine",
                    args=[str(self.test_medicine.id)]),
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
        self.assertEqual(Medicine.objects.count(), 2)


class MedicalVisitTests(TestCase):
    """Test MedicalVisit views."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.visit = MedicalVisitFactory(
            user=self.user, specialization="setup dr", notes="setup notes")

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com", password="testpass456")
        self.test_visit = MedicalVisitFactory(
            user=self.test_user, specialization="test dr", notes="test notes")

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(MedicalVisit.objects.count(), 2)

    def test_medical_visits_302_redirect_if_unauthorized(self):
        """Test if medical_visits page is unavailable for unauthorized users."""
        response = self.client.get(reverse("medical:medical-visits"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_medical_visits_200_if_logged_in(self):
        """Test if medical_visits page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:medical-visits"))
        self.assertEqual(response_get.status_code, 200)

    def test_medical_visits_correct_template_if_logged_in(self):
        """Test if medical_visits page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:medical-visits"))
        self.assertTemplateUsed(response_get, "medical/medical.html")

    def test_medical_visits_initial_values_set_context_data(self):
        """Test if medical_visits page displays correct context data."""
        MedCardFactory(user=self.user)
        visits = MedicalVisit.objects.filter(user=self.user).order_by("-updated")
        medcard = MedCard.objects.get(user=self.user)
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("medical:medical-visits"))
        self.assertIn(str(self.visit.specialization), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "medical-visits-page")
        self.assertQuerysetEqual(response_get.context["visits"], visits)
        self.assertEqual(response_get.context["medcard"], medcard)
        self.assertEqual(response_get.context["profile"],
                         self.visit.user.profile)

    def test_medical_visits_initial_values_set_medical_visits_data(self):
        """Test if page medical_visits displays only medical_visits of logged user
        (without medical_visits of other users)."""
        new_user = MedicalVisitFactory(user=self.user, specialization="new dr")

        # Test for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("medical:medical-visits"))

        self.assertIn(self.visit.specialization, response_get.content.decode())
        self.assertIn(new_user.specialization, response_get.content.decode())
        self.assertNotIn(self.test_visit.specialization, response_get.content.decode())

        self.client.logout()

        # Test for user self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("medical:medical-visits"))

        self.assertNotIn(self.visit.specialization, response_get.content.decode())
        self.assertNotIn(new_user.specialization, response_get.content.decode())
        self.assertIn(self.test_visit.specialization, response_get.content.decode())

    def test_single_visit_302_redirect_if_unauthorized(self):
        """ Test if single_visit page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("medical:single-visit", args=[self.visit.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    def test_single_visit_200_if_logged_in(self):
        """Test if single_visit page return status code 200 for
        authenticated user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:single-visit", args=[self.visit.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_single_visit_correct_template_if_logged_in(self):
        """Test if single_visit page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:single-visit", args=[self.visit.id]))
        self.assertTemplateUsed(
            response_get, "medical/single_medical.html")

    def test_single_visit_initial_values_set_context_data(self):
        """Test if single_visit page displays correct context data."""
        MedCardFactory(user=self.user)
        medcard = MedCard.objects.get(user=self.user)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-visit", args=[str(self.visit.id)]))
        self.assertIn(str(self.visit.specialization), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "single-visit")
        self.assertEqual(response_get.context["visit"], self.visit)
        self.assertEqual(response_get.context["medcard"], medcard)
        self.assertEqual(response_get.context["profile"], self.visit.user.profile)

    def test_single_visit_initial_values_set_renovation_data(self):
        """Test if single_visit page displays correct visit data
        (only data of logged user)."""

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-visit", args=[self.visit.id]))

        self.assertIn(self.visit.specialization, response_get.content.decode())
        self.assertNotIn(self.test_visit.specialization, response_get.content.decode())
        self.assertIn(self.visit.notes, response_get.content.decode())
        self.assertNotIn(self.test_visit.notes, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("medical:single-visit", args=[self.test_visit.id]))

        self.assertIn(self.test_visit.specialization, response_get.content.decode())
        self.assertNotIn(self.visit.specialization, response_get.content.decode())
        self.assertIn(self.test_visit.notes, response_get.content.decode())
        self.assertNotIn(self.visit.notes, response_get.content.decode())

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_single_visit_initial_values_set_attachments(self):
        """Test if single_visit page displays correct attachments
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
        self.attachment.medical_visits.add(self.visit)
        self.test_attachment.medical_visits.add(self.test_visit)

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-visit", args=[self.visit.id]))

        self.assertEqual(response_get.context["attachments"][0], self.attachment)

        self.assertIn(self.visit.specialization, response_get.content.decode())
        self.assertNotIn(self.test_visit.specialization, response_get.content.decode())
        self.assertIn(self.visit.notes, response_get.content.decode())
        self.assertNotIn(self.test_visit.notes, response_get.content.decode())
        self.assertIn(self.attachment.attachment_name,
                      response_get.content.decode())
        self.assertNotIn(self.test_attachment.attachment_name,
                         response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("medical:single-visit", args=[self.test_visit.id]))

        self.assertEqual(response_get.context["attachments"][0], self.test_attachment)

        self.assertIn(self.test_visit.specialization, response_get.content.decode())
        self.assertNotIn(self.visit.specialization, response_get.content.decode())
        self.assertIn(self.test_visit.notes, response_get.content.decode())
        self.assertNotIn(self.visit.notes, response_get.content.decode())
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

    def test_single_visit_forced_logout_if_security_breach(self):
        """Attempt to overview single visit of another user is forbidden and
        triggers logout."""

        # Attempt to see self.test_user data by self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("medical:single-visit",
                    args=[self.test_visit.id]), follow=True)
        self.assertIn(self.test_visit.specialization,
                      response_get.content.decode())
        self.client.logout()

        # Attempt to see self.test_user data by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-visit",
                    args=[self.test_visit.id]), follow=True)
        self.assertNotIn(self.test_visit.specialization,
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

    def test_add_visit_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add visit
        (user is redirected to login page)."""
        response = self.client.get(reverse("medical:add-visit"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_visit_200_if_logged_in(self):
        """Test if add_visit page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-visit"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_visit_correct_template_if_logged_in(self):
        """Test if add_visit page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-visit"))
        self.assertTemplateUsed(response_get, "medical/medical_form.html")

    def test_add_visit_form_initial_values_set_context_data(self):
        """Test if add_visit page displays correct context data."""
        queryset = list(MedicalVisit.objects.filter(user=self.user).values(
            "specialization", "visit_date", "visit_time"))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-visit"))
        self.assertEqual(response_get.context["page"], "add-visit-page")
        self.assertEqual(response_get.context["profile"], self.visit.user.profile)
        self.assertQuerysetEqual(response_get.context["queryset"], queryset)
        self.assertIsInstance(response_get.context["form"], MedicalVisitForm)

    def test_add_visit_form_initial_values_set_form_data(self):
        """Test if add_visit page displays correct form data."""
        visit_fields = ["specialization", "doctor", "visit_date", "visit_time",
                        "visit_location", "notes"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-visit"))
        for field in visit_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_visit_success_and_redirect(self):
        """Test if creating a visit is successful (status code 200) and
        redirecting is successful (status code 302)."""
        payload = {
            "specialization": "Family med",
            "visit_time": "9:20",
            "visit_date": datetime.date(2020, 12, 10),
            "notes": "private visit",
        }
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "medical:add-visit"),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("medical:medical-visits"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano wizytę.",
                      str(messages[0]))
        self.assertInHTML("Family med",
                          response_post.content.decode())
        self.assertEqual(MedicalVisit.objects.count(), 3)
        self.assertTrue(MedicalVisit.objects.filter(
            user=self.user, specialization=payload["specialization"]).exists())

    def test_add_visit_successful_with_correct_user(self):
        """Test if creating a visit successfully has correct user."""
        queryset = list(MedicalVisit.objects.filter(
            user=self.user).values_list(
            "specialization", "visit_date", "visit_time", flat=False))

        payload = {
            "specialization": "Visit to test user",
            "visit_time": "9:20",
            "visit_date": datetime.date(2020, 12, 10),
            "notes": "private visit",
        }
        self.client.force_login(self.user)

        self.client.post(reverse("medical:add-visit"),
                         payload,
                         queryset=queryset,
                         follow=True)

        visit = MedicalVisit.objects.filter(specialization=payload["specialization"])
        self.assertEqual(visit[0].user, self.user)

    def test_add_visit_successful_with_correct_specialization(self):
        """Test if creating a visit successfully has correct specialization
        (capitalize)."""
        self.assertEqual(MedicalVisit.objects.count(), 2)
        queryset = list(MedicalVisit.objects.filter(
            user=self.user).values_list(
            "specialization", "visit_date", "visit_time", flat=False))

        payload = {
            "specialization": "urologist",
            "visit_time": "9:20",
            "visit_date": datetime.date(2020, 12, 10),
            "notes": "test for name of visit",
        }
        self.client.force_login(self.user)

        self.client.post(reverse("medical:add-visit"),
                         payload,
                         queryset=queryset,
                         follow=True)

        self.assertEqual(MedicalVisit.objects.count(), 3)

        visit = MedicalVisit.objects.get(notes=payload["notes"])

        self.assertEqual(visit.specialization, "Urologist")
        self.assertNotEqual(visit.specialization, "urologist")

    @parameterized.expand(
        [
            ("Empty field: specialization",
             {"doctor": "dr Who", "visit_date": datetime.date(2020, 10, 10),
              "visit_time": "9:20"},
             "To pole jest wymagane."),
            ("Not unique fields (unique together): "
             "specialization, visit_date, visit_time",
             {"specialization": "setup dr", "visit_time": "9:20",
              "visit_date": datetime.date(2020, 10, 10)},
             "Istnieje już wizyta u tego specjalisty w danym dniu "
             "i o wskazanej godzinie."),
            ("Incorrect date field",
             {"specialization": "new name", "visit_date": "2020/1/1",
              "visit_time": "9:20"},
             "Wpisz poprawną datę."),
            ("Incorrect time field",
             {"specialization": "new name", "visit_time": "11,11",
              "visit_date": datetime.date(2020, 10, 10)},
             "Wpisz poprawną godzinę."),
        ]
    )
    def test_add_visit_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a visit is not successful if data is incorrect."""
        self.client.force_login(self.user)
        queryset = list(MedicalVisit.objects.filter(
            user=self.visit.user).values_list(
            "specialization", "visit_date", "visit_time",
            flat=False))
        response_post = self.client.post(
            reverse("medical:add-visit"), payload, queryset=queryset)
        self.assertEqual(MedicalVisit.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_visit_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot edit visit
        (user is redirected to login page)."""
        response = self.client.get(
            reverse("medical:edit-visit", args=[self.visit.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_visit_200_if_logged_in(self):
        """Test if edit_visit page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:edit-visit", args=[self.visit.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_visit_correct_template_if_logged_in(self):
        """Test if edit_visit page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:edit-visit", args=[self.visit.id]))
        self.assertTemplateUsed(response_get, "medical/medical_form.html")

    def test_edit_visit_form_initial_values_set_context_data(self):
        """Test if edit_visit page displays correct context data."""
        queryset = list(MedicalVisit.objects.filter(
            user=self.user).exclude(id=self.visit.id).values_list(
            "specialization", "visit_date", "visit_time", flat=False))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:edit-visit", args=[str(self.visit.id)]))
        self.assertEqual(response_get.context["page"], "edit-visit-page")
        self.assertEqual(response_get.context["visit"], self.visit)
        self.assertQuerysetEqual(response_get.context["queryset"], queryset)
        self.assertIsInstance(response_get.context["form"], MedicalVisitForm)

    def test_edit_visit_form_initial_values_set_form_data(self):
        """Test if edit_visit page displays correct form data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:edit-visit", args=[str(self.visit.id)]))
        self.assertIn(self.visit.notes, response_get.content.decode())
        self.assertIn(self.visit.specialization, response_get.content.decode())

    def test_edit_visit_success_and_redirect(self):
        """Test if updating a visit is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        queryset = list(MedicalVisit.objects.filter(
            user=self.user).exclude(
            id=self.visit.id).values_list(
            "specialization", "visit_date", "visit_time", flat=False))

        payload = {
            "specialization": "yet another one",
            "doctor": self.visit.doctor,
            "visit_date": self.visit.visit_date,
            "visit_time": self.visit.visit_time,
            "visit_location": self.visit.visit_location,
            "notes": "New visit for new disease",
        }
        self.assertNotEqual(self.visit.notes, payload["notes"])
        self.assertNotEqual(self.visit.specialization, payload["specialization"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("medical:edit-visit",
                    args=[str(self.visit.id)]),
            data=payload,
            instance=self.visit,
            queryset=queryset,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("medical:medical-visits"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano wizytę.", str(messages[0]))
        self.visit.refresh_from_db()
        self.assertEqual(MedicalVisit.objects.count(), 2)
        self.assertEqual(self.visit.specialization,
                         payload["specialization"].capitalize())
        self.assertEqual(self.visit.notes, payload["notes"])

    def test_edit_visit_success_and_redirect_with_correct_specialization(self):
        """Test if successfully updating a visit has correct specialization
        (capitalize)."""
        queryset = list(MedicalVisit.objects.filter(
            user=self.user).exclude(
            id=self.visit.id).values_list(
            "specialization", "visit_date", "visit_time", flat=False))

        payload = {
            "specialization": "is capitalize",
            "doctor": self.visit.doctor,
            "visit_date": self.visit.visit_date,
            "visit_time": self.visit.visit_time,
            "visit_location": self.visit.visit_location,
            "notes": self.visit.notes,
        }
        self.assertNotEqual(self.visit.specialization, payload["specialization"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("medical:edit-visit",
                    args=[str(self.visit.id)]),
            data=payload,
            instance=self.visit,
            queryset=queryset,
            follow=True
        )

        self.visit.refresh_from_db()
        self.assertEqual(MedicalVisit.objects.count(), 2)
        self.assertEqual(self.visit.specialization,
                         payload["specialization"].capitalize())
        self.assertNotEqual(self.visit.specialization, payload["specialization"])

    def test_edit_visit_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)
        queryset = list(MedicalVisit.objects.filter(
            user=self.user).exclude(
            id=self.visit.id).values_list(
            "specialization", "visit_date", "visit_time", flat=False))

        # PATCH
        payload = {
            "specialization": "New update 123",
            "visit_date": datetime.date(2020, 1, 3),
            "visit_time": self.visit.visit_time,
        }
        response_patch = self.client.patch(
            reverse("medical:edit-visit",
                    args=[str(self.visit.id)]),
            data=payload,
            instance=self.visit,
            queryset=queryset,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "specialization": "yet another one",
            "doctor": self.visit.doctor,
            "visit_date": self.visit.visit_date,
            "visit_time": self.visit.visit_time,
            "visit_location": self.visit.visit_location,
            "notes": "New visit for new disease",
        }
        response_put = self.client.put(
            reverse("medical:edit-visit",
                    args=[str(self.visit.id)]),
            data=payload,
            instance=self.visit,
            queryset=queryset,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("medical:edit-visit",
                    args=[str(self.visit.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_visit_logout_if_security_breach(self):
        """Editing visit of another user is unsuccessful and triggers logout."""
        queryset = list(MedicalVisit.objects.filter(
            user=self.user).exclude(
            id=self.visit.id).values_list(
            "specialization", "visit_date", "visit_time", flat=False))

        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_visit.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "specialization": "SECURITY BREACH",
            "doctor": self.visit.doctor,
            "visit_date": self.visit.visit_date,
            "visit_time": self.visit.visit_time,
            "visit_location": self.visit.visit_location,
            "notes": "SECURITY BREACH",
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("medical:edit-visit",
                    args=[str(self.test_visit.id)]),
            data=payload,
            content_type="text/html",
            queryset=queryset,
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
        self.assertEqual(MedicalVisit.objects.count(), 2)
        self.assertNotIn(self.test_visit.specialization, payload["specialization"])

    def test_delete_visit_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot delete visit
        (user is redirected to login page)."""
        response = self.client.get(reverse(
            "medical:delete-visit", args=[str(self.visit.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_visit_200_if_logged_in(self):
        """Test if delete_visit page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response = self.client.get(reverse(
            "medical:delete-visit", args=[str(self.visit.id)]))
        self.assertEqual(response.status_code, 200)

    def test_delete_test_result_correct_template_if_logged_in(self):
        """Test if delete_visit page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response = self.client.get(reverse(
            "medical:delete-visit", args=[str(self.visit.id)]))
        self.assertTemplateUsed(response,
                                template_name="medical/medical_delete_form.html")

    def test_delete_visit_initial_values_set_context_data(self):
        """Test if delete_visit page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(reverse(
            "medical:delete-visit", args=[str(self.visit.id)]))
        self.assertIn(str(self.visit), response_get.content.decode())
        self.assertEqual(response_get.context["visit"], self.visit)
        self.assertEqual(response_get.context["page"], "delete-visit")

    def test_delete_visit_and_redirect(self):
        """Deleting visit is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(MedicalVisit.objects.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(reverse("medical:medical-visits"))
        self.assertIn(str(self.visit.specialization), response.content.decode())

        response_delete = self.client.post(
            reverse("medical:delete-visit", args=[str(self.visit.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("medical:medical-visits"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto wizytę lekarską.", str(messages[0]))

        response = self.client.get(reverse("medical:medical-visits"))
        self.assertEqual(MedicalVisit.objects.count(), 1)
        self.assertNotIn(self.visit.specialization, response.content.decode())
        self.assertNotIn(self.test_visit.specialization, response.content.decode())

    def test_delete_visit_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("medical:delete-visit",
                    args=[str(self.visit.id)]),
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("medical:delete-visit",
                    args=[str(self.visit.id)]),
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("medical:delete-visit",
                    args=[str(self.visit.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_visit_logout_if_security_breach(self):
        """Deleting visit of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(MedicalVisit.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_visit.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("medical:delete-visit",
                    args=[str(self.test_visit.id)]),
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
        self.assertEqual(MedicalVisit.objects.count(), 2)


class HealthTestResultTests(TestCase):
    """Test HealthTestResult views."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.result = HealthTestResultFactory(user=self.user, name="setup drug")

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com", password="testpass456")
        self.test_result = HealthTestResultFactory(
            user=self.test_user, name="test drug", notes="test notes")

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(HealthTestResult.objects.count(), 2)

    def test_health_test_results_302_redirect_if_unauthorized(self):
        """Test if test_results page is unavailable for unauthorized users."""
        response = self.client.get(reverse("medical:test-results"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_health_test_results_200_if_logged_in(self):
        """Test if test_results page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:test-results"))
        self.assertEqual(response_get.status_code, 200)

    def test_health_test_results_correct_template_if_logged_in(self):
        """Test if test_results page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:test-results"))
        self.assertTemplateUsed(response_get, "medical/medical.html")

    def test_health_test_results_initial_values_set_context_data(self):
        """Test if test_results page displays correct context data."""
        MedCardFactory(user=self.user)
        results = HealthTestResult.objects.filter(user=self.user).order_by("-updated")
        medcard = MedCard.objects.get(user=self.user)
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("medical:test-results"))
        self.assertEqual(response_get.context["page"], "test-results")
        self.assertQuerysetEqual(response_get.context["test_results"], results)
        self.assertEqual(response_get.context["medcard"], medcard)
        self.assertEqual(response_get.context["profile"],
                         self.result.user.profile)

    def test_health_test_results_initial_values_set_test_result_data(self):
        """Test if page test_results displays only test_results of logged user
        (without test_results of other users)."""
        new_user = HealthTestResultFactory(user=self.user, name="new result")

        # Test for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("medical:test-results"))

        self.assertIn(self.result.name, response_get.content.decode())
        self.assertIn(new_user.name, response_get.content.decode())
        self.assertNotIn(self.test_result.name, response_get.content.decode())

        self.client.logout()

        # Test for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("medical:test-results"))

        self.assertNotIn(self.result.name, response_get.content.decode())
        self.assertNotIn(new_user.name, response_get.content.decode())
        self.assertIn(self.test_result.name, response_get.content.decode())

    def test_single_test_result_302_redirect_if_unauthorized(self):
        """ Test if single_test_result page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("medical:single-test-result", args=[self.result.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    def test_single_test_result_200_if_logged_in(self):
        """Test if single_test_result page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:single-test-result", args=[self.result.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_single_test_result_correct_template_if_logged_in(self):
        """Test if single_test_result page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:single-test-result", args=[self.result.id]))
        self.assertTemplateUsed(response_get,
                                "medical/single_medical.html")

    def test_single_test_result_initial_values_set_context_data(self):
        """Test if single_test_result page displays correct context data."""
        MedCardFactory(user=self.user)
        medcard = MedCard.objects.get(user=self.user)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-test-result", args=[str(self.result.id)]))
        self.assertEqual(response_get.context["page"], "single-test-result")
        self.assertEqual(response_get.context["test_result"], self.result)
        self.assertEqual(response_get.context["medcard"], medcard)
        self.assertEqual(response_get.context["profile"], self.result.user.profile)

    def test_single_test_result_initial_values_set_test_result_data(self):
        """Test if single_test_result page displays correct test_result data
        (only data of logged user)."""

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-test-result", args=[self.result.id]))

        self.assertIn(self.result.name, response_get.content.decode())
        self.assertNotIn(self.test_result.name, response_get.content.decode())
        self.assertIn(self.result.notes, response_get.content.decode())
        self.assertNotIn(self.test_result.notes, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("medical:single-test-result",
                    args=[self.test_result.id]))

        self.assertIn(self.test_result.name, response_get.content.decode())
        self.assertNotIn(self.result.name, response_get.content.decode())
        self.assertIn(self.test_result.notes, response_get.content.decode())
        self.assertNotIn(self.result.notes, response_get.content.decode())

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_single_test_result_initial_values_set_attachments(self):
        """Test if single_test_result page displays correct attachments
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
        self.attachment.health_results.add(self.result)
        self.test_attachment.health_results.add(self.test_result)

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-test-result", args=[self.result.id]))

        self.assertEqual(response_get.context["attachments"][0], self.attachment)

        self.assertIn(self.result.name, response_get.content.decode())
        self.assertNotIn(self.test_result.name, response_get.content.decode())
        self.assertIn(self.result.notes, response_get.content.decode())
        self.assertNotIn(self.test_result.notes, response_get.content.decode())
        self.assertIn(self.attachment.attachment_name,
                      response_get.content.decode())
        self.assertNotIn(self.test_attachment.attachment_name,
                         response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("medical:single-test-result", args=[self.test_result.id]))

        self.assertIn(self.test_result.name, response_get.content.decode())
        self.assertNotIn(self.result.name, response_get.content.decode())
        self.assertIn(self.test_result.notes, response_get.content.decode())
        self.assertNotIn(self.result.notes, response_get.content.decode())
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

    def test_single_test_result_forced_logout_if_security_breach(self):
        """Attempt to overview test_result of another user is forbidden and
        triggers logout."""

        # Attempt to see self.test_user data by self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("medical:single-test-result",
                    args=[self.test_result.id]), follow=True)
        self.assertIn(self.test_result.name,
                      response_get.content.decode())
        self.client.logout()

        # Attempt to see self.test_user data by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:single-test-result",
                    args=[self.test_result.id]), follow=True)
        self.assertNotIn(self.test_result.name,
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

    def test_add_test_result_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add test_result
        (user is redirected to login page)."""
        response = self.client.get(reverse("medical:add-test-result"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_test_result_200_if_logged_in(self):
        """Test if add_test_result page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-test-result"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_test_result_correct_template_if_logged_in(self):
        """Test if add_test_result page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-test-result"))
        self.assertTemplateUsed(response_get, "medical/medical_form.html")

    def test_add_test_result_form_initial_values_set_context_data(self):
        """Test if add_test_result page displays correct context data."""
        queryset = list(HealthTestResult.objects.filter(
            user=self.user).values_list("name", "test_date"))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-test-result"))
        self.assertEqual(response_get.context["page"], "add-test-result")
        self.assertEqual(response_get.context["profile"], self.result.user.profile)
        self.assertEqual(response_get.context["queryset"][0]["name"], queryset[0][0])
        self.assertEqual(response_get.context["queryset"][0]["test_date"], queryset[0][1])
        self.assertIsInstance(response_get.context["form"], HealthTestResultForm)

    def test_add_test_result_form_initial_values_set_form_data(self):
        """Test if add_test_result page displays correct form data."""
        result_fields = ["name", "test_result", "test_date", "disease", "notes"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("medical:add-test-result"))
        for field in result_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz",
                      response_get.content.decode())  # input type="submit"

    def test_add_test_result_success_and_redirect(self):
        """Test if creating a test_result is successful (status code 200) and
        redirecting is successful (status code 302)."""
        payload = {
            "name": "Flu test",
            "test_result": "Positive",
            "test_date": datetime.date(2020, 10, 10)
        }
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "medical:add-test-result"),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("medical:test-results"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano wyniki.",
                      str(messages[0]))
        self.assertInHTML("Flu test",
                          response_post.content.decode())
        self.assertEqual(HealthTestResult.objects.count(), 3)
        self.assertTrue(HealthTestResult.objects.filter(
            user=self.user, name=payload["name"]).exists())

    def test_add_test_result_successful_with_correct_user(self):
        """Test if creating a test result successfully has correct user."""
        queryset = list(HealthTestResult.objects.filter(
            user=self.user).values_list("name", "test_date", flat=False))

        payload = {
            "name": "Test if user is ok",
            "test_result": "Positive",
            "test_date": datetime.date(2020, 10, 10)
        }
        self.client.force_login(self.user)

        self.client.post(reverse("medical:add-test-result"),
                         payload,
                         queryset=queryset,
                         follow=True)

        result = HealthTestResult.objects.get(name=payload["name"])
        self.assertEqual(result.user, self.user)

    @parameterized.expand(
        [
            ("Empty field: name",
             {"test_result": "Negative", "test_date": datetime.date(2020, 2, 2)},
             "To pole jest wymagane."),
            ("Empty field: test_result",
             {"name": "OB test", "test_date": datetime.date(2020, 2, 2)},
             "To pole jest wymagane."),
            ("Empty field: test_date",
             {"name": "OB test", "test_result": "2.5"},
             "To pole jest wymagane."),
            ("Not unique fields (unique together): name, test_date",
             {"name": "setup drug", "test_result": "Not good",
              "test_date": datetime.date(2020, 11, 11)},
             "Istnieje już test o tej nazwie wykonany w danym dniu."),
            ("Incorrect date field",
             {"name": "OB test", "test_result": "Not good",
              "test_date": "2020,11,11"},
             "Wpisz poprawną datę."),
        ]
    )
    def test_add_test_result_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a test_result is not successful if data is incorrect."""
        self.client.force_login(self.user)
        queryset = list(HealthTestResult.objects.filter(
            user=self.result.user).values_list(
            "name", "test_date", flat=False))
        response_post = self.client.post(
            reverse("medical:add-test-result"), payload, queryset=queryset)
        self.assertEqual(HealthTestResult.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_test_result_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot edit test result
        (user is redirected to login page)."""
        response = self.client.get(
            reverse("medical:edit-test-result", args=[self.result.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_test_result_200_if_logged_in(self):
        """Test if edit_test_result page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:edit-test-result", args=[self.result.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_test_result_correct_template_if_logged_in(self):
        """Test if edit_test_result page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:edit-test-result", args=[self.result.id]))
        self.assertTemplateUsed(response_get, "medical/medical_form.html")

    def test_edit_test_result_form_initial_values_set_context_data(self):
        """Test if edit_test_result page displays correct context data."""
        queryset = list(HealthTestResult.objects.filter(
            user=self.user).exclude(id=self.result.id).values_list(
            "name", "test_date", flat=False))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:edit-test-result", args=[str(self.result.id)]))
        self.assertEqual(response_get.context["page"], "edit-test-result")
        self.assertEqual(response_get.context["test_result"], self.result)
        self.assertQuerysetEqual(response_get.context["queryset"], queryset)
        self.assertIsInstance(response_get.context["form"], HealthTestResultForm)

    def test_edit_test_result_form_initial_values_set_form_data(self):
        """Test if edit_test_result page displays correct form data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:edit-test-result", args=[str(self.result.id)]))
        self.assertIn(self.result.notes, response_get.content.decode())
        self.assertIn(self.result.name, response_get.content.decode())

    def test_edit_test_result_success_and_redirect(self):
        """Test if updating a test_result is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        queryset = list(HealthTestResult.objects.filter(
            user=self.result.user).exclude(id=self.result.id).values_list(
            "name", "test_date", flat=False))

        payload = {
            "name": "CRP result",
            "test_result": self.result.test_result,
            "test_date": self.result.test_date,
            "disease": self.result.disease,
            "notes": "New result",
        }
        self.assertNotEqual(self.result.notes, payload["notes"])
        self.assertNotEqual(self.result.name, payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("medical:edit-test-result",
                    args=[str(self.result.id)]),
            data=payload,
            instance=self.result,
            queryset=queryset,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("medical:test-results"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano wyniki.", str(messages[0]))
        self.result.refresh_from_db()
        self.assertEqual(HealthTestResult.objects.count(), 2)
        self.assertEqual(self.result.name, payload["name"])
        self.assertEqual(self.result.notes, payload["notes"])

    def test_edit_test_result_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)
        queryset = list(HealthTestResult.objects.filter(
            user=self.result.user).exclude(id=self.result.id).values_list(
            "name", "test_date", flat=False))

        # PATCH
        payload = {
            "name": "New name",
            "test_result": "Good",
            "test_date": datetime.date(2022, 1, 1),
        }
        response_patch = self.client.patch(
            reverse("medical:edit-test-result",
                    args=[str(self.result.id)]),
            data=payload,
            instance=self.result,
            queryset=queryset,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "name": "CRP result",
            "test_result": self.result.test_result,
            "test_date": self.result.test_date,
            "disease": self.result.disease,
            "notes": "New result",
        }
        response_put = self.client.put(
            reverse("medical:edit-test-result",
                    args=[str(self.result.id)]),
            data=payload,
            instance=self.result,
            queryset=queryset,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("medical:edit-test-result",
                    args=[str(self.result.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_test_result_logout_if_security_breach(self):
        """Editing test_result of another user is unsuccessful and triggers logout."""
        queryset = list(HealthTestResult.objects.filter(
            user=self.user).exclude(
            id=self.test_result.id).values_list("name", "test_date", flat=False))
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_result.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "test_result": self.result.test_result,
            "test_date": self.result.test_date,
            "disease": self.result.disease,
            "notes": "SECURITY BREACH",
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("medical:edit-test-result",
                    args=[str(self.test_result.id)]),
            data=payload,
            content_type="text/html",
            queryset=queryset,
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
        self.assertEqual(HealthTestResult.objects.count(), 2)
        self.assertNotIn(self.test_result.name, payload["name"])

    def test_delete_test_result_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot delete test result
        (user is redirected to login page)."""
        response = self.client.get(
            reverse("medical:delete-test-result", args=[self.result.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_test_result_200_if_logged_in(self):
        """Test if delete_test_result page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:delete-test-result", args=[self.result.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_test_result_correct_template_if_logged_in(self):
        """Test if delete_test_result page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("medical:delete-test-result", args=[self.result.id]))
        self.assertTemplateUsed(response_get,
                                "medical/medical_delete_form.html")

    def test_delete_test_result_initial_values_set_context_data(self):
        """Test if delete_test_result page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("medical:delete-test-result", args=[str(self.result.id)]))
        self.assertIn(str(self.result), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-test-result")
        self.assertEqual(response_get.context["test_result"], self.result)

    def test_delete_test_result_and_redirect(self):
        """Deleting test_result is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(HealthTestResult.objects.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(reverse("medical:test-results"))
        self.assertIn(str(self.result), response.content.decode())

        response_delete = self.client.post(
            reverse("medical:delete-test-result", args=[str(self.result.id)]),
            content_type="text/html",
            follow=True,
        )
        self.assertRedirects(
            response_delete,
            reverse("medical:test-results"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto wyniki badań.", str(messages[0]))

        response = self.client.get(reverse("medical:test-results"))
        self.assertEqual(HealthTestResult.objects.count(), 1)
        self.assertNotIn(self.result.name, response.content.decode())
        self.assertNotIn(self.test_result.name, response.content.decode())

    def test_delete_test_result_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("medical:delete-test-result",
                    args=[str(self.result.id)]),
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("medical:delete-test-result",
                    args=[str(self.result.id)]),
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("medical:delete-test-result",
                    args=[str(self.result.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_test_result_logout_if_security_breach(self):
        """Deleting test result of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(HealthTestResult.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_result.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("medical:delete-test-result",
                    args=[str(self.test_result.id)]),
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
        self.assertEqual(HealthTestResult.objects.count(), 2)
