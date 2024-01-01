import logging

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from access.enums import Access
from connection.models import Attachment, Counterparty
from connection.factories import AttachmentFactory, CounterpartyFactory
from payment.models import Payment
from payment.factories import PaymentFactory
from credit.models import Credit, CreditInsurance, CreditInterestRate
from credit.factories import (CreditFactory, CreditInterestRateFactory,
                              CreditInsuranceFactory)
from trip.models import Trip, TripBasicChecklist, TripAdvancedChecklist
from trip.factories import TripFactory, TripBasicFactory, TripAdvancedFactory
from renovation.models import Renovation, RenovationCost
from renovation.factories import RenovationFactory, RenovationCostFactory
from planner.models import ExpenseList, ExpenseItem, ToDoList, ToDoItem
from planner.factories import (ExpenseListFactory, ExpenseItemFactory,
                               ToDoListFactory, ToDoItemFactory)
from medical.models import MedCard, Medicine, MedicalVisit, HealthTestResult
from medical.factories import (MedCardFactory, MedicineFactory,
                               MedicalVisitFactory, HealthTestResultFactory)
from user.models import Profile


logger = logging.getLogger("test")
User = get_user_model()


# NOTE: (for test purposes)
# self.user has given access to self.test_user (at test@example.com)
# In case of testing access given by self.user, we must log in self.test_user
# And the other way round - self.test_user gave access to user@example.com
# self.user can see data shared by self.test_user
# But no one has given access to self.abc_user, therefore, attempt to see
# data of self.user or self.test_user by self.abc_user is a security breach
# which results in self.abc_user logout.


class BasicUrlsTests(TestCase):
    """Test basic access urls."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="user@example.com", password="testpass456")
        self.profile = Profile.objects.get(user=self.user)
        self.profile.access_granted_to = "test@example.com"
        self.profile.save()
        self.counterparty_yes = CounterpartyFactory(
            user=self.user, access_granted=Access.ACCESS_GRANTED)
        self.credit_yes = CreditFactory(
            user=self.user, access_granted=Access.ACCESS_GRANTED,
            access_granted_for_schedule=Access.ACCESS_GRANTED)
        self.credit_interest_rate = CreditInterestRateFactory(
            user=self.user, credit=self.credit_yes)
        self.credit_insurance = CreditInsuranceFactory(
            user=self.user, credit=self.credit_yes)
        self.medcard_yes = MedCardFactory(
            user=self.user,
            access_granted=Access.ACCESS_GRANTED,
            access_granted_medicines=Access.ACCESS_GRANTED,
            access_granted_test_results=Access.NO_ACCESS_GRANTED,
            access_granted_visits=Access.NO_ACCESS_GRANTED,
        )
        self.medicine_yes = MedicineFactory(user=self.user)
        self.visit_no = MedicalVisitFactory(user=self.user)
        self.test_result_no = HealthTestResultFactory(user=self.user)
        self.payment_no = PaymentFactory(
            user=self.user, access_granted=Access.NO_ACCESS_GRANTED)

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com",
            password="testpass456")
        self.test_profile = Profile.objects.get(user=self.test_user)
        self.test_profile.access_granted_to = "user@example.com"
        self.test_profile.save()
        self.test_counterparty_yes = CounterpartyFactory(
            user=self.test_user, access_granted=Access.ACCESS_GRANTED)
        self.test_renovation_no = RenovationFactory(
            user=self.test_user, access_granted=Access.NO_ACCESS_GRANTED)
        self.test_trip_yes = TripFactory(
            user=self.test_user, access_granted=Access.ACCESS_GRANTED)
        self.test_medcard_yes = MedCardFactory(
            user=self.test_user,
            access_granted=Access.ACCESS_GRANTED,
            access_granted_medicines=Access.NO_ACCESS_GRANTED,
            access_granted_test_results=Access.NO_ACCESS_GRANTED,
            access_granted_visits=Access.NO_ACCESS_GRANTED,
        )

        self.abc_user = User.objects.create_user(
            username="fakeuser", email="abc@example.com",
            password="testpass456")
        self.abc_profile = Profile.objects.get(user=self.abc_user)
        self.abc_profile.access_granted_to = "test@example.com"
        self.abc_profile.save()
        self.abc_counterparty_yes = CounterpartyFactory(
            user=self.abc_user, access_granted=Access.ACCESS_GRANTED)
        self.abc_medcard_no = MedCardFactory(
            user=self.abc_user,
            access_granted=Access.NO_ACCESS_GRANTED,
            access_granted_medicines=Access.ACCESS_GRANTED,
            access_granted_test_results=Access.ACCESS_GRANTED,
            access_granted_visits=Access.ACCESS_GRANTED,
        )

        self.pages = [
            {"page": "access:access",
             "kwargs": {}, "name": "access",
             "template": "access/access.html"},
            {"page": "access:data-access",
             "kwargs": {"slug": self.test_user.profile.slug, "page": 1},
             "name": "data_access",
             "template": "access/data_access.html"},
            {"page": "access:data-access-payments",
             "kwargs": {"slug": self.test_user.profile.slug, "page": 1},
             "name": "data_access_payments",
             "template": "access/data_access.html"},
            {"page": "access:data-access-planner",
             "kwargs": {"slug": self.test_user.profile.slug, "page": 1},
             "name": "data_access_planner",
             "template": "access/data_access.html"},
            {"page": "access:data-access-medical",
             "kwargs": {"slug": self.test_user.profile.slug, "page": 1},
             "name": "data_access_medical",
             "template": "access/data_access.html"},
        ]

    def test_view_url_accessible_by_name_for_unauthenticated_user(self):
        """Test if view url is accessible by its name
        and returns redirect (302) for unauthenticated user."""
        for page in self.pages:
            response_page = self.client.get(
                reverse(page["page"], kwargs=page["kwargs"]))
            self.assertEqual(response_page.status_code, 302)
            self.assertIn("login", response_page.url)

    def test_view_url_accessible_by_name_for_authenticated_user(self):
        """Test if view url is accessible by its name
         and returns desired page (200) for authenticated user."""
        self.client.force_login(self.user)
        for page in self.pages:
            response = self.client.get(
                reverse(page["page"], kwargs=page["kwargs"]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(str(response.context["user"]), "johndoe123")

    def test_view_uses_correct_template(self):
        """Test if response returns correct page template."""
        self.client.force_login(self.user)
        for page in self.pages:
            response = self.client.get(
                reverse(page["page"], kwargs=page["kwargs"]))
            self.assertTemplateUsed(response, page["template"])


class AccessTests(TestCase):
    """Test all access views."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")
        self.profile = Profile.objects.get(user=self.user)
        self.profile.access_granted_to = "test@example.com"
        self.profile.save()
        self.counterparty_yes = CounterpartyFactory(
            user=self.user, access_granted=Access.ACCESS_GRANTED)
        self.credit_yes = CreditFactory(
            user=self.user, access_granted=Access.ACCESS_GRANTED,
            access_granted_for_schedule=Access.ACCESS_GRANTED)
        self.credit_interest_rate = CreditInterestRateFactory(
            user=self.user, credit=self.credit_yes)
        self.credit_insurance = CreditInsuranceFactory(
            user=self.user, credit=self.credit_yes)
        self.medcard_yes = MedCardFactory(
            user=self.user,
            access_granted=Access.ACCESS_GRANTED,
            access_granted_medicines=Access.ACCESS_GRANTED,
            access_granted_test_results=Access.NO_ACCESS_GRANTED,
            access_granted_visits=Access.NO_ACCESS_GRANTED,
        )
        self.medicine_yes = MedicineFactory(user=self.user)
        self.visit_no = MedicalVisitFactory(user=self.user)
        self.test_result_no = HealthTestResultFactory(user=self.user)
        self.payment_no = PaymentFactory(
            user=self.user, access_granted=Access.NO_ACCESS_GRANTED)
        self.expense_list_yes = ExpenseListFactory(
            user=self.user, access_granted=Access.ACCESS_GRANTED)
        self.expense_1 = ExpenseItemFactory(
            user=self.user, expense_list=self.expense_list_yes)
        self.expense_2 = ExpenseItemFactory(
            user=self.user, expense_list=self.expense_list_yes,
            name="Expense item 2")
        self.todo_list_no = ToDoListFactory(
            user=self.user, access_granted=Access.NO_ACCESS_GRANTED)
        self.todo_1 = ToDoItemFactory(
            user=self.user, todo_list=self.todo_list_no)
        self.todo_2_ = ToDoItemFactory(
            user=self.user,  todo_list=self.todo_list_no, name="ToDo item 2")
        self.renovation_yes = RenovationFactory(
            user=self.user, access_granted=Access.ACCESS_GRANTED)
        self.renovation_cost = RenovationCostFactory(
            user=self.user, renovation=self.renovation_yes)
        self.trip_no = TripFactory(
            user=self.user, access_granted=Access.NO_ACCESS_GRANTED)
        self.trip_luggage = TripBasicFactory(user=self.user, trip=self.trip_no)

        self.abc_user = User.objects.create_user(
            username="abc_user", email="abc@example.com",
            password="testpass456")
        self.abc_profile = Profile.objects.get(user=self.abc_user)
        self.abc_profile.access_granted_to = "test@example.com"
        self.abc_profile.save()
        self.abc_counterparty_yes = CounterpartyFactory(
            user=self.abc_user, access_granted=Access.ACCESS_GRANTED)
        self.abc_credit_yes = CreditFactory(
            user=self.abc_user, access_granted=Access.ACCESS_GRANTED,
            access_granted_for_schedule=Access.ACCESS_GRANTED)
        self.abc_credit_interest_rate = CreditInterestRateFactory(
            user=self.abc_user, credit=self.abc_credit_yes)
        self.abc_credit_insurance = CreditInsuranceFactory(
            user=self.abc_user, credit=self.abc_credit_yes)
        self.abc_medcard_no = MedCardFactory(
            user=self.abc_user,
            access_granted=Access.NO_ACCESS_GRANTED,
            access_granted_medicines=Access.ACCESS_GRANTED,
            access_granted_test_results=Access.ACCESS_GRANTED,
            access_granted_visits=Access.ACCESS_GRANTED,
        )
        self.abc_medicine_yes = MedicineFactory(user=self.abc_user)
        self.abc_visit_yes = MedicalVisitFactory(user=self.abc_user)
        self.abc_test_result_yes = HealthTestResultFactory(user=self.abc_user)
        self.abc_payment_no = PaymentFactory(
            user=self.abc_user, access_granted=Access.NO_ACCESS_GRANTED)
        self.abc_expense_list_yes = ExpenseListFactory(
            user=self.abc_user, access_granted=Access.ACCESS_GRANTED)
        self.abc_expense_1 = ExpenseItemFactory(
            user=self.abc_user, expense_list=self.abc_expense_list_yes)
        self.abc_expense_2 = ExpenseItemFactory(
            user=self.abc_user, expense_list=self.abc_expense_list_yes,
            name="ABC Expense item 2")
        self.abc_todo_list_no = ToDoListFactory(
            user=self.abc_user, access_granted=Access.NO_ACCESS_GRANTED)
        self.abc_todo_1 = ToDoItemFactory(
            user=self.abc_user, todo_list=self.abc_todo_list_no)
        self.abc_todo_2 = ToDoItemFactory(
            user=self.abc_user, todo_list=self.abc_todo_list_no,
            name="ABC item 2")
        self.abc_renovation_no = RenovationFactory(
            user=self.abc_user, access_granted=Access.NO_ACCESS_GRANTED)
        self.abc_renovation_cost = RenovationCostFactory(
            user=self.abc_user, renovation=self.abc_renovation_no)
        self.abc_trip_yes = TripFactory(
            user=self.abc_user, access_granted=Access.ACCESS_GRANTED)
        self.abc_trip_luggage = TripBasicFactory(
            user=self.user, trip=self.abc_trip_yes)
        self.abc_trip_luggage_advanced = TripAdvancedFactory(
            user=self.user, trip=self.abc_trip_yes)

        self.test_user = User.objects.create_user(
            username="testuser123", email="test@example.com",
            password="testpass456")
        self.test_profile = Profile.objects.get(user=self.test_user)
        self.test_profile.access_granted_to = "jd@example.com"
        self.test_profile.save()
        self.test_counterparty_yes = CounterpartyFactory(
            user=self.test_user, access_granted=Access.ACCESS_GRANTED)
        self.test_renovation_no = RenovationFactory(
            user=self.test_user, access_granted=Access.NO_ACCESS_GRANTED)
        self.test_trip_yes = TripFactory(
            user=self.test_user, access_granted=Access.ACCESS_GRANTED)
        self.test_medcard_yes = MedCardFactory(
            user=self.test_user,
            access_granted=Access.ACCESS_GRANTED,
            access_granted_medicines=Access.NO_ACCESS_GRANTED,
            access_granted_test_results=Access.NO_ACCESS_GRANTED,
            access_granted_visits=Access.NO_ACCESS_GRANTED,
        )
        self.test_medicine_no = MedicineFactory(user=self.test_user)
        self.abc_visit_no = MedicalVisitFactory(user=self.test_user)

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Profile.objects.count(), 3)
        self.assertEqual(Counterparty.objects.count(), 3)
        self.assertEqual(Credit.objects.count(), 2)
        self.assertEqual(CreditInsurance.objects.count(), 2)
        self.assertEqual(CreditInterestRate.objects.count(), 2)
        self.assertEqual(MedCard.objects.count(), 3)
        self.assertEqual(Medicine.objects.count(), 3)
        self.assertEqual(HealthTestResult.objects.count(), 2)
        self.assertEqual(MedicalVisit.objects.count(), 3)
        self.assertEqual(Payment.objects.count(), 2)
        self.assertEqual(ExpenseList.objects.count(), 2)
        self.assertEqual(ExpenseItem.objects.count(), 4)
        self.assertEqual(ToDoList.objects.count(), 2)
        self.assertEqual(ToDoItem.objects.count(), 4)
        self.assertEqual(Renovation.objects.count(), 3)
        self.assertEqual(RenovationCost.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 3)
        self.assertEqual(TripBasicChecklist.objects.count(), 2)
        self.assertEqual(TripAdvancedChecklist.objects.count(), 1)

    def test_access_page_302_redirect_if_unauthorized(self):
        """Test if access page is unavailable for unauthorized users."""
        response = self.client.get(reverse("access:access"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_access_page_200_if_logged_in(self):
        """Test if access page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("access:access"))
        self.assertEqual(response_get.status_code, 200)

    def test_access_page_correct_template_if_logged_in(self):
        """Test if access page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("access:access"))
        self.assertTemplateUsed(response_get, "access/access.html")

    def test_access_page_initial_values_set_context_data(self):
        """Test if access page displays correct context data."""
        access_granted = Profile.objects.filter(
            access_granted_to=self.test_user.email).order_by("email")
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("access:access"))
        self.assertIn(str(self.user.email), response_get.content.decode())
        self.assertIn(str(self.abc_user.email), response_get.content.decode())
        self.assertQuerysetEqual(response_get.context["access_granted"],
                                 access_granted)

    def test_access_page_initial_values_set_no_access_to_any_data(self):
        """Test if access page displays correct context data."""
        access_granted = Profile.objects.filter(
            access_granted_to=self.abc_user.email).order_by("email")
        self.assertFalse(access_granted.exists())

        self.client.force_login(self.abc_user)
        response_get = self.client.get(reverse("access:access"))
        self.assertIn("Brak udostępnionych danych od użytkowników.",
                      response_get.content.decode())

    def test_data_access_page_302_redirect_if_unauthorized(self):
        """Test if data_access page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("access:data-access",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_data_access_page_200_if_logged_in(self):
        """Test if data_access page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("access:data-access",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertEqual(response_get.status_code, 200)

    def test_data_access_page_correct_template_if_logged_in(self):
        """Test if data_access page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("access:data-access",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertTemplateUsed(response_get, "access/data_access.html")

    def test_data_access_page_initial_values_set_context_data(self):
        """Test if data_access page displays correct context data."""

        # For self.user accessing data of self.test_user
        slug = self.test_user.profile.slug
        credits = Credit.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        credit_schedules = Credit.objects.filter(user=self.test_user).filter(
            access_granted_for_schedule=_("Udostępnij dane")).order_by(
            "-updated")
        payments = Payment.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        counterparties = Counterparty.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        attachments = Attachment.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        trips = Trip.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        renovations = Renovation.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        expense_lists = ExpenseList.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        todo_lists = ToDoList.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        try:
            medcard = MedCard.objects.get(user=self.test_user)
        except MedCard.DoesNotExist:
            medcard = None

        if medcard:
            if medcard.access_granted == _("Udostępnij dane"):
                medcard = MedCard.objects.get(user=self.test_user)
            else:
                medcard = None
            if medcard.access_granted_medicines == _("Udostępnij dane"):
                medicines = Medicine.objects.filter(user=self.test_user)
            else:
                medicines = None
            if medcard.access_granted_visits == _("Udostępnij dane"):
                med_visits = MedicalVisit.objects.filter(user=self.test_user)
            else:
                med_visits = None
            if medcard.access_granted_test_results == _("Udostępnij dane"):
                med_results = HealthTestResult.objects.filter(user=self.test_user)
            else:
                med_results = None
        else:
            medicines = None
            med_visits = None
            med_results = None

        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("access:data-access",
                    kwargs={"slug": slug, "page": 1}))
        self.assertEqual(response_get.context["page_name"], "all-shared-data")
        self.assertEqual(response_get.context["slug"], slug)
        self.assertQuerysetEqual(response_get.context["page_object_credits"],
                                 credits)
        self.assertQuerysetEqual(response_get.context["credit_schedules"],
                                 credit_schedules)
        self.assertQuerysetEqual(response_get.context["page_object_payments"],
                                 payments)
        self.assertQuerysetEqual(response_get.context["page_object_counterparties"],
                                 counterparties)
        self.assertQuerysetEqual(response_get.context["page_object_attachments"],
                                 attachments)
        self.assertQuerysetEqual(response_get.context["page_object_trips"],
                                 trips)
        self.assertQuerysetEqual(response_get.context["page_object_renovations"],
                                 renovations)
        self.assertQuerysetEqual(response_get.context["page_object_expense_lists"],
                                 expense_lists)
        self.assertQuerysetEqual(response_get.context["page_object_todo_lists"],
                                 todo_lists)
        self.assertEqual(response_get.context["medcard"], medcard)
        self.assertEqual(response_get.context["page_object_medicines"],
                         medicines)
        self.assertEqual(response_get.context["page_object_med_visits"],
                         med_visits)
        self.assertEqual(response_get.context["page_object_med_results"],
                         med_results)

        # For self.test_user accessing data of self.user
        slug = self.user.profile.slug
        credits = Credit.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        credit_schedules = Credit.objects.filter(user=self.user).filter(
            access_granted_for_schedule=_("Udostępnij dane")).order_by(
            "-updated")
        payments = Payment.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        counterparties = Counterparty.objects.filter(
            user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        attachments = Attachment.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        trips = Trip.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        renovations = Renovation.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        expense_lists = ExpenseList.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        todo_lists = ToDoList.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        try:
            medcard = MedCard.objects.get(user=self.user)
        except MedCard.DoesNotExist:
            medcard = None

        if medcard:
            if medcard.access_granted == _("Udostępnij dane"):
                medcard = MedCard.objects.get(user=self.user)
            else:
                medcard = None
            if medcard.access_granted_medicines == _("Udostępnij dane"):
                medicines = Medicine.objects.filter(user=self.user)
            else:
                medicines = None
            if medcard.access_granted_visits == _("Udostępnij dane"):
                med_visits = MedicalVisit.objects.filter(user=self.user)
            else:
                med_visits = None
            if medcard.access_granted_test_results == _("Udostępnij dane"):
                med_results = HealthTestResult.objects.filter(
                    user=self.user)
            else:
                med_results = None
        else:
            medicines = None
            med_visits = None
            med_results = None

        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("access:data-access",
                    kwargs={"slug": slug, "page": 1}))
        self.assertEqual(response_get.context["page_name"], "all-shared-data")
        self.assertEqual(response_get.context["slug"], slug)
        self.assertQuerysetEqual(response_get.context["page_object_credits"],
                                 credits)
        self.assertQuerysetEqual(response_get.context["credit_schedules"],
                                 credit_schedules)
        self.assertQuerysetEqual(response_get.context["page_object_payments"],
                                 payments)
        self.assertQuerysetEqual(
            response_get.context["page_object_counterparties"], counterparties)
        self.assertQuerysetEqual(
            response_get.context["page_object_attachments"], attachments)
        self.assertQuerysetEqual(response_get.context["page_object_trips"],
                                 trips)
        self.assertQuerysetEqual(
            response_get.context["page_object_renovations"], renovations)
        self.assertQuerysetEqual(
            response_get.context["page_object_expense_lists"], expense_lists)
        self.assertQuerysetEqual(
            response_get.context["page_object_todo_lists"], todo_lists)
        self.assertEqual(response_get.context["medcard"], medcard)
        self.assertQuerysetEqual(response_get.context["page_object_medicines"],
                                 medicines)
        self.assertEqual(response_get.context["page_object_med_visits"],
                         med_visits)
        self.assertEqual(response_get.context["page_object_med_results"],
                         med_results)

    def test_data_access_page_logout_is_security_breach(self):
        """Accessing data of another user without access granted by this user
        is unsuccessful and user is logout."""

        # Test for user "abc_user" (user without access) attempt to see test_user data
        access_granted = Profile.objects.filter(
            access_granted_to=self.abc_user.email)
        self.assertFalse(access_granted.exists())
        self.client.force_login(self.test_user)
        test_user_profile_slug = self.test_profile.slug
        self.client.login(username="abc_user", password="testpass456")
        self.assertIn("_auth_user_id", self.client.session)
        response_get = self.client.get(reverse("access:data-access",
                                       kwargs={"slug": test_user_profile_slug,
                                               "page": 1}), follow=True)

        self.assertRedirects(
            response_get,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_get.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do tych danych.", str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_access_to_payments_page_302_redirect_if_unauthorized(self):
        """Test if access_to_payments page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("access:data-access-payments",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_access_to_payments_page_200_if_logged_in(self):
        """Test if access_to_payments page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("access:data-access-payments",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertEqual(response_get.status_code, 200)

    def test_access_to_payments_page_correct_template_if_logged_in(self):
        """Test if access_to_payments page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("access:data-access-payments",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertTemplateUsed(response_get, "access/data_access.html")

    def test_access_to_payments_page_initial_values_set_context_data(self):
        """Test if access_to_payments page displays correct context data."""

        # For self.user accessing data of self.test_user
        slug = self.test_user.profile.slug
        credits = Credit.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        payments = Payment.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        counterparties = Counterparty.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        attachments = Attachment.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")

        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("access:data-access-payments",
                    kwargs={"slug": slug, "page": 1}))
        self.assertEqual(response_get.context["page_name"], "access-to-payments")
        self.assertEqual(response_get.context["slug"], slug)
        self.assertQuerysetEqual(response_get.context["page_object_credits"],
                                 credits)
        self.assertQuerysetEqual(response_get.context["page_object_payments"],
                                 payments)
        self.assertQuerysetEqual(response_get.context["page_object_counterparties"],
                                 counterparties)
        self.assertQuerysetEqual(response_get.context["page_object_attachments"],
                                 attachments)

        # For self.test_user accessing data of self.user
        slug = self.user.profile.slug
        credits = Credit.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        payments = Payment.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        counterparties = Counterparty.objects.filter(
            user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        attachments = Attachment.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")

        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("access:data-access-payments",
                    kwargs={"slug": slug, "page": 1}))
        self.assertEqual(response_get.context["page_name"], "access-to-payments")
        self.assertEqual(response_get.context["slug"], slug)
        self.assertQuerysetEqual(response_get.context["page_object_credits"],
                                 credits)
        self.assertQuerysetEqual(response_get.context["page_object_payments"],
                                 payments)
        self.assertQuerysetEqual(
            response_get.context["page_object_counterparties"], counterparties)
        self.assertQuerysetEqual(
            response_get.context["page_object_attachments"], attachments)

    def test_access_to_payments_page_logout_is_security_breach(self):
        """Accessing data of another user without access granted by this user
        is unsuccessful and user is logout."""

        # Test for user "abc_user" (user without access) attempt to see test_user data
        access_granted = Profile.objects.filter(
            access_granted_to=self.abc_user.email)
        self.assertFalse(access_granted.exists())
        self.client.force_login(self.test_user)
        test_user_profile_slug = self.test_profile.slug
        self.client.login(username="abc_user", password="testpass456")
        self.assertIn("_auth_user_id", self.client.session)
        response_get = self.client.get(reverse("access:data-access-payments",
                                       kwargs={"slug": test_user_profile_slug,
                                               "page": 1}), follow=True)

        self.assertRedirects(
            response_get,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_get.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do tych danych.", str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_access_to_planner_page_302_redirect_if_unauthorized(self):
        """Test if data_access page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("access:data-access-planner",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_access_to_planner_page_200_if_logged_in(self):
        """Test if access_to_planner page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("access:data-access-planner",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertEqual(response_get.status_code, 200)

    def test_access_to_planner_page_correct_template_if_logged_in(self):
        """Test if access_to_planner page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("access:data-access-planner",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertTemplateUsed(response_get, "access/data_access.html")

    def test_access_to_planner_page_initial_values_set_context_data(self):
        """Test if access_to_planner page displays correct context data."""

        # For self.user accessing data of self.test_user
        slug = self.test_user.profile.slug
        trips = Trip.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        renovations = Renovation.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        expense_lists = ExpenseList.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        todo_lists = ToDoList.objects.filter(user=self.test_user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")

        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("access:data-access-planner",
                    kwargs={"slug": slug, "page": 1}))
        self.assertEqual(response_get.context["page_name"], "access-to-planner")
        self.assertEqual(response_get.context["slug"], slug)
        self.assertQuerysetEqual(response_get.context["page_object_trips"],
                                 trips)
        self.assertQuerysetEqual(response_get.context["page_object_renovations"],
                                 renovations)
        self.assertQuerysetEqual(response_get.context["page_object_expense_lists"],
                                 expense_lists)
        self.assertQuerysetEqual(response_get.context["page_object_todo_lists"],
                                 todo_lists)

        # For self.test_user accessing data of self.user
        slug = self.user.profile.slug

        trips = Trip.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        renovations = Renovation.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        expense_lists = ExpenseList.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")
        todo_lists = ToDoList.objects.filter(user=self.user).filter(
            access_granted=_("Udostępnij dane")).order_by("-updated")

        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("access:data-access-planner",
                    kwargs={"slug": slug, "page": 1}))
        self.assertEqual(response_get.context["page_name"], "access-to-planner")
        self.assertEqual(response_get.context["slug"], slug)
        self.assertQuerysetEqual(response_get.context["page_object_trips"],
                                 trips)
        self.assertQuerysetEqual(
            response_get.context["page_object_renovations"], renovations)
        self.assertQuerysetEqual(
            response_get.context["page_object_expense_lists"], expense_lists)
        self.assertQuerysetEqual(
            response_get.context["page_object_todo_lists"], todo_lists)

    def test_access_to_planner_page_logout_is_security_breach(self):
        """Accessing data of another user without access granted by this user
        is unsuccessful and user is logout."""

        # Test for user "abc_user" (user without access) attempt to see test_user data
        access_granted = Profile.objects.filter(
            access_granted_to=self.abc_user.email)
        self.assertFalse(access_granted.exists())
        self.client.force_login(self.test_user)
        test_user_profile_slug = self.test_profile.slug
        self.client.login(username="abc_user", password="testpass456")
        self.assertIn("_auth_user_id", self.client.session)
        response_get = self.client.get(reverse("access:data-access-planner",
                                       kwargs={"slug": test_user_profile_slug,
                                               "page": 1}), follow=True)

        self.assertRedirects(
            response_get,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_get.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do tych danych.", str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_access_to_medical_page_302_redirect_if_unauthorized(self):
        """Test if access_to_medical page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("access:data-access-medical",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_access_to_medical_page_200_if_logged_in(self):
        """Test if access_to_medical page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("access:data-access-medical",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertEqual(response_get.status_code, 200)

    def test_access_to_medical_page_correct_template_if_logged_in(self):
        """Test if access_to_medical page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("access:data-access-medical",
                    kwargs={"slug": self.test_user.profile.slug, "page": 1}))
        self.assertTemplateUsed(response_get, "access/data_access.html")

    def test_access_to_medical_page_initial_values_set_context_data(self):
        """Test if access_to_medical page displays correct context data."""

        # For self.user accessing data of self.test_user
        slug = self.test_user.profile.slug
        try:
            medcard = MedCard.objects.get(user=self.test_user)
        except MedCard.DoesNotExist:
            medcard = None

        if medcard:
            if medcard.access_granted == _("Udostępnij dane"):
                medcard = MedCard.objects.get(user=self.test_user)
            else:
                medcard = None
            if medcard.access_granted_medicines == _("Udostępnij dane"):
                medicines = Medicine.objects.filter(user=self.test_user)
            else:
                medicines = None
            if medcard.access_granted_visits == _("Udostępnij dane"):
                med_visits = MedicalVisit.objects.filter(user=self.test_user)
            else:
                med_visits = None
            if medcard.access_granted_test_results == _("Udostępnij dane"):
                med_results = HealthTestResult.objects.filter(user=self.test_user)
            else:
                med_results = None
        else:
            medicines = None
            med_visits = None
            med_results = None

        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("access:data-access-medical",
                    kwargs={"slug": slug, "page": 1}))
        self.assertEqual(response_get.context["page_name"], "access-to-medical")
        self.assertEqual(response_get.context["slug"], slug)
        self.assertEqual(response_get.context["medcard"], medcard)
        self.assertEqual(response_get.context["page_object_medicines"],
                         medicines)
        self.assertEqual(response_get.context["page_object_med_visits"],
                         med_visits)
        self.assertEqual(response_get.context["page_object_med_results"],
                         med_results)

        # For self.test_user accessing data of self.user
        slug = self.user.profile.slug
        try:
            medcard = MedCard.objects.get(user=self.user)
        except MedCard.DoesNotExist:
            medcard = None

        if medcard:
            if medcard.access_granted == _("Udostępnij dane"):
                medcard = MedCard.objects.get(user=self.user)
            else:
                medcard = None
            if medcard.access_granted_medicines == _("Udostępnij dane"):
                medicines = Medicine.objects.filter(user=self.user)
            else:
                medicines = None
            if medcard.access_granted_visits == _("Udostępnij dane"):
                med_visits = MedicalVisit.objects.filter(user=self.user)
            else:
                med_visits = None
            if medcard.access_granted_test_results == _("Udostępnij dane"):
                med_results = HealthTestResult.objects.filter(
                    user=self.user)
            else:
                med_results = None
        else:
            medicines = None
            med_visits = None
            med_results = None

        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("access:data-access-medical",
                    kwargs={"slug": slug, "page": 1}))
        self.assertEqual(response_get.context["page_name"], "access-to-medical")
        self.assertEqual(response_get.context["slug"], slug)
        self.assertEqual(response_get.context["medcard"], medcard)
        self.assertQuerysetEqual(response_get.context["page_object_medicines"],
                                 medicines)
        self.assertEqual(response_get.context["page_object_med_visits"],
                         med_visits)
        self.assertEqual(response_get.context["page_object_med_results"],
                         med_results)

    def test_access_to_medical_page_logout_is_security_breach(self):
        """Accessing data of another user without access granted by this user
        is unsuccessful and user is logout."""

        # Test for user "abc_user" (user without access) attempt to see test_user data
        access_granted = Profile.objects.filter(
            access_granted_to=self.abc_user.email)
        self.assertFalse(access_granted.exists())
        self.client.force_login(self.test_user)
        test_user_profile_slug = self.test_profile.slug
        self.client.login(username="abc_user", password="testpass456")
        self.assertIn("_auth_user_id", self.client.session)
        response_get = self.client.get(reverse("access:data-access-medical",
                                       kwargs={"slug": test_user_profile_slug,
                                               "page": 1}), follow=True)

        self.assertRedirects(
            response_get,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_get.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do tych danych.", str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
