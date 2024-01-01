import datetime
import logging
import shutil
import time
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
from credit.factories import (CreditFactory, CreditAdditionalCostFactory,
                              CreditCollateralFactory, CreditInsuranceFactory,
                              CreditInterestRateFactory, CreditTrancheFactory,
                              CreditEarlyRepaymentFactory)
from credit.forms import (CreditForm, CreditInsuranceForm,
                          CreditCollateralForm, CreditTrancheForm,
                          CreditInterestRateForm, CreditAdditionalCostForm,
                          CreditEarlyRepaymentForm)
from credit.models import (Credit, CreditAdditionalCost, CreditCollateral,
                           CreditInsurance, CreditInterestRate, CreditTranche,
                           CreditEarlyRepayment)
from user.factories import UserFactory, ProfileFactory
from user.models import Profile

logger = logging.getLogger("test")
User = get_user_model()


class BasicUrlsTests(TestCase):
    """Test basic urls for credit application."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)

        self.user = UserFactory(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.profile = Profile.objects.get(user=self.user)
        self.profile.access_granted_to = "jd@example.com"    # the same as logged user
        self.profile.save()

        self.credit = CreditFactory(user=self.user)
        self.tranche = CreditTrancheFactory(user=self.user, credit=self.credit)
        additional_tranche = self.credit.credit_amount - self.tranche.tranche_amount
        self.tranche_2 = CreditTrancheFactory(
            user=self.user, credit=self.credit, tranche_amount=additional_tranche)
        self.interest_rate = CreditInterestRateFactory(user=self.user, credit=self.credit)
        self.insurance = CreditInsuranceFactory(user=self.user, credit=self.credit)
        self.collateral = CreditCollateralFactory(user=self.user, credit=self.credit)
        self.cost = CreditAdditionalCostFactory(user=self.user, credit=self.credit)
        self.repayment = CreditEarlyRepaymentFactory(user=self.user, credit=self.credit)

        self.pages = [
            {"page": "credit:credits",
             "args": [], "name": "credits",
             "template": "credit/credits.html"},
            {"page": "credit:single-credit",
             "args": [str(self.credit.id)], "name": "single-credit",
             "template": "credit/single_credit.html"},

            {"page": "credit:add-credit",
             "args": [], "name": "add-credit",
             "template": "credit/credit_form.html"},
            {"page": "credit:edit-credit",
             "args": [str(self.credit.id)], "name": "edit-credit",
             "template": "credit/credit_form.html"},
            {"page": "credit:delete-credit",
             "args": [str(self.credit.id)], "name": "delete-credit",
             "template": "credit/credit_delete_form.html"},

            {"page": "credit:add-credit-interest-rate",
             "args": [str(self.credit.id)], "name": "add-credit-interest-rate",
             "template": "credit/credit_form.html"},
            {"page": "credit:edit-credit-interest-rate",
             "args": [str(self.interest_rate.id)], "name": "edit-credit-interest-rate",
             "template": "credit/credit_form.html"},
            {"page": "credit:delete-credit-interest-rate",
             "args": [str(self.interest_rate.id)], "name": "delete-credit-interest-rate",
             "template": "credit/credit_delete_form.html"},

            {"page": "credit:add-credit-insurance",
             "args": [str(self.credit.id)], "name": "add-credit-insurance",
             "template": "credit/credit_form.html"},
            {"page": "credit:edit-credit-insurance",
             "args": [str(self.insurance.id)],
             "name": "edit-credit-insurance",
             "template": "credit/credit_form.html"},
            {"page": "credit:delete-credit-insurance",
             "args": [str(self.insurance.id)],
             "name": 'delete-credit-insurance',
             "template": "credit/credit_delete_form.html"},

            {"page": "credit:add-credit-tranche",
             "args": [str(self.credit.id)], "name": "add-credit-tranche",
             "template": "credit/credit_form.html"},
            {"page": "credit:edit-credit-tranche",
             "args": [str(self.tranche.id)],
             "name": "edit-credit-tranche",
             "template": "credit/credit_form.html"},
            {"page": "credit:delete-credit-tranche",
             "args": [str(self.tranche.id)],
             "name": 'delete-credit-tranche',
             "template": "credit/credit_delete_form.html"},

            {"page": "credit:add-credit-collateral",
             "args": [str(self.credit.id)], "name": "add-credit-collateral",
             "template": "credit/credit_form.html"},
            {"page": "credit:edit-credit-collateral",
             "args": [str(self.collateral.id)],
             "name": "edit-credit-collateral",
             "template": "credit/credit_form.html"},
            {"page": "credit:delete-credit-collateral",
             "args": [str(self.collateral.id)],
             "name": 'delete-credit-collateral',
             "template": "credit/credit_delete_form.html"},

            {"page": "credit:add-credit-additional-cost",
             "args": [str(self.credit.id)], "name": "add-credit-additional-cost",
             "template": "credit/credit_form.html"},
            {"page": "credit:edit-credit-additional-cost",
             "args": [str(self.cost.id)],
             "name": "edit-credit-additional-cost",
             "template": "credit/credit_form.html"},
            {"page": "credit:delete-credit-additional-cost",
             "args": [str(self.cost.id)],
             "name": 'delete-credit-additional-cost',
             "template": "credit/credit_delete_form.html"},

            {"page": "credit:add-credit-early-repayment",
             "args": [str(self.credit.id)], "name": "add-credit-early-repayment",
             "template": "credit/credit_form.html"},
            {"page": "credit:edit-credit-early-repayment",
             "args": [str(self.repayment.id)],
             "name": "edit-credit-early-repayment",
             "template": "credit/credit_form.html"},
            {"page": "credit:delete-credit-early-repayment",
             "args": [str(self.repayment.id)],
             "name": 'delete-credit-early-repayment',
             "template": "credit/credit_delete_form.html"},

            # For credit schedule page to be rendered there has to be several
            # conditions fulfilled:
                # Credit model:
                    # access_granted = Access.ACCESS_GRANTED
                    # access_granted_for_schedule = Access.ACCESS_GRANTED
                # and if:
                    # tranches_in_credit = YesNo.YES
                # then sum of tranche_amount in CreditTranche models must be equal to credit_amount
            # Also logged in user who attempt to see another user's credit
            # schedule must have the same email address in Profile model as
            # was specified by the owner of the credit in his Profile account
            # in field access_granted_to.
            {"page": "credit:credit-repayment-schedule",
             "args": [str(self.credit.id)], "name": "credit-repayment-schedule",
             "template": "credit/credit_repayment_schedule.html"},
            {"page": "credit:access-to-credit-schedule",
             "args": [str(self.credit.slug)],
             "name": "access-to-credit-schedule",
             "template": "credit/credit_repayment_schedule.html"},
        ]

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def tearDown(self):
        if os.path.exists(settings.TEST_ROOT):
            shutil.rmtree(settings.TEST_ROOT)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_url_accessible_by_name_for_unauthenticated_user(self):
        """Test if view url is accessible by its name
        and returns redirect (302) for unauthenticated user."""
        for page in self.pages:
            response_page = self.client.get(
                reverse(page["page"], args=page["args"]))
            self.assertEqual(response_page.status_code, 302)
            self.assertIn("login", response_page.url)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_url_accessible_by_name_for_authenticated_user(self):
        """Test if view url is accessible by its name
         and returns desired page (200) for authenticated user."""
        self.client.force_login(self.user)
        for page in self.pages:
            response_page = self.client.get(
                reverse(page["page"], args=page["args"]))
            self.assertEqual(response_page.status_code, 200)
            self.assertEqual(str(response_page.context["user"]), "johndoe123")

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_uses_correct_template(self):
        """Test if response returns correct page template."""

        # Test for authenticated user
        self.client.force_login(self.user)
        for page in self.pages:
            response = self.client.get(
                reverse(page["page"], args=page["args"]))
            self.assertTemplateUsed(response, page["template"])


class AccessCreditScheduleUrlsTests(TestCase):
    """Test specific urls access situations for access credit schedule page."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)

        self.user = UserFactory(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.profile = Profile.objects.get(user=self.user)

        self.credit = CreditFactory(user=self.user)
        self.tranche = CreditTrancheFactory(user=self.user, credit=self.credit)

        self.interest_rate = CreditInterestRateFactory(
            user=self.user, credit=self.credit)
        self.insurance = CreditInsuranceFactory(
            user=self.user, credit=self.credit)
        self.collateral = CreditCollateralFactory(
            user=self.user, credit=self.credit)
        self.cost = CreditAdditionalCostFactory(
            user=self.user, credit=self.credit)
        self.repayment = CreditEarlyRepaymentFactory(
            user=self.user, credit=self.credit)

        self.page = {
            "page": "credit:access-to-credit-schedule",
            "args": [str(self.credit.slug)],
            "name": "access-to-credit-schedule",
            "template": "credit/credit_repayment_schedule.html"
        }

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def tearDown(self):
        if os.path.exists(settings.TEST_ROOT):
            shutil.rmtree(settings.TEST_ROOT)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_url_status_code_200_if_all_conditions_fulfilled(self):
        """Test if view url exists at desired location if all conditions are met.
        Conditions:
        1) logged in user has access to another user's data
            - user logged in: self.user_with_access (email: test123@example.com)
            - access granted by user: self.user (Profile > access_granted_to = "test123@example.com")
        2) access to see credit is granted by self.user
            -  self.user (Credit > access_granted = Access.ACCESS_GRANTED)
        3) access to see credit schedule is granted by self.user
            -  self.user (Credit > access_granted_to_schedule = Access.ACCESS_GRANTED)
        4) credit schedule is fulfilled by self.user (has all required information
        including tranche amounts equal to credit amount)
        """

        # creating user with access
        user_with_access = User.objects.create_user(
            username="testuser123", email="test123@example.com",
            password="testpass456"
        )
        self.assertTrue(User.objects.filter(username="testuser123").exists())
        # giving access to credit to created user
        self.profile.access_granted_to = "test123@example.com"    # the same as logged user
        self.profile.save()
        # fulfilling credit tranches so that sum of tranches matches credit amount
        additional_tranche = self.credit.credit_amount - self.tranche.tranche_amount
        self.tranche_2 = CreditTrancheFactory(
            user=self.user, credit=self.credit, tranche_amount=additional_tranche)

        self.client.force_login(user_with_access)
        url = reverse(self.page["page"], args=self.page["args"])
        response_page = self.client.get(url)
        self.assertEqual(response_page.status_code, 200)
        self.assertEqual(str(response_page.context["user"]), "testuser123")
        self.assertIn(str(self.credit), response_page.content.decode())
        self.assertIn("Rata całkowita", response_page.content.decode())
        self.assertIn("Saldo", response_page.content.decode(encoding="UTF-8"))

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_url_status_code_302_if_no_access_granted_to_users_data(self):
        """Test if user is logged out and redirect to login page when
        attempting to see credit schedule without proper access in access_granted_to."""
        user_with_access = User.objects.create_user(
            username="testuser123", email="test123@example.com",
            password="testpass456"
        )
        self.assertTrue(User.objects.filter(username="testuser123").exists())
        self.profile.access_granted_to = "some_other_user@example.com"    # different email (no access granted to test123@example.com)
        self.profile.save()

        additional_tranche = self.credit.credit_amount - self.tranche.tranche_amount
        self.tranche_2 = CreditTrancheFactory(
            user=self.user, credit=self.credit, tranche_amount=additional_tranche)

        self.assertNotEqual(user_with_access.email, self.profile.access_granted_to)
        self.client.force_login(user_with_access)
        self.assertIn("_auth_user_id", self.client.session)
        response_page = self.client.get(
            reverse("credit:access-to-credit-schedule",
                    args=[str(self.credit.slug)]),
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_page,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_page.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do tych danych.",
                      str(messages[0]))
        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("Saldo", response_page.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_url_status_code_302_if_no_access_granted_to_credit_schedule(self):
        """Test if user is logged out and redirect to login page when
        attempting to see credit schedule without proper access that schedule."""
        user_with_access = User.objects.create_user(
            username="testuser123", email="test123@example.com",
            password="testpass456"
        )
        self.assertTrue(User.objects.filter(username="testuser123").exists())
        self.profile.access_granted_to = "test123@example.com"    # correct email access
        self.profile.save()

        self.credit.access_granted_for_schedule = Access.NO_ACCESS_GRANTED  # no access to credit schedule
        self.credit.save()

        additional_tranche = self.credit.credit_amount - self.tranche.tranche_amount
        self.tranche_2 = CreditTrancheFactory(
            user=self.user, credit=self.credit, tranche_amount=additional_tranche)

        self.assertEqual(user_with_access.email, self.profile.access_granted_to)
        self.client.force_login(user_with_access)
        self.assertIn("_auth_user_id", self.client.session)
        response_page = self.client.get(
            reverse("credit:access-to-credit-schedule",
                    args=[str(self.credit.slug)]),
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_page,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_page.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do tych danych.",
                      str(messages[0]))
        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("Saldo", response_page.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_url_status_code_302_if_credit_data_is_not_complete_no_initial_tranche(self):
        """Test if user is redirect to previous page when attempting to see
        credit schedule without initial tranche (if required)."""
        user_with_access = User.objects.create_user(
            username="testuser123", email="test123@example.com",
            password="testpass456"
        )
        self.assertTrue(User.objects.filter(username="testuser123").exists())
        self.profile.access_granted_to = "test123@example.com"    # correct email access
        self.profile.save()

        self.tranche.delete()   # no initial data available (data required)

        self.assertEqual(user_with_access.email, self.profile.access_granted_to)
        self.client.force_login(user_with_access)
        self.assertIn("_auth_user_id", self.client.session)
        response_page = self.client.get(
            reverse("credit:access-to-credit-schedule",
                    args=[str(self.credit.slug)]),
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_page,
            reverse("access:data-access-payments",
                    args=[str(self.profile.slug), 1]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_page.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Harmonogram niedostępny - nieprawidłowe dane dotyczące "
                      "kredytu. Wymagana wpłata inicjalna.",
                      str(messages[0]))
        self.assertNotIn("Saldo", response_page.content.decode())

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_view_url_status_code_200_with_message_error_if_sum_of_tranches_not_equal_credit_amount(self):
        """Test if user is able to see credit schedule with additional error
        message if owner of the credit does not fulfill all credit tranches
        (except for initial one)."""
        user_with_access = User.objects.create_user(
            username="testuser123", email="test123@example.com",
            password="testpass456"
        )
        self.assertTrue(User.objects.filter(username="testuser123").exists())
        self.profile.access_granted_to = "test123@example.com"    # correct email access
        self.profile.save()

        additional_tranche = (self.credit.credit_amount
                              - self.tranche.tranche_amount
                              - 1000)  # not full credit amount is covered in tranches
        self.tranche_2 = CreditTrancheFactory(
            user=self.user, credit=self.credit, tranche_amount=additional_tranche)

        credit_amount = round(self.credit.credit_amount, 2)
        credit_tranches = CreditTranche.objects.filter(credit=self.credit)
        sum_of_tranches = round(CreditTranche.total_tranche(credit_tranches), 2)

        self.assertNotEqual(credit_amount, sum_of_tranches)
        self.client.force_login(user_with_access)

        response_page = self.client.get(
            reverse("credit:access-to-credit-schedule",
                    args=[str(self.credit.slug)]),
            content_type="text/html",
            follow=True)
        self.assertEqual(response_page.status_code, 200)

        messages = list(response_page.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn(f"Suma transz ({sum_of_tranches}) nie jest równa "
                      f"wartości kredytu ({credit_amount}). "
                      f"Wymagane uzupełnienie kredytu celem wygenerowania "
                      f"prawidłowego harmonogramu.",
                      str(messages[0]))
        self.assertIn("Saldo", response_page.content.decode())

class CreditTests(TestCase):
    """Test Credit views."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)

        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.profile = Profile.objects.get(user=self.user)

        self.credit = CreditFactory(user=self.user)
        self.tranche = CreditTrancheFactory(
            user=self.user, credit=self.credit, tranche_amount=666)
        self.interest_rate = CreditInterestRateFactory(user=self.user,
                                                       credit=self.credit)
        self.insurance = CreditInsuranceFactory(user=self.user,
                                                credit=self.credit)
        self.collateral = CreditCollateralFactory(user=self.user,
                                                  credit=self.credit)
        self.cost = CreditAdditionalCostFactory(user=self.user,
                                                credit=self.credit)
        self.repayment = CreditEarlyRepaymentFactory(user=self.user,
                                                     credit=self.credit)
        self.counterparty = CounterpartyFactory(user=self.user)

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com",
            password="testpass456")
        self.test_credit = CreditFactory(
            user=self.test_user, name="test credit", credit_number="ABCD1234")
        self.test_tranche = CreditTrancheFactory(
            user=self.test_user, credit=self.test_credit,
            tranche_amount=333, tranche_date=datetime.date(2020, 6, 1))
        self.test_interest_rate = CreditInterestRateFactory(
            user=self.test_user, credit=self.test_credit, interest_rate=12.3)
        self.test_insurance = CreditInsuranceFactory(
            user=self.test_user, credit=self.test_credit, amount=999)
        self.test_collateral = CreditCollateralFactory(
            user=self.test_user, credit=self.test_credit, description="Home")
        self.test_cost = CreditAdditionalCostFactory(
            user=self.test_user, credit=self.test_credit, name="Notary")
        self.test_repayment = CreditEarlyRepaymentFactory(
            user=self.test_user, credit=self.test_credit,
            repayment_action="Zmniejszenie raty")

        self.payload = {
            "name": "New credit for tests",
            "credit_number": "NewCredit123",
            "type": "Konsumpcyjny",
            "currency": "EUR",
            "credit_amount": 70000,
            "own_contribution": 10000,
            "market_value": "",
            "credit_period": 60,
            "grace_period": 0,
            "installment_type": "Raty malejące",
            "installment_frequency": "Miesięczne",
            "total_installment": 0,
            "capital_installment": 1010,
            "type_of_interest": "Zmienne",
            "fixed_interest_rate": 0,
            "floating_interest_rate": 5.5,
            "bank_margin": 1.2,
            "interest_rate_benchmark": "EURIBOR",
            "date_of_agreement": datetime.date(2020, 1, 1),
            "start_of_credit": datetime.date(2020, 2, 1),
            "start_of_payment": datetime.date(2020, 3, 1),
            "payment_day": 1,
            "provision": 0,
            "credited_provision": "Nie",
            "tranches_in_credit": "Tak",
            "life_insurance_first_year": 600,
            "property_insurance_first_year": 0,
            "collateral_required": "Tak",
            "collateral_rate": 1.5,
            "notes": "",
            "access_granted": "Udostępnij dane",
            "access_granted_for_schedule": "Brak dostępu",
        }

    def tearDown(self):
        if os.path.exists(settings.TEST_ROOT):
            shutil.rmtree(settings.TEST_ROOT)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(CreditTranche.objects.count(), 2)
        self.assertEqual(CreditInterestRate.objects.count(), 2)
        self.assertEqual(CreditInsurance.objects.count(), 2)
        self.assertEqual(CreditCollateral.objects.count(), 2)
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)
        self.assertEqual(Counterparty.objects.count(), 1)

    def test_credits_302_redirect_if_unauthorized(self):
        """Test credits page is unavailable for unauthorized users."""
        response = self.client.get(reverse("credit:credits"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_credits_200_if_logged_in(self):
        """Test credits page returns status code 200 for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:credits"))
        self.assertEqual(response_get.status_code, 200)

    def test_credits_correct_template_if_logged_in(self):
        """Test credits page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:credits"))
        self.assertTemplateUsed(response_get, "credit/credits.html")

    def test_credits_initial_values_set_context_data(self):
        """Test credits page displays correct context data."""
        credits = Credit.objects.filter(user=self.user).order_by("-updated")
        attachments = self.user.attachment_set.all()
        counterparties = self.user.counterparty_set.all()
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("credit:credits"))
        self.assertQuerysetEqual(response_get.context["credits"], credits)
        self.assertQuerysetEqual(response_get.context["counterparties"],
                                 counterparties)
        self.assertQuerysetEqual(response_get.context["attachments"], attachments)

    def test_credits_initial_values_set_credits_data(self):
        """Test if page credits displays only credits of logged user
        (without credits of other users)."""
        new_credit = CreditFactory(user=self.user, name="new credit")

        # Test for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("credit:credits"))

        self.assertIn(self.credit.name, response_get.content.decode())
        self.assertIn(new_credit.name, response_get.content.decode())
        self.assertNotIn(self.test_credit.name, response_get.content.decode())

        self.client.logout()

        # Test for user self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("credit:credits"))

        self.assertNotIn(self.credit.name, response_get.content.decode())
        self.assertNotIn(new_credit.name, response_get.content.decode())
        self.assertIn(self.test_credit.name, response_get.content.decode())

    def test_single_credit_302_redirect_if_unauthorized(self):
        """ Test if single_credit page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("credit:single-credit", args=[self.credit.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    def test_single_credit_200_if_logged_in(self):
        """Test if single_credit page return status code 200 for
        authenticated user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:single-credit", args=[self.credit.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_single_credit_correct_template_if_logged_in(self):
        """Test if single_credit page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:single-credit", args=[self.credit.id]))
        self.assertTemplateUsed(
            response_get, "credit/single_credit.html")

    def test_single_credit_initial_values_set_context_data(self):
        """Test if single_credit page displays correct context data."""
        credit_interest_rate = CreditInterestRate.objects.filter(
            credit=self.credit).order_by("interest_rate_start_date")
        credit_insurance = CreditInsurance.objects.filter(
            credit=self.credit).order_by("start_date")
        credit_tranche = CreditTranche.objects.filter(
            credit=self.credit).order_by("tranche_date")
        credit_tranches_total = CreditTranche.total_tranche(credit_tranche)
        credit_early_repayment = CreditEarlyRepayment.objects.filter(
            credit=self.credit).order_by("repayment_date")
        credit_total_repayment = CreditEarlyRepayment.total_repayment(
            credit_early_repayment)
        credit_collateral = CreditCollateral.objects.filter(
            credit=self.credit).order_by("collateral_set_date")
        credit_additional_cost = CreditAdditionalCost.objects.filter(
            credit=self.credit).order_by("cost_payment_date")
        attachments = Attachment.objects.filter(credits=self.credit.id)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertEqual(response_get.context["profile"], self.credit.user.profile)
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertQuerysetEqual(response_get.context["attachments"], attachments)
        self.assertQuerysetEqual(response_get.context["credit_interest_rate"],
                                 credit_interest_rate)
        self.assertQuerysetEqual(response_get.context["credit_insurance"],
                                 credit_insurance)
        self.assertQuerysetEqual(response_get.context["credit_tranche"],
                                 credit_tranche)
        self.assertEqual(response_get.context["credit_tranches_total"],
                         credit_tranches_total)
        self.assertEqual(response_get.context["credit_tranches_ratio"], round(
            ((credit_tranches_total / self.credit.credit_amount) * 100), 2))
        self.assertQuerysetEqual(response_get.context["credit_early_repayment"],
                                 credit_early_repayment)
        self.assertEqual(response_get.context["credit_total_repayment"],
                         credit_total_repayment)
        self.assertEqual(response_get.context["credit_repayment_ratio"],
                         round(((credit_total_repayment / self.credit.credit_amount)
                                * 100), 2))
        self.assertQuerysetEqual(response_get.context["credit_collateral"],
                                 credit_collateral)
        self.assertQuerysetEqual(response_get.context["credit_additional_cost"],
                                 credit_additional_cost)

    def test_single_credit_initial_values_set_credit_data(self):
        """Test if single_credit page displays correct credit data
        (only data of logged user)."""

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:single-credit", args=[self.credit.id]))

        self.assertIn(self.credit.name, response_get.content.decode())
        self.assertNotIn(self.test_credit.name, response_get.content.decode())
        self.assertIn(self.credit.credit_number, response_get.content.decode())
        self.assertNotIn(self.test_credit.credit_number, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("credit:single-credit",
                    args=[self.test_credit.id]))

        self.assertIn(self.test_credit.name, response_get.content.decode())
        self.assertNotIn(self.credit.name, response_get.content.decode())
        self.assertIn(self.test_credit.credit_number, response_get.content.decode())
        self.assertNotIn(self.credit.credit_number, response_get.content.decode())

    def test_single_credit_initial_values_set_foreign_key_model_data(self):
        """Test if single_credit page displays correct credit data of foreign key models
        (only data of logged user)."""

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:single-credit", args=[self.credit.id]))

        self.assertIn("1 maja 2020", response_get.content.decode())
        self.assertIn(self.interest_rate.note, response_get.content.decode())
        self.assertIn(str(self.insurance.amount), response_get.content.decode())
        self.assertIn(self.collateral.description, response_get.content.decode())
        self.assertIn(self.cost.name, response_get.content.decode())
        self.assertIn(self.repayment.repayment_action,
                      response_get.content.decode())
        self.assertNotIn("1 czerwca 2020", response_get.content.decode())
        self.assertNotIn(self.test_interest_rate.note,
                         response_get.content.decode())
        self.assertNotIn(str(self.test_insurance.amount),
                         response_get.content.decode())
        self.assertNotIn(self.test_collateral.description,
                         response_get.content.decode())
        self.assertNotIn(self.test_cost.name, response_get.content.decode())
        self.assertNotIn(self.test_repayment.repayment_action,
                         response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("credit:single-credit",
                    args=[self.test_credit.id]))

        self.assertNotIn("1 maja 2020", response_get.content.decode())
        self.assertNotIn(self.interest_rate.note,
                         response_get.content.decode())
        self.assertNotIn(str(self.insurance.amount),
                         response_get.content.decode())
        self.assertNotIn(self.collateral.description,
                         response_get.content.decode())
        self.assertNotIn(self.cost.name, response_get.content.decode())
        self.assertNotIn(self.repayment.repayment_action,
                         response_get.content.decode())
        self.assertIn("1 czerwca 2020", response_get.content.decode())
        self.assertIn(self.test_interest_rate.note,
                      response_get.content.decode())
        self.assertIn(str(self.test_insurance.amount),
                      response_get.content.decode())
        self.assertIn(self.test_collateral.description,
                      response_get.content.decode())
        self.assertIn(self.test_cost.name, response_get.content.decode())
        self.assertIn(self.test_repayment.repayment_action,
                      response_get.content.decode())

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_single_credit_initial_values_set_attachments(self):
        """Test if single_credit page displays correct attachments
        (only data of logged user)."""

        # For testing file attachment
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)
        paths = [os.path.join(settings.TEST_ROOT, str(self.user.id)),
                 os.path.join(settings.TEST_ROOT, str(self.test_user.id))]
        for path in paths:
            if not os.path.exists(path):
                os.mkdir(path)

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
        self.attachment.credits.add(self.credit)
        self.test_attachment.credits.add(self.test_credit)

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:single-credit", args=[self.credit.id]))
        credit_id = response_get.request["PATH_INFO"].split("/")[-2]
        self.assertEqual(self.credit, Credit.objects.get(id=credit_id))
        self.assertIn(self.credit.name, response_get.content.decode())
        self.assertNotIn(self.test_credit.name, response_get.content.decode())
        self.assertIn(self.attachment.attachment_name,
                      response_get.content.decode())
        self.assertNotIn(self.test_attachment.attachment_name,
                         response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("credit:single-credit", args=[self.test_credit.id]))

        self.assertIn(self.test_credit.name, response_get.content.decode())
        self.assertNotIn(self.credit.name, response_get.content.decode())
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

    def test_single_credit_initial_values_set_counterparties_data(self):
        """Test if single_credit page displays correct counterparty data
        (only data of logged user)."""
        user_counterparty_1 = CounterpartyFactory(user=self.user, name="cp 1")
        user_counterparty_2 = CounterpartyFactory(user=self.user, name="cp 2")
        test_user_counterparty = CounterpartyFactory(user=self.test_user,
                                                     name="test cp")
        self.assertEqual(Counterparty.objects.filter(user=self.user).count(), 3)
        self.assertEqual(Counterparty.objects.filter(user=self.test_user).count(), 1)
        user_counterparty_1.credits.add(self.credit)
        user_counterparty_1.save()
        user_counterparty_2.credits.add(self.credit)
        user_counterparty_2.save()
        test_user_counterparty.credits.add(self.test_credit)
        test_user_counterparty.save()

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:single-credit", args=[self.credit.id]))

        self.assertIn(user_counterparty_1.name, response_get.content.decode())
        self.assertIn(user_counterparty_2.name, response_get.content.decode())
        self.assertNotIn(test_user_counterparty.name, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("credit:single-credit",
                    args=[self.test_credit.id]))

        self.assertIn(test_user_counterparty.name, response_get.content.decode())
        self.assertNotIn(user_counterparty_1.name, response_get.content.decode())
        self.assertNotIn(user_counterparty_2.name, response_get.content.decode())

    def test_single_credit_forced_logout_if_security_breach(self):
        """Attempt to overview single credit of another user is forbidden and
        triggers logout."""

        # Attempt to see self.test_user data by self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("credit:single-credit",
                    args=[self.test_credit.id]), follow=True)
        self.assertIn(self.test_credit.name,
                      response_get.content.decode())
        self.client.logout()

        # Attempt to see self.test_user data by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:single-credit",
                    args=[self.test_credit.id]), follow=True)
        self.assertNotIn(self.test_credit.name,
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

    def test_add_credit_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add credit
        (user is redirected to login page)."""
        response = self.client.get(reverse("credit:add-credit"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_credit_200_if_logged_in(self):
        """Test if add_credit page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_credit_correct_template_if_logged_in(self):
        """Test if add_credit page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit"))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_add_credit_form_initial_values_set_context_data(self):
        """Test if add_credit page displays correct context data."""
        credit_names = list(Credit.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit"))
        self.assertEqual(response_get.context["page"], "add-credit")
        self.assertQuerysetEqual(response_get.context["credit_names"], credit_names)
        self.assertIsInstance(response_get.context["form"], CreditForm)

    def test_add_credit_form_initial_values_set_form_data(self):
        """Test if add_credit page displays correct form data."""
        credit_fields = ["name", "credit_number", "type", "currency",
                         "credit_amount", "own_contribution", "market_value",
                         "credit_period", "grace_period", "installment_type",
                         "installment_frequency", "total_installment",
                         "capital_installment", "type_of_interest",
                         "fixed_interest_rate", "floating_interest_rate",
                         "bank_margin", "interest_rate_benchmark",
                         "date_of_agreement", "start_of_credit",
                         "start_of_payment", "payment_day", "provision",
                         "credited_provision", "tranches_in_credit",
                         "life_insurance_first_year",
                         "property_insurance_first_year", "collateral_required",
                         "collateral_rate", "notes", "access_granted",
                         "access_granted_for_schedule"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit"))
        for field in credit_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_credit_success_and_redirect(self):
        """Test if creating a credit is successful (status code 200) and
        redirecting is successful (status code 302)."""
        credit_names = list(
            Credit.objects.filter(user=self.user).values_list(
                "name", flat=True))
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "credit:add-credit"),
            data=self.payload,
            credit_names=credit_names,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("credit:credits"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano kredyt.",
                      str(messages[0]))
        self.assertInHTML("New credit for tests",
                          response_post.content.decode(encoding="UTF-8"))
        self.assertEqual(Credit.objects.count(), 3)
        self.assertTrue(Credit.objects.filter(
            user=self.user, name=self.payload["name"]).exists())

    def test_add_credit_successful_with_correct_user(self):
        """Test if creating a credit successfully has correct user."""
        credit_names = list(Credit.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.force_login(self.user)

        self.client.post(reverse("credit:add-credit"),
                         data=self.payload,
                         credit_names=credit_names,
                         follow=True)

        credit = Credit.objects.get(name=self.payload["name"])
        self.assertEqual(credit.user, self.user)

    @parameterized.expand(
        [
            ("Empty field: name", {"name": ""}, "To pole jest wymagane."),
            ("Not unique field: name", {"name": "Some credit name"},
             "Istnieje już kredyt o podanej nazwie w bazie danych. "
             "Podaj inną nazwę."),

            ("Empty field: type", {"type": ""}, "To pole jest wymagane."),
            ("Incorrect type field - value outside the permissible choice",
             {"type": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),

            ("Empty field: currency", {"currency": ""}, "To pole jest wymagane."),
            ("Incorrect currency field - value outside the permissible choice",
             {"currency": "CNY"},
             "Wybierz poprawną wartość. CNY nie jest żadną z dostępnych opcji."),

            ("Empty field: credit_amount", {"credit_amount": ""},
             "To pole jest wymagane."),
            ("Incorrect credit_amount field (negative values are not allowed)",
             {"credit_amount": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect credit_amount field - max 2 decimal places",
             {"credit_amount": 112000.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),

            ("Incorrect own_contribution field (negative values are not allowed)",
             {"own_contribution": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect own_contribution field - max 2 decimal places",
             {"own_contribution": 112000.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),

            ("Incorrect market_value field (negative values are not allowed)",
             {"market_value": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect market_value field - max 2 decimal places",
             {"market_value": 112000.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),

            ("Empty field: credit_period", {"credit_period": ""},
             "To pole jest wymagane."),

            ("Empty field: installment_type", {"installment_type": ""},
             "To pole jest wymagane."),
            ("Incorrect installment_type field - value outside the permissible choice",
             {"installment_type": "Jakaś wartość"},
             "Wybierz poprawną wartość. Jakaś wartość nie jest żadną z dostępnych opcji."),

            ("Empty field: installment_frequency", {"installment_frequency": ""},
             "To pole jest wymagane."),
            ("Incorrect installment_frequency field - value outside the "
             "permissible choice", {"installment_frequency": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),

            ("Empty field: total_installment", {"total_installment": ""},
             "To pole jest wymagane."),
            ("Incorrect total_installment field (negative values are not allowed)",
             {"total_installment": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect total_installment field - max 2 decimal places",
             {"total_installment": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect total_installment field - max 8 digits",
             {"total_installment": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),

            ("Empty field: capital_installment", {"capital_installment": ""},
             "To pole jest wymagane."),
            ("Incorrect capital_installment field (negative values are not allowed)",
             {"capital_installment": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect capital_installment field - max 2 decimal places",
             {"capital_installment": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect capital_installment field - max 8 digits",
             {"capital_installment": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),

            ("Empty field: type_of_interest", {"type_of_interest": ""},
             "To pole jest wymagane."),
            ("Incorrect type_of_interest field - value outside the permissible choice",
             {"type_of_interest": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),

            ("Empty field: fixed_interest_rate", {"fixed_interest_rate": ""},
             "To pole jest wymagane."),
            ("Incorrect fixed_interest_rate field (negative values are not allowed)",
             {"fixed_interest_rate": -45}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect fixed_interest_rate field - max 2 digits before decimal places",
             {"fixed_interest_rate": 456.1},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry przed przecinkiem."),
            ("Incorrect fixed_interest_rate field - max 2 decimal places",
             {"fixed_interest_rate": 1.987},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect fixed_interest_rate field - max 4 digits",
             {"fixed_interest_rate": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 4 cyfry."),

            ("Empty field: floating_interest_rate", {"floating_interest_rate": ""},
             "To pole jest wymagane."),
            ("Incorrect floating_interest_rate field (negative values are not allowed)",
             {"floating_interest_rate": -46}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect floating_interest_rate field (negative values are not allowed)",
             {"floating_interest_rate": -456.1},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry przed przecinkiem."),
            ("Incorrect floating_interest_rate field - max 2 decimal places",
             {"floating_interest_rate": 1.986},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect floating_interest_rate field - max 4 digits",
             {"floating_interest_rate": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 4 cyfry."),

            ("Empty field: bank_margin", {"bank_margin": ""},
             "To pole jest wymagane."),
            ("Incorrect bank_margin field (negative values are not allowed)",
             {"bank_margin": -45}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect bank_margin field (negative values are not allowed)",
             {"bank_margin": -456.1},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry przed przecinkiem."),
            ("Incorrect bank_margin field - max 4 digits with 2 decimal places",
             {"bank_margin": 1.987},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect bank_margin field - max 4 digits with 2 decimal places",
             {"bank_margin": 111.98},
             "Upewnij się, że łącznie nie ma więcej niż 4 cyfry."),

            ("Empty field: date_of_agreement", {"date_of_agreement": ""},
             "To pole jest wymagane."),
            ("Incorrect date_of_agreement field (incorrect data)",
             {"date_of_agreement": "2020, 11, 11"}, "Wpisz poprawną datę."),
            ("Empty field: start_of_credit", {"start_of_credit": ""},
             "To pole jest wymagane."),
            ("Incorrect start_of_credit field (incorrect data)",
             {"start_of_credit": "2020, 11, 11"}, "Wpisz poprawną datę."),
            ("Empty field: start_of_payment", {"start_of_payment": ""},
             "To pole jest wymagane."),
            ("Incorrect start_of_payment field (incorrect data)",
             {"start_of_payment": "2020, 11, 11"}, "Wpisz poprawną datę."),
            ("Empty field: payment_day", {"payment_day": ""},
             "To pole jest wymagane."),

            ("Incorrect provision field (negative values are not allowed)",
             {"provision": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect provision field - max 8 digits with 2 decimal places",
             {"provision": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),

            ("Empty field: credited_provision", {"credited_provision": ""},
             "To pole jest wymagane."),
            ("Incorrect credited_provision field - value outside the permissible choice",
             {"credited_provision": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),
            ("Empty field: tranches_in_credit", {"tranches_in_credit": ""},
             "To pole jest wymagane."),
            ("Incorrect tranches_in_credit field - value outside the permissible choice",
             {"tranches_in_credit": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),

            ("Incorrect life_insurance_first_year field (negative values are "
             "not allowed)", {"life_insurance_first_year": -456},
             "Wartość nie może być liczbą ujemną."),
            ("Incorrect life_insurance_first_year field - max decimal places",
             {"life_insurance_first_year": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect life_insurance_first_year field - max 8 digits",
             {"life_insurance_first_year": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),
            ("Incorrect property_insurance_first_year field (negative values "
             "are not allowed)", {"property_insurance_first_year": -456},
             "Wartość nie może być liczbą ujemną."),
            ("Incorrect property_insurance_first_year field - max 2 decimal places",
             {"property_insurance_first_year": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect property_insurance_first_year field - max 8 digits",
             {"property_insurance_first_year": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),

            ("Empty field: collateral_required", {"collateral_required": ""},
             "To pole jest wymagane."),
            ("Incorrect collateral_required field - value outside the permissible choice",
             {"collateral_required": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),
            ("Incorrect collateral_rate field (negative values are not allowed)",
             {"collateral_rate": -45.6}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect collateral_rate field (negative values are not allowed)",
             {"collateral_rate": -456},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry przed przecinkiem."),
            ("Incorrect collateral_rate field - max 4 digits with 2 decimal places",
             {"collateral_rate": 1.987},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect collateral_rate field - max 4 digits with 2 decimal places",
             {"collateral_rate": 112.98},
             "Upewnij się, że łącznie nie ma więcej niż 4 cyfry."),

            ("Empty field: access_granted", {"access_granted": ""},
             "To pole jest wymagane."),
            ("Incorrect access_granted field - value outside the permissible choice",
             {"access_granted": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),
            ("Empty field: access_granted_for_schedule",
             {"access_granted_for_schedule": ""}, "To pole jest wymagane."),
            ("Incorrect access_granted_for_schedule field - value outside the "
             "permissible choice", {"access_granted_for_schedule": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),
        ]
    )
    def test_add_credit_unsuccessful_with_incorrect_data(
            self,
            name: str,
            new_payload: dict,
            field_message: str,
    ):
        """Test creating a credit is not successful if data is incorrect."""
        payload = self.payload
        for key, value in new_payload.items():
            payload[key] = value
        self.client.force_login(self.user)
        credit_names = list(Credit.objects.filter(
            user=self.credit.user).values_list("name", flat=True))
        response_post = self.client.post(
            reverse("credit:add-credit"),
            data=payload,
            credit_names=credit_names)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode(encoding="UTF-8"))
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_credit_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot edit credit
        (user is redirected to login page)."""
        response = self.client.get(
            reverse("credit:edit-credit", args=[self.credit.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_credit_200_if_logged_in(self):
        """Test if edit_credit page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit", args=[self.credit.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_credit_correct_template_if_logged_in(self):
        """Test if edit_credit page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit", args=[self.credit.id]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_edit_credit_form_initial_values_set_context_data(self):
        """Test if edit_credit page displays correct context data."""
        credit_names = list(Credit.objects.filter(
            user=self.user).exclude(id=self.credit.id).values_list("name", flat=True))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit", args=[str(self.credit.id)]))
        self.assertEqual(response_get.context["page"], "edit-credit")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertQuerysetEqual(response_get.context["credit_names"], credit_names)
        self.assertIsInstance(response_get.context["form"], CreditForm)

    def test_edit_credit_form_initial_values_set_form_data(self):
        """Test if edit_credit page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit",
                    args=[str(self.credit.id)]))
        self.assertIn(self.credit.credit_number, response_get.content.decode())
        self.assertIn(self.credit.name, response_get.content.decode())

    def test_edit_credit_success_and_redirect(self):
        """Test if updating a credit is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        credit_names = list(Credit.objects.filter(
            user=self.user).exclude(
            id=self.credit.id).values_list(
            "name", flat=True))
        payload = self.payload

        self.assertNotEqual(self.credit.name, payload["name"])
        self.assertNotEqual(self.credit.credit_number, payload["credit_number"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("credit:edit-credit",
                    args=[str(self.credit.id)]),
            data=payload,
            instance=self.credit,
            credit_names=credit_names,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano kredyt.", str(messages[0]))
        self.credit.refresh_from_db()
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(self.credit.credit_number,
                         payload["credit_number"])
        self.assertEqual(self.credit.name, payload["name"])

    def test_edit_credit_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)
        credit_names = list(Credit.objects.filter(
            user=self.user).exclude(
            id=self.credit.id).values_list(
            "name", flat=True))

        # PATCH
        payload = {
            "name": "New credit",
            "credit_number": "Number of credit agreement",
            "access_granted": Access.ACCESS_GRANTED,
        }
        response_patch = self.client.patch(
            reverse("credit:edit-credit",
                    args=[str(self.credit.id)]),
            data=payload,
            instance=self.credit,
            credit_names=credit_names,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = self.payload
        response_put = self.client.put(
            reverse("credit:edit-credit",
                    args=[str(self.credit.id)]),
            data=payload,
            instance=self.credit,
            creditnames=credit_names,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:edit-credit",
                    args=[str(self.credit.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_credit_logout_if_security_breach(self):
        """Editing credit of another user is unsuccessful and triggers logout."""
        credit_names = list(Credit.objects.filter(
            user=self.user).exclude(
            id=self.credit.id).values_list(
            "name", flat=True))

        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_credit.user)
        self.assertIn("_auth_user_id", self.client.session)
        payload = self.payload
        payload["name"] = "SECURITY BREACH"
        payload["credit_number"] = "SECURITY BREACH"

        # Attempt to change data that belongs to test_user by user
        response_post = self.client.post(
            reverse("credit:edit-credit",
                    args=[str(self.test_credit.id)]),
            data=payload,
            content_type="text/html",
            credit_names=credit_names,
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
        self.assertEqual(Credit.objects.count(), 2)
        self.assertNotIn(self.test_credit.credit_number, payload["credit_number"])

    def test_delete_credit_302_redirect_if_unauthorized(self):
        """Test if delete_credit page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("credit:delete-credit", args=[self.credit.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_credit_200_if_logged_in(self):
        """Test if delete_credit page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit", args=[self.credit.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_credit_correct_template_if_logged_in(self):
        """Test if delete_credit page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit", args=[self.credit.id]))
        self.assertTemplateUsed(response_get,
                                "credit/credit_delete_form.html")

    def test_delete_credit_initial_values_set_context_data(self):
        """Test if delete_credit page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:delete-credit", args=[str(self.credit.id)]))
        self.assertIn(str(self.credit), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-credit")
        self.assertEqual(response_get.context["credit"], self.credit)

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_delete_credit_successful_and_redirect(self):
        """Deleting credit is successful (status code 200) and redirect
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
        self.assertEqual(Credit.objects.filter(user=self.user).count(), 1)
        self.client.force_login(self.user)

        response_get = self.client.get(reverse(
            "credit:delete-credit", args=[str(self.credit.id)]))
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response_get,
                                template_name="credit/credit_delete_form.html")
        self.assertIn(self.credit.name, response_get.content.decode())

        response_delete = self.client.post(
            reverse("credit:delete-credit", args=[str(self.credit.id)]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("credit:credits"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto kredyt wraz z informacjami dodatkowymi.",
                      str(messages[0]))
        self.assertFalse(os.path.exists(credit_file_path))

        response = self.client.get(reverse("credit:credits"))
        self.assertEqual(Credit.objects.count(), 1)
        self.assertNotIn(self.credit.name, response.content.decode())
        self.assertNotIn(self.test_credit.name, response.content.decode())

        self.assertEqual(Credit.objects.filter(user=self.user).count(), 0)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Credit.objects.count(), 1)
        self.assertEqual(CreditTranche.objects.count(), 1)
        self.assertEqual(CreditInterestRate.objects.count(), 1)
        self.assertEqual(CreditInsurance.objects.count(), 1)
        self.assertEqual(CreditCollateral.objects.count(), 1)
        self.assertEqual(CreditAdditionalCost.objects.count(), 1)
        self.assertEqual(CreditEarlyRepayment.objects.count(), 1)
        self.assertEqual(Counterparty.objects.count(), 1)

    def test_delete_credit_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("credit:delete-credit", args=[str(self.credit.id)]),
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("credit:delete-credit", args=[str(self.credit.id)]),
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:delete-credit", args=[str(self.credit.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_credit_logout_if_security_breach(self):
        """Deleting credit of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_credit.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("credit:delete-credit",
                    args=[str(self.test_credit.id)]),
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
        self.assertEqual(Credit.objects.count(), 2)


class CreditTrancheTests(TestCase):
    """Test CreditTranche views."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)

        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.profile = Profile.objects.get(user=self.user)

        self.credit = CreditFactory(user=self.user)
        self.tranche = CreditTrancheFactory(
            user=self.user, credit=self.credit,
            tranche_date=datetime.date(2020, 2, 1))

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com",
            password="testpass456")
        self.test_credit = CreditFactory(
            user=self.test_user, name="test credit", credit_number="ABCD1234")
        self.test_tranche = CreditTrancheFactory(
            user=self.test_user, credit=self.test_credit,
            tranche_amount=333, tranche_date=datetime.date(2020, 6, 1))

        self.payload = {
            "tranche_amount": 30000,
            "tranche_date": datetime.date(2020, 7, 1),
            "total_installment": "",
            "capital_installment": "",
        }

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def tearDown(self):
        if os.path.exists(settings.TEST_ROOT):
            shutil.rmtree(settings.TEST_ROOT)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(CreditTranche.objects.count(), 2)

    def test_add_credit_tranche_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add credit tranche
        (user is redirected to login page)."""
        response = self.client.get(reverse("credit:add-credit-tranche",
                                           args=[str(self.credit.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_credit_tranche_result_200_if_logged_in(self):
        """Test if add_credit_tranche page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-tranche",
                                               args=[str(self.credit.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_credit_tranche_correct_template_if_logged_in(self):
        """Test if add_credit_tranche page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-tranche",
                                               args=[str(self.credit.id)]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_add_credit_tranche_form_initial_values_set_context_data(self):
        """Test if add_credit_tranche page displays correct context data."""
        queryset = CreditTranche.objects.filter(credit=self.credit.id)
        sum_of_tranches = CreditTranche.total_tranche(queryset)
        dates_of_tranches = list(queryset.exclude(id=self.credit.id).values_list(
            "tranche_date", flat=True))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-tranche",
                                               args=[str(self.credit.id)]))
        self.assertEqual(response_get.context["page"], "add-credit-tranche")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertQuerysetEqual(response_get.context["queryset"], queryset)
        self.assertEqual(response_get.context["sum_of_tranches"], sum_of_tranches)
        self.assertEqual(response_get.context["dates_of_tranches"], dates_of_tranches)
        self.assertIsInstance(response_get.context["form"], CreditTrancheForm)

    def test_add_credit_tranche_form_initial_values_set_form_data(self):
        """Test if add_credit_tranche page displays correct form data."""
        tranche_fields = ["tranche_amount",  "tranche_date",
                          "total_installment", "capital_installment"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-tranche",
                                               args=[str(self.credit.id)]))
        for field in tranche_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_credit_tranche_success_and_redirect(self):
        """Test if creating credit tranche is successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(CreditTranche.objects.count(), 2)
        payload = self.payload
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "credit:add-credit-tranche", args=[str(self.credit.id)]),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano informacje związane z transzą.",  str(messages[0]))
        self.assertInHTML("1 lipca 2020", response_post.content.decode())
        self.assertEqual(CreditTranche.objects.count(), 3)
        self.assertTrue(CreditTranche.objects.filter(
            user=self.user, tranche_amount=payload["tranche_amount"]).exists())

    def test_add_credit_tranche_successful_with_correct_user(self):
        """Test if creating credit tranche successfully has correct user."""
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-tranche", args=[str(self.credit.id)]),
            payload,
            follow=True)

        tranche = CreditTranche.objects.get(tranche_amount=payload["tranche_amount"])
        self.assertEqual(tranche.user, self.user)

    def test_add_credit_tranche_successful_with_correct_credit(self):
        """Test if creating credit tranche successfully has correct
        credit as foreign key."""
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-tranche", args=[str(self.credit.id)]),
            payload,
            follow=True)

        tranche = CreditTranche.objects.get(tranche_amount=payload["tranche_amount"])
        self.assertEqual(tranche.credit, self.credit)
        self.assertNotEqual(tranche.credit, self.test_credit)

    @parameterized.expand(
        [
            ("Empty field: tranche_amount", {"tranche_amount": ""},
             "To pole jest wymagane."),
            ("Incorrect tranche_amount field (negative values are not allowed)",
             {"tranche_amount": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect tranche_amount field - max 2 decimal places",
             {"tranche_amount": 112000.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),

            ("Empty field: tranche_date", {"tranche_date": ""},
             "To pole jest wymagane."),
            ("Incorrect tranche_date field (incorrect data)",
             {"tranche_date": "2020, 11, 11"}, "Wpisz poprawną datę."),

            ("Incorrect total_installment field (negative values are not allowed)",
             {"total_installment": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect total_installment field - max 2 decimal places",
             {"total_installment": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect total_installment field - max 8 digits",
             {"total_installment": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),

            ("Incorrect capital_installment field (negative values are not allowed)",
             {"capital_installment": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect capital_installment field - max 2 decimal places",
             {"capital_installment": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect capital_installment field - max 8 digits",
             {"capital_installment": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),
        ]
    )
    def test_add_credit_tranche_unsuccessful_with_incorrect_data(
            self,
            name: str,
            new_payload: dict,
            field_message: str,
    ):
        """Test creating credit tranche is not successful if data is incorrect."""
        self.assertEqual(CreditTranche.objects.count(), 2)
        self.client.force_login(self.user)
        payload = self.payload
        for key, value in new_payload.items():
            payload[key] = value

        response_post = self.client.post(
            reverse("credit:add-credit-tranche", args=[str(self.credit.id)]),
            payload)
        self.assertEqual(CreditTranche.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_credit_tranche_302_redirect_if_unauthorized(self):
        """Test if edit_credit_tranche page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("credit:edit-credit-tranche", args=[self.tranche.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_credit_tranche_200_if_logged_in(self):
        """Test if edit_credit_tranche page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-tranche", args=[self.tranche.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_credit_tranche_correct_template_if_logged_in(self):
        """Test if edit_credit_tranche page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-tranche", args=[self.tranche.id]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_edit_credit_tranche_form_initial_values_set_context_data(self):
        """Test if edit_credit_tranche page displays correct context data."""
        credit_tranche = CreditTranche.objects.get(id=self.tranche.id)
        queryset = CreditTranche.objects.filter(credit=self.credit.id)
        sum_of_tranches = (CreditTranche.total_tranche(queryset)
                           - credit_tranche.tranche_amount)
        dates_of_tranches = list(queryset.exclude(id=self.tranche.id).values_list(
            "tranche_date", flat=True))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-tranche", args=[str(self.tranche.id)]))
        self.assertEqual(response_get.context["page"], "edit-credit-tranche")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertEqual(response_get.context["credit_tranche"], self.tranche)
        self.assertQuerysetEqual(response_get.context["queryset"], queryset)
        self.assertEqual(response_get.context["sum_of_tranches"], sum_of_tranches)
        self.assertEqual(response_get.context["dates_of_tranches"], dates_of_tranches)
        self.assertIsInstance(response_get.context["form"], CreditTrancheForm)

    def test_edit_credit_tranche_form_initial_values_set(self):
        """Test if edit_credit_tranche page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-tranche", args=[str(self.tranche.id)]))
        self.assertIn("01.02.2020", response_get.content.decode())
        self.assertIn("10000.00", response_get.content.decode())

    def test_edit_credit_tranche_success_and_redirect(self):
        """Test if updating credit tranche is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        self.assertEqual(CreditTranche.objects.count(), 2)
        queryset = CreditTranche.objects.filter(credit=self.credit.id)
        sum_of_tranches = (CreditTranche.total_tranche(queryset)
                           - self.tranche.tranche_amount)
        dates_of_tranches = list(queryset.exclude(id=self.tranche.id).values_list(
            "tranche_date", flat=True))
        payload = self.payload
        payload["tranche_date"] = datetime.date(2020, 2, 1)  # forms restriction: cannot change initial tranche date
        self.assertNotEqual(self.tranche.tranche_amount, payload["tranche_amount"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("credit:edit-credit-tranche", args=[str(self.tranche.id)]),
            data=payload,
            instance=self.tranche,
            sum_of_tranches=sum_of_tranches,
            dates_of_tranches=dates_of_tranches,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano informacje związane z transzą.", str(messages[0]))
        self.tranche.refresh_from_db()
        self.assertEqual(CreditTranche.objects.count(), 2)
        self.assertEqual(self.tranche.tranche_amount, payload["tranche_amount"])

    def test_edit_credit_tranche_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        queryset = CreditTranche.objects.filter(credit=self.credit.id)
        sum_of_tranches = (CreditTranche.total_tranche(queryset)
                           - self.tranche.tranche_amount)
        dates_of_tranches = list(
            queryset.exclude(id=self.tranche.id).values_list(
                "tranche_date", flat=True))
        self.client.force_login(self.user)

        # PATCH
        payload = {"tranche_amount": 20000}
        response_patch = self.client.patch(
            reverse("credit:edit-credit-tranche",
                    args=[str(self.tranche.id)]),
            data=payload,
            instance=self.tranche,
            sum_of_tranches=sum_of_tranches,
            dates_of_tranches=dates_of_tranches,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = self.payload
        response_put = self.client.put(
            reverse("credit:edit-credit-tranche",
                    args=[str(self.tranche.id)]),
            data=payload,
            instance=self.tranche,
            sum_of_tranches=sum_of_tranches,
            dates_of_tranches=dates_of_tranches,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:edit-credit-tranche",
                    args=[str(self.tranche.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_credit_tranche_logout_if_security_breach(self):
        """Editing credit tranche of another user is unsuccessful and
        triggers logout."""
        queryset = CreditTranche.objects.filter(credit=self.credit.id)
        sum_of_tranches = (CreditTranche.total_tranche(queryset)
                           - self.tranche.tranche_amount)
        dates_of_tranches = list(
            queryset.exclude(id=self.tranche.id).values_list(
                "tranche_date", flat=True))
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_tranche.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = self.payload

        # Attempt to change data that belongs to test_user by user
        response_post = self.client.post(
            reverse("credit:edit-credit-tranche",
                    args=[str(self.test_tranche.id)]),
            data=payload,
            content_type="text/html",
            sum_of_tranches=sum_of_tranches,
            dates_of_tranches=dates_of_tranches,
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
        self.assertEqual(CreditTranche.objects.count(), 2)
        self.assertNotEqual(self.test_tranche.tranche_amount,
                            payload["tranche_amount"])

    def test_delete_credit_tranche_302_redirect_if_unauthorized(self):
        """Test if delete_credit_tranche page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("credit:delete-credit-tranche", args=[self.tranche.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_credit_tranche_200_if_logged_in(self):
        """Test if delete_credit_tranche page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-tranche", args=[self.tranche.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_credit_tranche_correct_template_if_logged_in(self):
        """Test if delete_credit_tranche page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-tranche", args=[self.tranche.id]))
        self.assertTemplateUsed(response_get,
                                "credit/credit_delete_form.html")

    def test_delete_credit_tranche_initial_values_set_context_data(self):
        """Test if delete_credit_tranche page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:delete-credit-tranche", args=[str(self.tranche.id)]))
        self.assertIn("1 lutego 2020", response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-credit-tranche")
        self.assertEqual(response_get.context["credit_tranche"], self.tranche)
        self.assertEqual(response_get.context["credit"], self.credit)

    def test_delete_credit_tranche_successful_and_redirect(self):
        """Deleting credit tranche is successful (status code 200) and redirect
        is successful (status code 302)."""
        another_tranche = CreditTranche.objects.create(
            user=self.user, credit=self.credit, tranche_amount=15000,
            tranche_date=datetime.date(2020, 9, 1))
        self.assertEqual(CreditTranche.objects.count(), 3)

        self.client.force_login(self.user)
        response = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertIn("1 września 2020", response.content.decode())
        self.assertIn("1 lutego 2020", response.content.decode())

        response_delete = self.client.post(
            reverse("credit:delete-credit-tranche", args=[str(another_tranche.id)]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto transzę.", str(messages[0]))

        response = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertEqual(CreditTranche.objects.count(), 2)
        self.assertNotIn("1 września 2020", response.content.decode())
        self.assertIn("1 lutego 2020", response.content.decode())

    def test_delete_credit_tranche_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        another_tranche = CreditTranche.objects.create(
            user=self.user, credit=self.credit, tranche_amount=15000,
            tranche_date=datetime.date(2020, 9, 1))
        self.assertEqual(CreditTranche.objects.count(), 3)
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("credit:delete-credit-tranche",
                    args=[str(another_tranche.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("credit:delete-credit-tranche",
                    args=[str(another_tranche.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:delete-credit-tranche",
                    args=[str(another_tranche.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_credit_tranche_logout_if_security_breach(self):
        """Deleting credit tranche of another user is unsuccessful and
        triggers logout."""
        another_tranche = CreditTranche.objects.create(
            user=self.test_user, credit=self.credit, tranche_amount=15000,
            tranche_date=datetime.date(2020, 9, 1))
        self.assertEqual(CreditTranche.objects.count(), 3)
        self.assertNotEqual(self.user, self.test_tranche.user)
        self.client.force_login(self.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("credit:delete-credit-tranche",
                    args=[str(another_tranche.id)]),
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
        self.assertEqual(CreditTranche.objects.count(), 3)


class CreditInterestRateTests(TestCase):
    """Test CreditInterestRate views."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)

        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.profile = Profile.objects.get(user=self.user)

        self.credit = CreditFactory(user=self.user)
        self.interest_rate = CreditInterestRateFactory(user=self.user,
                                                       credit=self.credit)

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com",
            password="testpass456")
        self.test_credit = CreditFactory(
            user=self.test_user, name="test credit", credit_number="ABCD1234")
        self.test_interest_rate = CreditInterestRateFactory(
            user=self.test_user, credit=self.test_credit, interest_rate=12.3,
            note="test rate")

        self.payload = {
            "interest_rate": 7.89,
            "interest_rate_start_date": datetime.date(2021, 11, 1),
            "note": "New interest rate",
            "total_installment": "",
            "capital_installment": "",
        }

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def tearDown(self):
        if os.path.exists(settings.TEST_ROOT):
            shutil.rmtree(settings.TEST_ROOT)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(CreditInterestRate.objects.count(), 2)

    def test_add_interest_rate_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add interest rate
        (user is redirected to login page)."""
        response = self.client.get(reverse("credit:add-credit-interest-rate",
                                           args=[str(self.credit.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_interest_rate_result_200_if_logged_in(self):
        """Test if add_interest_rate page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-interest-rate",
                                               args=[str(self.credit.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_interest_rate_correct_template_if_logged_in(self):
        """Test if add_interest_rate page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-interest-rate",
                                               args=[str(self.credit.id)]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_add_interest_rate_form_initial_values_set_context_data(self):
        """Test if add_interest_rate page displays correct context data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-interest-rate",
                                               args=[str(self.credit.id)]))
        self.assertEqual(response_get.context["page"], "add-credit-interest-rate")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertEqual(response_get.context["installment_type"],
                         self.credit.installment_type)
        self.assertEqual(response_get.context["start_of_payment"],
                         self.credit.start_of_payment)
        self.assertEqual(response_get.context["payment_day"], self.credit.payment_day)
        self.assertIsInstance(response_get.context["form"], CreditInterestRateForm)

    def test_add_interest_rate_form_initial_values_set_form_data(self):
        """Test if add_interest_rate page displays correct form data."""
        rate_fields = ["interest_rate", "interest_rate_start_date", "note",
                       "total_installment", "capital_installment"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-interest-rate",
                                               args=[str(self.credit.id)]))
        for field in rate_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_interest_rate_success_and_redirect(self):
        """Test if creating interest rate is successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(CreditInterestRate.objects.count(), 2)
        payload = self.payload
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "credit:add-credit-interest-rate", args=[str(self.credit.id)]),
            data=payload,
            installment_type=self.credit.installment_type,
            start_of_payment=self.credit.start_of_payment,
            payment_day=self.credit.payment_day,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano informacje związane z oprocentowaniem zmiennym.",
                      str(messages[0]))
        self.assertInHTML("New interest rate",
                          response_post.content.decode())
        self.assertEqual(CreditInterestRate.objects.count(), 3)
        self.assertTrue(CreditInterestRate.objects.filter(
            user=self.user, interest_rate=payload["interest_rate"]).exists())

    def test_add_interest_rate_successful_with_correct_user(self):
        """Test if creating interest rate successfully has correct user."""
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-interest-rate", args=[str(self.credit.id)]),
            payload,
            installment_type=self.credit.installment_type,
            start_of_payment=self.credit.start_of_payment,
            payment_day=self.credit.payment_day,
            follow=True)

        rate = CreditInterestRate.objects.get(interest_rate=payload["interest_rate"])
        self.assertEqual(rate.user, self.user)

    def test_add_interest_rate_successful_with_correct_credit(self):
        """Test if creating interest rate successfully has correct
        credit as foreign key."""
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-interest-rate", args=[str(self.credit.id)]),
            payload,
            installment_type=self.credit.installment_type,
            start_of_payment=self.credit.start_of_payment,
            payment_day=self.credit.payment_day,
            follow=True)

        rate = CreditInterestRate.objects.get(interest_rate=payload["interest_rate"])
        self.assertEqual(rate.credit, self.credit)
        self.assertNotEqual(rate.credit, self.test_credit)

    @parameterized.expand(
        [
            ("Empty field: interest_rate", {"interest_rate": ""},
             "To pole jest wymagane."),
            ("Incorrect interest_rate field (negative values are not allowed)",
             {"interest_rate": -4.2}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect interest_rate field - max 2 decimal places",
             {"interest_rate": 1.986},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect interest_rate field - max 4 digits",
             {"interest_rate": 111.22},
             "Upewnij się, że łącznie nie ma więcej niż 4 cyfry."),

            ("Empty field: interest_rate_start_date", {"interest_rate_start_date": ""},
             "To pole jest wymagane."),
            ("Incorrect interest_rate_start_date field (incorrect data)",
             {"interest_rate_start_date": "2020, 11, 11"}, "Wpisz poprawną datę."),

            ("Incorrect total_installment field (negative values are not allowed)",
             {"total_installment": -456},
             "Wartość nie może być liczbą ujemną."),
            ("Incorrect total_installment field - max 2 decimal places",
             {"total_installment": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect total_installment field - max 8 digits",
             {"total_installment": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),

            ("Incorrect capital_installment field (negative values are not allowed)",
             {"capital_installment": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect capital_installment field - max 2 decimal places",
             {"capital_installment": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect capital_installment field - max 8 digits",
             {"capital_installment": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),
        ]
    )
    def test_add_interest_rate_unsuccessful_with_incorrect_data(
            self,
            name: str,
            new_payload: dict,
            field_message: str,
    ):
        """Test creating interest rate is not successful if data is incorrect."""
        self.assertEqual(CreditInterestRate.objects.count(), 2)
        self.client.force_login(self.user)
        payload = self.payload
        for key, value in new_payload.items():
            payload[key] = value

        response_post = self.client.post(
            reverse("credit:add-credit-interest-rate",
                    args=[str(self.credit.id)]),
            payload,
            installment_type=self.credit.installment_type,
            start_of_payment=self.credit.start_of_payment,
            payment_day=self.credit.payment_day,
        )
        self.assertEqual(CreditInterestRate.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_interest_rate_302_redirect_if_unauthorized(self):
        """Test if edit_interest_rate page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("credit:edit-credit-interest-rate",
                    args=[self.interest_rate.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_interest_rate_200_if_logged_in(self):
        """Test if edit_interest_rate page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-interest-rate",
                    args=[self.interest_rate.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_interest_rate_correct_template_if_logged_in(self):
        """Test if edit_interest_rate page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-interest-rate",
                    args=[self.interest_rate.id]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_edit_interest_rate_form_initial_values_set_context_data(self):
        """Test if edit_interest_rate page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-interest-rate",
                    args=[str(self.interest_rate.id)]))
        self.assertEqual(response_get.context["page"],
                         "edit-credit-interest-rate")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertEqual(response_get.context["credit_interest_rate"],
                         self.interest_rate)
        self.assertEqual(response_get.context["installment_type"],
                         self.credit.installment_type)
        self.assertEqual(response_get.context["start_of_payment"],
                         self.credit.start_of_payment)
        self.assertEqual(response_get.context["payment_day"],
                         self.credit.payment_day)
        self.assertIsInstance(response_get.context["form"],
                              CreditInterestRateForm)

    def test_edit_interest_rate_form_initial_values_set(self):
        """Test if edit_interest_rate page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-interest-rate",
                    args=[str(self.interest_rate.id)]))
        self.assertIn(self.interest_rate.note, response_get.content.decode())

    def test_edit_interest_rate_success_and_redirect(self):
        """Test if updating interest rate is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        self.assertEqual(CreditInterestRate.objects.count(), 2)
        payload = self.payload
        self.assertNotEqual(self.interest_rate.interest_rate,
                            payload["interest_rate"])
        self.assertNotEqual(self.interest_rate.note, payload["note"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("credit:edit-credit-interest-rate",
                    args=[str(self.interest_rate.id)]),
            data=payload,
            instance=self.interest_rate,
            installment_type=self.credit.installment_type,
            start_of_payment=self.credit.start_of_payment,
            payment_day=self.credit.payment_day,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano informacje związane z oprocentowaniem "
                      "zmiennym.", str(messages[0]))
        self.interest_rate.refresh_from_db()
        self.assertEqual(CreditInterestRate.objects.count(), 2)
        self.assertEqual(float(self.interest_rate.interest_rate),
                         round(payload["interest_rate"], 2))
        self.assertEqual(self.interest_rate.note, payload["note"])

    def test_edit_interest_rate_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "interest_rate": 1.1,
            "interest_rate_start_date": datetime.date(2021, 12, 1),
        }
        response_patch = self.client.patch(
            reverse("credit:edit-credit-interest-rate",
                    args=[str(self.interest_rate.id)]),
            data=payload,
            instance=self.interest_rate,
            installment_type=self.credit.installment_type,
            start_of_payment=self.credit.start_of_payment,
            payment_day=self.credit.payment_day,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = self.payload
        response_put = self.client.put(
            reverse("credit:edit-credit-interest-rate",
                    args=[str(self.interest_rate.id)]),
            data=payload,
            instance=self.interest_rate,
            installment_type=self.credit.installment_type,
            start_of_payment=self.credit.start_of_payment,
            payment_day=self.credit.payment_day,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:edit-credit-interest-rate",
                    args=[str(self.interest_rate.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_interest_rate_logout_if_security_breach(self):
        """Editing interest_rate of another user is unsuccessful and t
        riggers logout."""
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_interest_rate.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = self.payload

        # Attempt to change data that belongs to test_user by user
        response_post = self.client.post(
            reverse("credit:edit-credit-interest-rate",
                    args=[str(self.test_interest_rate.id)]),
            data=payload,
            content_type="text/html",
            installment_type=self.credit.installment_type,
            start_of_payment=self.credit.start_of_payment,
            payment_day=self.credit.payment_day,
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
        self.assertEqual(CreditInterestRate.objects.count(), 2)
        self.assertNotIn(self.test_interest_rate.note, payload["note"])

    def test_delete_interest_rate_302_redirect_if_unauthorized(self):
        """Test if delete_interest_rate page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("credit:delete-credit-interest-rate",
                    args=[self.interest_rate.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_interest_rate_200_if_logged_in(self):
        """Test if delete_interest_rate page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-interest-rate",
                    args=[self.interest_rate.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_interest_rate_correct_template_if_logged_in(self):
        """Test if delete_interest_rate page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-interest-rate",
                    args=[self.interest_rate.id]))
        self.assertTemplateUsed(response_get,
                                "credit/credit_delete_form.html")

    def test_delete_interest_rate_initial_values_set_context_data(self):
        """Test if delete_interest_rate page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:delete-credit-interest-rate",
                    args=[str(self.interest_rate.id)]))
        self.assertIn(str(self.interest_rate.interest_rate),
                      response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-credit-interest-rate")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertEqual(response_get.context["interest_rate"], self.interest_rate)

    def test_delete_interest_rate_successful_and_redirect(self):
        """Deleting interest rate is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(CreditInterestRate.objects.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("credit:single-credit",
                    args=[str(self.credit.id)]))
        self.assertIn("1 sierpnia 2020", response.content.decode())

        response_delete = self.client.post(
            reverse("credit:delete-credit-interest-rate",
                    args=[str(self.interest_rate.id)]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto oprocentowanie.", str(messages[0]))

        response = self.client.get(
            reverse("credit:single-credit",
                    args=[str(self.credit.id)]))
        self.assertEqual(CreditInterestRate.objects.count(), 1)
        self.assertNotIn(self.interest_rate.note, response.content.decode())
        self.assertNotIn(self.test_interest_rate.note, response.content.decode())

    def test_delete_interest_rate_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("credit:delete-credit-interest-rate",
                    args=[str(self.interest_rate.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("credit:delete-credit-interest-rate",
                    args=[str(self.interest_rate.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:delete-credit-interest-rate",
                    args=[str(self.interest_rate.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_interest_rate_logout_if_security_breach(self):
        """Deleting interest rate of another user is unsuccessful and
        triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(CreditInterestRate.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_interest_rate.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("credit:delete-credit-interest-rate",
                    args=[str(self.test_interest_rate.id)]),
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
        self.assertEqual(CreditInterestRate.objects.count(), 2)


class CreditInsuranceTests(TestCase):
    """Test CreditInsurance views."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)

        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.profile = Profile.objects.get(user=self.user)

        self.credit = CreditFactory(user=self.user)
        self.insurance = CreditInsuranceFactory(user=self.user,
                                                credit=self.credit)

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com",
            password="testpass456")
        self.test_credit = CreditFactory(
            user=self.test_user, name="test credit", credit_number="ABCD1234")
        self.test_insurance = CreditInsuranceFactory(
            user=self.test_user, credit=self.test_credit, amount=999,
            frequency="Półroczne")

        self.payload = {
            "type": "",
            "amount": 876,
            "frequency": "Kwartalne",
            "start_date": datetime.date(2022, 10, 10),
            "end_date": datetime.date(2024, 10, 10),
            "payment_period": 8,
        }

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def tearDown(self):
        if os.path.exists(settings.TEST_ROOT):
            shutil.rmtree(settings.TEST_ROOT)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(CreditInsurance.objects.count(), 2)

    def test_add_credit_insurance_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add credit insurance
        (user is redirected to login page)."""
        response = self.client.get(reverse("credit:add-credit-insurance",
                                           args=[str(self.credit.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_credit_insurance_result_200_if_logged_in(self):
        """Test if add_credit_insurance page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-insurance",
                                               args=[str(self.credit.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_credit_insurance_correct_template_if_logged_in(self):
        """Test if add_credit_insurance page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-insurance",
                                               args=[str(self.credit.id)]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_add_credit_insurance_form_initial_values_set_context_data(self):
        """Test if add_credit_insurance page displays correct context data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-insurance",
                                               args=[str(self.credit.id)]))
        self.assertEqual(response_get.context["page"], "add-credit-insurance")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertEqual(response_get.context["start_of_credit"],
                         self.credit.start_of_credit)
        self.assertIsInstance(response_get.context["form"], CreditInsuranceForm)

    def test_add_credit_insurance_form_initial_values_set_form_data(self):
        """Test if add_credit_insurance page displays correct form data."""
        insurance_fields = ["type", "amount", "frequency",  "start_date",
                            "end_date", "payment_period"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-insurance",
                                               args=[str(self.credit.id)]))
        for field in insurance_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_credit_insurance_success_and_redirect(self):
        """Test if creating credit insurance is successful (status code 200) and
        redirecting is successful (status code 302)."""
        start_of_credit = self.credit.start_of_credit
        self.assertEqual(CreditInsurance.objects.count(), 2)
        payload = self.payload
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "credit:add-credit-insurance", args=[str(self.credit.id)]),
            data=payload,
            start_of_credit=start_of_credit,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano informacje związane z ubezpieczeniem.",
                      str(messages[0]))
        self.assertInHTML("10 października 2022",
                          response_post.content.decode())
        self.assertEqual(CreditInsurance.objects.count(), 3)
        self.assertTrue(CreditInsurance.objects.filter(
            user=self.user, start_date=payload["start_date"]).exists())

    def test_add_credit_insurance_successful_with_correct_user(self):
        """Test if creating credit insurance successfully has correct user."""
        start_of_credit = self.credit.start_of_credit
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-insurance", args=[str(self.credit.id)]),
            payload,
            start_of_credit=start_of_credit,
            follow=True)

        insurance = CreditInsurance.objects.get(start_date=payload["start_date"])
        self.assertEqual(insurance.user, self.user)

    def test_add_credit_insurance_successful_with_correct_credit(self):
        """Test if creating credit insurance successfully has correct
        credit as foreign key."""
        start_of_credit = self.credit.start_of_credit
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-insurance", args=[str(self.credit.id)]),
            payload,
            start_of_credit=start_of_credit,
            follow=True)

        insurance = CreditInsurance.objects.get(start_date=payload["start_date"])
        self.assertEqual(insurance.credit, self.credit)
        self.assertNotEqual(insurance.credit, self.test_credit)

    @parameterized.expand(
        [
            ("Empty field: amount", {"amount": ""}, "To pole jest wymagane."),
            ("Empty field: start_date", {"start_date": ""}, "To pole jest wymagane."),

            ("Incorrect amount field (negative values are not allowed)",
             {"amount": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect amount field - max 2 decimal places",
             {"amount": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect amount field - max 8 digits", {"amount": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),

            ("Incorrect frequency field - value outside the permissible choice",
             {"frequency": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),
            ("Incorrect type field - value outside the permissible choice",
             {"type": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),

            ("Incorrect start_date field (incorrect data)",
             {"start_date": "2020, 11, 11"}, "Wpisz poprawną datę."),
            ("Incorrect end_date field (incorrect data)",
             {"end_date": "2020, 11, 11"}, "Wpisz poprawną datę."),
        ]
    )
    def test_add_credit_insurance_unsuccessful_with_incorrect_data(
            self,
            name: str,
            new_payload: dict,
            field_message: str,
    ):
        """Test creating credit insurance is not successful if data is incorrect."""
        self.assertEqual(CreditInsurance.objects.count(), 2)
        start_of_credit = self.credit.start_of_credit
        payload = self.payload
        for key, value in new_payload.items():
            payload[key] = value
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("credit:add-credit-insurance",
                    args=[str(self.credit.id)]),
            data=payload,
            start_of_credit=start_of_credit,
        )
        self.assertEqual(CreditInsurance.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_credit_insurance_302_redirect_if_unauthorized(self):
        """Test if edit_credit_insurance page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("credit:edit-credit-insurance", args=[self.insurance.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_credit_insurance_200_if_logged_in(self):
        """Test if edit_credit_insurance page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-insurance", args=[self.insurance.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_credit_insurance_correct_template_if_logged_in(self):
        """Test if edit_credit_insurance page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-insurance", args=[self.insurance.id]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_edit_credit_insurance_form_initial_values_set_context_data(self):
        """Test if edit_credit_insurance page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-insurance", args=[str(self.insurance.id)]))
        self.assertEqual(response_get.context["page"], "edit-credit-insurance")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertEqual(response_get.context["credit_insurance"], self.insurance)
        self.assertEqual(response_get.context["start_of_credit"],
                         self.credit.start_of_credit)
        self.assertIsInstance(response_get.context["form"], CreditInsuranceForm)

    def test_edit_credit_insurance_form_initial_values_set(self):
        """Test if edit_credit_insurance page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-insurance", args=[str(self.insurance.id)]))
        self.assertIn(self.insurance.type, response_get.content.decode())
        self.assertIn(self.insurance.frequency, response_get.content.decode())

    def test_edit_credit_insurance_success_and_redirect(self):
        """Test if updating credit insurance is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        payload = self.payload
        self.assertNotEqual(self.insurance.frequency, payload["frequency"])
        self.assertNotEqual(self.insurance.start_date, payload["start_date"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("credit:edit-credit-insurance",
                    args=[str(self.insurance.id)]),
            data=payload,
            instance=self.insurance,
            start_of_credit=self.credit.start_of_credit,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano informacje związane z ubezpieczeniem.",
                      str(messages[0]))
        self.insurance.refresh_from_db()
        self.assertEqual(CreditInsurance.objects.count(), 2)
        self.assertEqual(self.insurance.frequency, payload["frequency"])
        self.assertEqual(self.insurance.start_date, payload["start_date"])

    def test_edit_credit_insurance_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "amount": 855,
            "frequency": "Kwartalne",
        }
        response_patch = self.client.patch(
            reverse("credit:edit-credit-insurance",
                    args=[str(self.insurance.id)]),
            data=payload,
            instance=self.insurance,
            start_of_credit=self.credit.start_of_credit,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = self.payload
        response_put = self.client.put(
            reverse("credit:edit-credit-insurance",
                    args=[str(self.insurance.id)]),
            data=payload,
            instance=self.insurance,
            start_of_credit=self.credit.start_of_credit,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:edit-credit-insurance",
                    args=[str(self.insurance.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_credit_insurance_logout_if_security_breach(self):
        """Editing credit_insurance of another user is unsuccessful and
        triggers logout."""
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_insurance.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = self.payload

        # Attempt to change data that belongs to test_user by user
        response_post = self.client.post(
            reverse("credit:edit-credit-insurance",
                    args=[str(self.test_insurance.id)]),
            data=payload,
            content_type="text/html",
            instance=self.test_insurance,
            start_of_credit=self.credit.start_of_credit,
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
        self.assertEqual(CreditInsurance.objects.count(), 2)
        self.assertNotIn(self.test_insurance.frequency, payload["frequency"])

    def test_delete_credit_insurance_302_redirect_if_unauthorized(self):
        """Test if delete_credit_insurance page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("credit:delete-credit-insurance", args=[self.insurance.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_credit_insurance_200_if_logged_in(self):
        """Test if delete_credit_insurance page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-insurance", args=[self.insurance.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_credit_insurance_correct_template_if_logged_in(self):
        """Test if delete_credit_insurance page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-insurance", args=[self.insurance.id]))
        self.assertTemplateUsed(response_get,
                                "credit/credit_delete_form.html")

    def test_delete_credit_insurance_initial_values_set_context_data(self):
        """Test if delete_credit_insurance page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:delete-credit-insurance", args=[str(self.insurance.id)]))
        self.assertEqual(response_get.context["page"], "delete-credit-insurance")
        self.assertEqual(response_get.context["credit_insurance"], self.insurance)
        self.assertEqual(response_get.context["credit"], self.credit)

    def test_delete_credit_insurance_successful_and_redirect(self):
        """Deleting credit insurance is successful (status code 200) and redirect
        is successful (status code 302)."""
        new_insurance = CreditInsurance.objects.create(
            user=self.user, credit=self.credit, type="Ubezpieczenie na życie",
            amount=876, frequency="Kwartalne", start_date=datetime.date(2022, 10, 10),
            end_date=datetime.date(2024, 10, 10), payment_period=8
        )
        self.assertEqual(CreditInsurance.objects.count(), 3)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertIn(new_insurance.frequency, response.content.decode())
        self.assertIn(new_insurance.type, response.content.decode())

        response_delete = self.client.post(
            reverse("credit:delete-credit-insurance", args=[str(new_insurance.id)]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto ubezpieczenie.", str(messages[0]))

        response = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertEqual(CreditInsurance.objects.count(), 2)
        self.assertNotIn(new_insurance.frequency, response.content.decode())
        self.assertIn(self.insurance.frequency, response.content.decode())
        self.assertNotIn(self.test_insurance.frequency, response.content.decode())

    def test_delete_credit_insurance_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("credit:delete-credit-insurance",
                    args=[str(self.insurance.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("credit:delete-credit-insurance",
                    args=[str(self.insurance.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:delete-credit-insurance",
                    args=[str(self.insurance.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_credit_insurance_logout_if_security_breach(self):
        """Deleting credit insurance of another user is unsuccessful and
        triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(CreditInsurance.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_insurance.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("credit:delete-credit-insurance",
                    args=[str(self.test_insurance.id)]),
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
        self.assertEqual(CreditInsurance.objects.count(), 2)


class CreditCollateralTests(TestCase):
    """Test CreditCollateral views."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)

        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.profile = Profile.objects.get(user=self.user)

        self.credit = CreditFactory(user=self.user)
        self.collateral = CreditCollateralFactory(user=self.user,
                                                  credit=self.credit)

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com",
            password="testpass456")
        self.test_credit = CreditFactory(
            user=self.test_user, name="test credit", credit_number="ABCD1234")
        self.test_collateral = CreditCollateralFactory(
            user=self.test_user, credit=self.test_credit,
            description="Additional land")

        self.payload = {
            "description": "New collateral",
            "collateral_value": 333333,
            "collateral_set_date": datetime.date(2021, 2, 2),
            "total_installment": "",
            "capital_installment": "",
        }

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def tearDown(self):
        if os.path.exists(settings.TEST_ROOT):
            shutil.rmtree(settings.TEST_ROOT)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(CreditCollateral.objects.count(), 2)

    def test_add_credit_collateral_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add collateral
        (user is redirected to login page)."""
        response = self.client.get(reverse("credit:add-credit-collateral",
                                           args=[str(self.credit.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_credit_collateral_result_200_if_logged_in(self):
        """Test if add_credit_collateral page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-collateral",
                                               args=[str(self.credit.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_credit_collateral_correct_template_if_logged_in(self):
        """Test if add_credit_collateral page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-collateral",
                                               args=[str(self.credit.id)]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_add_credit_collateral_form_initial_values_set_context_data(self):
        """Test if add_credit_collateral page displays correct context data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-collateral",
                                               args=[str(self.credit.id)]))
        self.assertEqual(response_get.context["page"], "add-credit-collateral")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertIsInstance(response_get.context["form"], CreditCollateralForm)

    def test_add_credit_collateral_form_initial_values_set_form_data(self):
        """Test if add_credit_collateral page displays correct form data."""
        collateral_fields = ["description", "collateral_value",
                             "collateral_set_date", "total_installment",
                             "capital_installment"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-collateral",
                                               args=[str(self.credit.id)]))
        for field in collateral_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_credit_collateral_success_and_redirect(self):
        """Test if creating collateral is successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(CreditCollateral.objects.count(), 2)
        payload = self.payload
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "credit:add-credit-collateral", args=[str(self.credit.id)]),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano informacje związane z zabezpieczeniem.",
                      str(messages[0]))
        self.assertInHTML("New collateral", response_post.content.decode())
        self.assertEqual(CreditCollateral.objects.count(), 3)
        self.assertTrue(CreditCollateral.objects.filter(
            user=self.user, description=payload["description"]).exists())

    def test_add_credit_collateral_successful_with_correct_user(self):
        """Test if creating credit collateral successfully has correct user."""
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-collateral", args=[str(self.credit.id)]),
            payload,
            follow=True)

        collateral = CreditCollateral.objects.get(description=payload["description"])
        self.assertEqual(collateral.user, self.user)

    def test_add_credit_collateral_successful_with_correct_credit(self):
        """Test if creating credit collateral successfully has correct
        credit as foreign key."""
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-collateral", args=[str(self.credit.id)]),
            payload,
            follow=True)

        collateral = CreditCollateral.objects.get(description=payload["description"])
        self.assertEqual(collateral.credit, self.credit)
        self.assertNotEqual(collateral.credit, self.test_credit)

    @parameterized.expand(
        [
            ("Incorrect collateral_value field (negative values are not allowed)",
             {"collateral_value": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect collateral_value field - max 2 decimal places",
             {"collateral_value": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),

            ("Incorrect total_installment field (negative values are not allowed)",
             {"total_installment": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect total_installment field - max 2 decimal places",
             {"total_installment": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect total_installment field - max 8 digits",
             {"total_installment": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),

            ("Incorrect capital_installment field (negative values are not allowed)",
             {"capital_installment": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect capital_installment field - max 2 decimal places",
             {"capital_installment": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect capital_installment field - max 8 digits ",
             {"capital_installment": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),

            ("Empty field: collateral_set_date", {"collateral_set_date": ""},
             "To pole jest wymagane."),
            ("Incorrect collateral_set_date field (incorrect data)",
             {"collateral_set_date": "2020, 11, 11"}, "Wpisz poprawną datę."),
        ]
    )
    def test_add_credit_collateral_unsuccessful_with_incorrect_data(
            self,
            name: str,
            new_payload: dict,
            field_message: str,
    ):
        """Test creating credit collateral is not successful if data is incorrect."""
        self.assertEqual(CreditCollateral.objects.count(), 2)
        self.client.force_login(self.user)
        payload = self.payload
        for key, value in new_payload.items():
            payload[key] = value

        response_post = self.client.post(
            reverse("credit:add-credit-collateral",
                    args=[str(self.credit.id)]),
            payload)
        self.assertEqual(CreditCollateral.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_credit_collateral_302_redirect_if_unauthorized(self):
        """Test if edit_credit_collateral page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("credit:edit-credit-collateral", args=[self.collateral.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_credit_collateral_200_if_logged_in(self):
        """Test if edit_credit_collateral page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-collateral", args=[self.collateral.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_credit_collateral_correct_template_if_logged_in(self):
        """Test if edit_credit_collateral page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-collateral", args=[self.collateral.id]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_edit_credit_collateral_form_initial_values_set_context_data(self):
        """Test if edit_credit_collateral page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-collateral", args=[str(self.collateral.id)]))
        self.assertEqual(response_get.context["page"], "edit-credit-collateral")
        self.assertEqual(response_get.context["credit_collateral"], self.collateral)
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertIsInstance(response_get.context["form"], CreditCollateralForm)

    def test_edit_credit_collateral_form_initial_values_set(self):
        """Test if edit_credit_collateral page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-collateral", args=[str(self.collateral.id)]))
        self.assertIn(self.collateral.description, response_get.content.decode())

    def test_edit_credit_collateral_success_and_redirect(self):
        """Test if updating credit collateral is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        payload = self.payload
        self.assertNotEqual(self.collateral.description, payload["description"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("credit:edit-credit-collateral",
                    args=[str(self.collateral.id)]),
            data=payload,
            instance=self.collateral,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano informacje związane z zabezpieczeniem.",
                      str(messages[0]))
        self.collateral.refresh_from_db()
        self.assertEqual(CreditCollateral.objects.count(), 2)
        self.assertEqual(self.collateral.description, payload["description"])

    def test_edit_credit_collateral_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "collateral_value": 333333,
            "collateral_set_date": datetime.date(2021, 2, 2)
        }
        response_patch = self.client.patch(
            reverse("credit:edit-credit-collateral",
                    args=[str(self.collateral.id)]),
            data=payload,
            instance=self.collateral,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = self.payload
        response_put = self.client.put(
            reverse("credit:edit-credit-collateral",
                    args=[str(self.collateral.id)]),
            data=payload,
            instance=self.collateral,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:edit-credit-collateral",
                    args=[str(self.collateral.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_credit_collateral_logout_if_security_breach(self):
        """Editing credit_collateral of another user is unsuccessful and
        triggers logout."""
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_collateral.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = self.payload

        # Attempt to change data that belongs to test_user by user
        response_post = self.client.post(
            reverse("credit:edit-credit-collateral",
                    args=[str(self.test_collateral.id)]),
            data=payload,
            content_type="text/html",
            instance=self.test_collateral,
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
        self.assertEqual(CreditCollateral.objects.count(), 2)
        self.assertNotIn(self.test_collateral.description, payload["description"])

    def test_delete_credit_collateral_302_redirect_if_unauthorized(self):
        """Test if delete_credit_collateral page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("credit:delete-credit-collateral", args=[self.collateral.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_credit_collateral_200_if_logged_in(self):
        """Test if delete_credit_collateral page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-collateral", args=[self.collateral.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_credit_collateral_correct_template_if_logged_in(self):
        """Test if delete_credit_collateral page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-collateral", args=[self.collateral.id]))
        self.assertTemplateUsed(response_get,
                                "credit/credit_delete_form.html")

    def test_delete_credit_collateral_initial_values_set_context_data(self):
        """Test if delete_credit_collateral page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:delete-credit-collateral",
                    args=[str(self.collateral.id)]))
        self.assertEqual(response_get.context["page"], "delete-credit-collateral")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertEqual(response_get.context["credit_collateral"], self.collateral)

    def test_delete_credit_collateral_successful_and_redirect(self):
        """Deleting credit collateral is successful (status code 200) and redirect
        is successful (status code 302)."""
        new_collateral = CreditCollateral.objects.create(
            user=self.user, credit=self.credit, description="New collateral",
            collateral_value=333333,
            collateral_set_date=datetime.date(2021, 2, 2))
        self.assertEqual(CreditCollateral.objects.count(), 3)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertIn(str(self.collateral.description), response.content.decode())
        self.assertIn(str(new_collateral.description), response.content.decode())

        response_delete = self.client.post(
            reverse("credit:delete-credit-collateral",
                    args=[str(new_collateral.id)]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto zabezpieczenie.", str(messages[0]))

        response = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertEqual(CreditCollateral.objects.count(), 2)
        self.assertIn(self.collateral.description, response.content.decode())
        self.assertNotIn(new_collateral.description, response.content.decode())
        self.assertNotIn(self.test_collateral.description,
                         response.content.decode())

    def test_delete_credit_collateral_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("credit:delete-credit-collateral",
                    args=[str(self.collateral.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("credit:delete-credit-collateral",
                    args=[str(self.collateral.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:delete-credit-collateral",
                    args=[str(self.collateral.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_credit_collateral_logout_if_security_breach(self):
        """Deleting credit collateral of another user is unsuccessful and
        triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(CreditCollateral.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_collateral.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("credit:delete-credit-collateral",
                    args=[str(self.test_collateral.id)]),
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
        self.assertEqual(CreditCollateral.objects.count(), 2)


class CreditAdditionalCostTests(TestCase):
    """Test CreditAdditionalCost views."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)

        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.profile = Profile.objects.get(user=self.user)

        self.credit = CreditFactory(user=self.user)
        self.cost = CreditAdditionalCostFactory(user=self.user,
                                                credit=self.credit)

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com",
            password="testpass456")
        self.test_credit = CreditFactory(
            user=self.test_user, name="test credit", credit_number="ABCD1234")
        self.test_cost = CreditAdditionalCostFactory(
            user=self.test_user, credit=self.test_credit, name="Notary")

        self.payload = {
            "name": "New credit cost",
            "cost_amount": 1100,
            "cost_payment_date": datetime.date(2021, 4, 4),
            "notes": "Mortgage costs",
        }

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def tearDown(self):
        if os.path.exists(settings.TEST_ROOT):
            shutil.rmtree(settings.TEST_ROOT)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)

    def test_add_credit_additional_cost_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add credit_additional_cost
        (user is redirected to login page)."""
        response = self.client.get(reverse("credit:add-credit-additional-cost",
                                           args=[str(self.credit.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_credit_additional_cost_result_200_if_logged_in(self):
        """Test if add_credit_additional_cost page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:add-credit-additional-cost",
                    args=[str(self.credit.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_credit_additional_cost_correct_template_if_logged_in(self):
        """Test if add_credit_additional_cost page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:add-credit-additional-cost",
                    args=[str(self.credit.id)]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_add_credit_additional_cost_form_initial_values_set_context_data(self):
        """Test if add_credit_additional_cost page displays correct context data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:add-credit-additional-cost",
                    args=[str(self.credit.id)]))
        self.assertEqual(response_get.context["page"], "add-credit-additional-cost")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertIsInstance(response_get.context["form"], CreditAdditionalCostForm)

    def test_add_credit_additional_cost_form_initial_values_set_form_data(self):
        """Test if add_credit_additional_cost page displays correct form data."""
        cost_fields = ["name", "cost_amount", "cost_payment_date", "notes"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:add-credit-additional-cost",
                    args=[str(self.credit.id)]))
        for field in cost_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_credit_additional_cost_success_and_redirect(self):
        """Test if creating credit additional cost is successful (status code
        200) and redirecting is successful (status code 302)."""
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)
        payload = self.payload
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "credit:add-credit-additional-cost", args=[str(self.credit.id)]),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano dodatkowe koszty kredytu.",
                      str(messages[0]))
        self.assertInHTML("New credit cost", response_post.content.decode())
        self.assertEqual(CreditAdditionalCost.objects.count(), 3)
        self.assertTrue(CreditAdditionalCost.objects.filter(
            user=self.user, name=payload["name"]).exists())

    def test_add_credit_additional_cost_successful_with_correct_user(self):
        """Test if creating credit additional cost successfully has correct user."""
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-additional-cost",
                    args=[str(self.credit.id)]),
            payload,
            follow=True)

        cost = CreditAdditionalCost.objects.get(name=payload["name"])
        self.assertEqual(cost.user, self.user)

    def test_add_credit_additional_cost_successful_with_correct_credit(self):
        """Test if creating credit additional cost successfully has correct
        credit as foreign key."""
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-additional-cost",
                    args=[str(self.credit.id)]),
            payload,
            follow=True)

        cost = CreditAdditionalCost.objects.get(name=payload["name"])
        self.assertEqual(cost.credit, self.credit)
        self.assertNotEqual(cost.credit, self.test_credit)

    @parameterized.expand(
        [
            ("Empty field: name", {"name": ""}, "To pole jest wymagane."),
            ("Empty field: cost_amount", {"cost_amount": ""},
             "To pole jest wymagane."),
            ("Empty field: cost_payment_date", {"cost_payment_date": ""},
             "To pole jest wymagane."),
            ("Incorrect cost_payment_date field (incorrect data)",
             {"cost_payment_date": "2020, 11, 11"}, "Wpisz poprawną datę."),

            ("Incorrect cost_amount field - max 82 decimal places",
             {"cost_amount": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect cost_amount field - max 9 digits",
             {"cost_amount": 11120000.98},
             "Upewnij się, że łącznie nie ma więcej niż 9 cyfr."),
        ]
    )
    def test_add_credit_additional_cost_unsuccessful_with_incorrect_data(
            self,
            name: str,
            new_payload: dict,
            field_message: str,
    ):
        """Test creating credit_additional_cost is not successful if data is
        incorrect."""
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)
        self.client.force_login(self.user)
        payload = self.payload
        for key, value in new_payload.items():
            payload[key] = value

        response_post = self.client.post(
            reverse("credit:add-credit-additional-cost",
                    args=[str(self.credit.id)]),
            payload)
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_credit_additional_cost_302_redirect_if_unauthorized(self):
        """Test if edit_credit_additional_cost page is unavailable for
        unauthorized users."""
        response = self.client.get(
            reverse("credit:edit-credit-additional-cost", args=[self.cost.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_credit_additional_cost_200_if_logged_in(self):
        """Test if edit_credit_additional_cost page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-additional-cost", args=[self.cost.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_credit_additional_cost_correct_template_if_logged_in(self):
        """Test if edit_credit_additional_cost page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-additional-cost", args=[self.cost.id]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_edit_credit_additional_cost_form_initial_values_set_context_data(self):
        """Test if edit_credit_additional_cost page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-additional-cost", args=[str(self.cost.id)]))
        self.assertEqual(response_get.context["page"], "edit-credit-additional-cost")
        self.assertEqual(response_get.context["credit_additional_cost"], self.cost)
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertIsInstance(response_get.context["form"], CreditAdditionalCostForm)

    def test_edit_credit_additional_cost_form_initial_values_set(self):
        """Test if edit_credit_additional_cost page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-additional-cost", args=[str(self.cost.id)]))
        self.assertIn(self.cost.notes, response_get.content.decode())
        self.assertIn(self.cost.name, response_get.content.decode())

    def test_edit_credit_additional_cost_success_and_redirect(self):
        """Test if updating credit_additional_cost is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        payload = self.payload
        self.assertNotEqual(self.cost.notes, payload["notes"])
        self.assertNotEqual(self.cost.name, payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("credit:edit-credit-additional-cost",
                    args=[str(self.cost.id)]),
            data=payload,
            instance=self.cost,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano dodatkowe koszty kredytu.", str(messages[0]))
        self.cost.refresh_from_db()
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)
        self.assertEqual(self.cost.name, payload["name"])
        self.assertEqual(self.cost.notes, payload["notes"])

    def test_edit_credit_additional_cost_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "New cost name",
            "cost_amount": 1100,
            "cost_payment_date": datetime.date(2021, 4, 4),
        }
        response_patch = self.client.patch(
            reverse("credit:edit-credit-additional-cost",
                    args=[str(self.cost.id)]),
            data=payload,
            instance=self.cost,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = self.payload
        response_put = self.client.put(
            reverse("credit:edit-credit-additional-cost",
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
            reverse("credit:edit-credit-additional-cost",
                    args=[str(self.cost.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_credit_additional_cost_logout_if_security_breach(self):
        """Editing credit_additional_cost of another user is unsuccessful and
        triggers logout."""
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_cost.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = self.payload

        # Attempt to change data that belongs to test_user by user
        response_post = self.client.post(
            reverse("credit:edit-credit-additional-cost",
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
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)
        self.assertNotIn(self.test_cost.name, payload["name"])

    def test_delete_credit_additional_cost_302_redirect_if_unauthorized(self):
        """Test if delete_credit_additional_cost page is unavailable for
        unauthorized users."""
        response = self.client.get(
            reverse("credit:delete-credit-additional-cost", args=[self.cost.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_credit_additional_cost_200_if_logged_in(self):
        """Test if delete_credit_additional_cost page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-additional-cost", args=[self.cost.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_credit_additional_cost_correct_template_if_logged_in(self):
        """Test if delete_credit_additional_cost page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-additional-cost", args=[self.cost.id]))
        self.assertTemplateUsed(response_get,
                                "credit/credit_delete_form.html")

    def test_delete_credit_additional_cost_initial_values_set_context_data(self):
        """Test if delete_credit_additional_cost page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:delete-credit-additional-cost",
                    args=[str(self.cost.id)]))
        self.assertIn(self.cost.name, response_get.content.decode())
        self.assertEqual(response_get.context["page"],
                         "delete-credit-additional-cost")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertEqual(response_get.context["credit_additional_cost"],
                         self.cost)

    def test_delete_credit_additional_cost_successful_and_redirect(self):
        """Deleting credit_additional_cost is successful (status code 200) and redirect
        is successful (status code 302)."""
        new_cost = CreditAdditionalCost.objects.create(
            user=self.user, credit=self.credit, name="Brand new cost",
            cost_amount=222, cost_payment_date=datetime.date(2021, 4, 4),
            notes="Some new payment")
        self.assertEqual(CreditAdditionalCost.objects.count(), 3)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertIn(str(self.cost), response.content.decode())
        self.assertIn(new_cost.name, response.content.decode())

        response_delete = self.client.post(
            reverse("credit:delete-credit-additional-cost", args=[str(new_cost.id)]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto koszt.", str(messages[0]))

        response = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)
        self.assertNotIn(new_cost.name, response.content.decode())
        self.assertIn(self.cost.name, response.content.decode())
        self.assertNotIn(self.test_cost.name, response.content.decode())

    def test_delete_credit_additional_cost_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("credit:delete-credit-additional-cost",
                    args=[str(self.cost.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("credit:delete-credit-additional-cost",
                    args=[str(self.cost.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:delete-credit-additional-cost",
                    args=[str(self.cost.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_credit_additional_cost_logout_if_security_breach(self):
        """Deleting credit_additional_cost of another user is unsuccessful
        and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_cost.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("credit:delete-credit-additional-cost",
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
        self.assertEqual(CreditAdditionalCost.objects.count(), 2)


class CreditEarlyRepaymentTests(TestCase):
    """Test CreditEarlyRepayment views."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)

        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.profile = Profile.objects.get(user=self.user)

        self.credit = CreditFactory(user=self.user)
        self.repayment = CreditEarlyRepaymentFactory(user=self.user,
                                                     credit=self.credit)

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com",
            password="testpass456")
        self.test_credit = CreditFactory(
            user=self.test_user, name="test credit", credit_number="ABCD1234")
        self.test_repayment = CreditEarlyRepaymentFactory(
            user=self.test_user, credit=self.test_credit, repayment_amount=11111)

        self.payload = {
            "repayment_amount": 22222,
            "repayment_date": datetime.date(2022, 2, 2),
            "repayment_action": "Zmniejszenie raty",
            "total_installment": "",
            "capital_installment": "",
        }

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def tearDown(self):
        if os.path.exists(settings.TEST_ROOT):
            shutil.rmtree(settings.TEST_ROOT)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)

    def test_add_credit_early_repayment_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add credit early repayment
        (user is redirected to login page)."""
        response = self.client.get(reverse("credit:add-credit-early-repayment",
                                           args=[str(self.credit.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_credit_early_repayment_result_200_if_logged_in(self):
        """Test if add_credit_early_repayment page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:add-credit-early-repayment",
                    args=[str(self.credit.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_credit_early_repayment_correct_template_if_logged_in(self):
        """Test if add_credit_early_repayment page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:add-credit-early-repayment",
                    args=[str(self.credit.id)]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_add_credit_early_repayment_form_initial_values_set_context_data(self):
        """Test if add_credit_early_repayment page displays correct context data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:add-credit-early-repayment",
                    args=[str(self.credit.id)]))
        self.assertEqual(response_get.context["page"],
                         "add-credit-early-repayment")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertIsInstance(response_get.context["form"],
                              CreditEarlyRepaymentForm)

    def test_add_credit_early_repayment_form_initial_values_set_form_data(self):
        """Test if add_credit_early_repayment page displays correct form data."""
        repayment_fields = ["repayment_amount", "repayment_date",
                            "repayment_action", "total_installment",
                            "capital_installment"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("credit:add-credit-early-repayment",
                                               args=[str(self.credit.id)]))
        for field in repayment_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_credit_early_repayment_success_and_redirect(self):
        """Test if creating credit_early_repayment is successful (status code
        200) and redirecting is successful (status code 302)."""
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)
        payload = self.payload
        self.client.force_login(self.user)

        response_post = self.client.post(reverse(
            "credit:add-credit-early-repayment", args=[str(self.credit.id)]),
            data=payload,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano nadpłatę kredytu.",
                      str(messages[0]))
        self.assertInHTML("Zmniejszenie raty",
                          response_post.content.decode())
        self.assertEqual(CreditEarlyRepayment.objects.count(), 3)
        self.assertTrue(CreditEarlyRepayment.objects.filter(
            user=self.user, repayment_action=payload["repayment_action"]).exists())

    def test_add_credit_early_repayment_successful_with_correct_user(self):
        """Test if creating credit_early_repayment successfully has correct user."""
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-early-repayment", args=[str(self.credit.id)]),
            payload,
            follow=True)

        repayment = CreditEarlyRepayment.objects.get(
            repayment_action=payload["repayment_action"])
        self.assertEqual(repayment.user, self.user)

    def test_add_credit_early_repayment_successful_with_correct_credit(self):
        """Test if creating credit_early_repayment successfully has correct
        credit as foreign key."""
        payload = self.payload
        self.client.force_login(self.user)

        self.client.post(
            reverse("credit:add-credit-early-repayment",
                    args=[str(self.credit.id)]),
            payload,
            follow=True)

        repayment = CreditEarlyRepayment.objects.get(
            repayment_action=payload["repayment_action"])
        self.assertEqual(repayment.credit, self.credit)
        self.assertNotEqual(repayment.credit, self.test_credit)

    @parameterized.expand(
        [
            ("Empty field: repayment_amount", {"repayment_amount": ""},
             "To pole jest wymagane."),
            ("Incorrect repayment_amount field (negative values are not allowed)",
             {"repayment_amount": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect repayment_amount field - max 8 digits with 2 decimal places",
             {"repayment_amount": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect repayment_amount field - max 8 digits with 2 decimal places",
             {"repayment_amount": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),

            ("Empty field: repayment_date", {"repayment_date": ""},
             "To pole jest wymagane."),
            ("Incorrect repayment_date field (incorrect data)",
             {"repayment_date": "2020, 11, 11"}, "Wpisz poprawną datę."),

            ("Empty field: repayment_action", {"repayment_action": ""},
             "To pole jest wymagane."),
            ("Incorrect repayment_action field - value outside the permissible choice",
             {"repayment_action": "ABCD"},
             "Wybierz poprawną wartość. ABCD nie jest żadną z dostępnych opcji."),

            ("Incorrect total_installment field (negative values are not allowed)",
             {"total_installment": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect total_installment field - max 2 decimal places",
             {"total_installment": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect total_installment field - max 8 digits",
             {"total_installment": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),

            ("Incorrect capital_installment field (negative values are not allowed)",
             {"capital_installment": -456}, "Wartość nie może być liczbą ujemną."),
            ("Incorrect capital_installment field - max 2 decimal places",
             {"capital_installment": 110.9876},
             "Upewnij się, że liczba ma nie więcej niż 2 cyfry po przecinku."),
            ("Incorrect capital_installment field - max 8 digits ",
             {"capital_installment": 1112000.98},
             "Upewnij się, że łącznie nie ma więcej niż 8 cyfr."),
        ]
    )
    def test_add_credit_early_repayment_unsuccessful_with_incorrect_data(
            self,
            name: str,
            new_payload: dict,
            field_message: str,
    ):
        """Test creating credit_early_repayment is not successful if data
        is incorrect."""
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)
        self.client.force_login(self.user)
        payload = self.payload
        for key, value in new_payload.items():
            payload[key] = value

        response_post = self.client.post(
            reverse("credit:add-credit-early-repayment",
                    args=[str(self.credit.id)]),
            payload)
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_credit_early_repayment_302_redirect_if_unauthorized(self):
        """Test if edit_credit_early_repayment page is unavailable for
        unauthorized users."""
        response = self.client.get(
            reverse("credit:edit-credit-early-repayment",
                    args=[self.repayment.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_credit_early_repayment_200_if_logged_in(self):
        """Test if edit_credit_early_repayment page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-early-repayment",
                    args=[self.repayment.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_credit_early_repayment_correct_template_if_logged_in(self):
        """Test if edit_credit_early_repayment page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:edit-credit-early-repayment",
                    args=[self.repayment.id]))
        self.assertTemplateUsed(response_get, "credit/credit_form.html")

    def test_edit_credit_early_repayment_form_initial_values_set_context_data(self):
        """Test if edit_credit_early_repayment page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-early-repayment",
                    args=[self.repayment.id]))
        self.assertEqual(response_get.context["page"],
                         "edit-credit-early-repayment")
        self.assertEqual(response_get.context["credit"], self.credit)
        self.assertEqual(response_get.context["credit_early_repayment"],
                         self.repayment)
        self.assertIsInstance(response_get.context["form"],
                              CreditEarlyRepaymentForm)

    def test_edit_credit_early_repayment_form_initial_values_set(self):
        """Test if edit_credit_early_repayment page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:edit-credit-early-repayment",
                    args=[self.repayment.id]))
        self.assertIn(self.repayment.repayment_action,
                      response_get.content.decode())

    def test_edit_credit_early_repayment_success_and_redirect(self):
        """Test if updating credit_early_repayment is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        payload = self.payload
        self.assertNotEqual(self.repayment.repayment_action,
                            payload["repayment_action"])
        self.assertNotEqual(self.repayment.repayment_amount,
                            payload["repayment_amount"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("credit:edit-credit-early-repayment", args=[self.repayment.id]),
            data=payload,
            instance=self.repayment,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Zaktualizowano dodatkowe koszty kredytu.",
                      str(messages[0]))
        self.repayment.refresh_from_db()
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)
        self.assertEqual(self.repayment.repayment_action,
                         payload["repayment_action"])
        self.assertEqual(self.repayment.repayment_amount,
                         payload["repayment_amount"])

    def test_edit_credit_early_repayment_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "repayment_amount": 22222,
            "repayment_date": datetime.date(2022, 2, 2),
            "repayment_action": "Zmniejszenie raty"
        }
        response_patch = self.client.patch(
            reverse("credit:edit-credit-early-repayment",
                    args=[str(self.repayment.id)]),
            data=payload,
            instance=self.repayment,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = self.payload
        response_put = self.client.put(
            reverse("credit:edit-credit-early-repayment",
                    args=[str(self.repayment.id)]),
            data=payload,
            instance=self.repayment,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:edit-credit-early-repayment",
                    args=[str(self.repayment.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_credit_early_repayment_logout_if_security_breach(self):
        """Editing credit_early_repayment of another user is unsuccessful
        and triggers logout."""
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_repayment.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = self.payload

        # Attempt to change data that belongs to test_user by user
        response_post = self.client.post(
            reverse("credit:edit-credit-early-repayment",
                    args=[str(self.test_repayment.id)]),
            data=payload,
            content_type="text/html",
            instance=self.test_repayment,
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
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)
        self.assertNotIn(self.test_repayment.repayment_action,
                         payload["repayment_action"])

    def test_delete_credit_early_repayment_302_redirect_if_unauthorized(self):
        """Test if delete_credit_early_repayment page is unavailable for
        unauthorized users."""
        response = self.client.get(
            reverse("credit:delete-credit-early-repayment",
                    args=[self.repayment.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_credit_early_repayment_200_if_logged_in(self):
        """Test if delete_credit_early_repayment page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-early-repayment",
                    args=[self.repayment.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_credit_early_repayment_correct_template_if_logged_in(self):
        """Test if delete_credit_early_repayment page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("credit:delete-credit-early-repayment",
                    args=[self.repayment.id]))
        self.assertTemplateUsed(response_get,
                                "credit/credit_delete_form.html")

    def test_delete_credit_early_repayment_initial_values_set_context_data(self):
        """Test if delete_credit_early_repayment page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("credit:delete-credit-early-repayment",
                    args=[str(self.repayment.id)]))
        self.assertEqual(response_get.context["page"],
                         "delete-credit-early-repayment")
        self.assertEqual(response_get.context["credit_early_repayment"],
                         self.repayment)
        self.assertEqual(response_get.context["credit"], self.credit)

    def test_delete_credit_early_repayment_successful_and_redirect(self):
        """Deleting credit_early_repayment is successful (status code 200)
        and redirect is successful (status code 302)."""
        new_repayment = CreditEarlyRepayment.objects.create(
            user=self.user, credit=self.credit, repayment_amount=2222,
            repayment_date=datetime.date(2022, 2, 2),
            repayment_action="Zmniejszenie raty"
        )
        self.assertNotEqual(new_repayment.repayment_action,
                            self.repayment.repayment_action)
        self.assertEqual(CreditEarlyRepayment.objects.count(), 3)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertIn(self.repayment.repayment_action, response.content.decode())
        self.assertIn(new_repayment.repayment_action, response.content.decode())

        response_delete = self.client.post(
            reverse("credit:delete-credit-early-repayment",
                    args=[str(new_repayment.id)]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("credit:single-credit", args=[str(self.credit.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto nadpłatę.", str(messages[0]))

        response = self.client.get(
            reverse("credit:single-credit", args=[str(self.credit.id)]))
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)
        self.assertNotIn(new_repayment.repayment_action, response.content.decode())
        self.assertIn(self.repayment.repayment_action, response.content.decode())
        self.assertNotIn("11 111,00", response.content.decode())

    def test_delete_credit_early_repayment_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("credit:delete-credit-early-repayment",
                    args=[str(self.repayment.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("credit:delete-credit-early-repayment",
                    args=[str(self.repayment.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("credit:delete-credit-early-repayment",
                    args=[str(self.repayment.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_credit_early_repayment_logout_if_security_breach(self):
        """Deleting credit_early_repayment of another user is unsuccessful
        and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_repayment.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("credit:delete-credit-early-repayment",
                    args=[str(self.test_repayment.id)]),
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
        self.assertEqual(CreditEarlyRepayment.objects.count(), 2)
