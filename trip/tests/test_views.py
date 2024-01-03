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
from trip.enums import (TripChoices, BasicChecklist, KeysChecklist,
                        CosmeticsChecklist, ElectronicsChecklist,
                        UsefulStaffChecklist, TrekkingChecklist,
                        HikingChecklist, CyclingChecklist, CampingChecklist,
                        FishingChecklist, SunbathingChecklist,
                        BusinessChecklist, CostGroup)
from trip.factories import (TripFactory, TripReportFactory, TripBasicFactory,
                            TripAdvancedFactory, TripCostFactory,
                            TripAdditionalInfoFactory, TripPersonalChecklistFactory)
from trip.forms import (TripForm, TripReportForm, TripCostForm,
                        TripBasicChecklistForm, TripAdvancedChecklistForm,
                        TripPersonalChecklistForm, TripAdditionalInfoForm)
from trip.models import (Trip, TripReport, TripCost, TripAdditionalInfo,
                         TripPersonalChecklist, TripAdvancedChecklist,
                         TripBasicChecklist)
from user.factories import UserFactory, ProfileFactory

User = get_user_model()
logger = logging.getLogger("test")


class TripBasicUrlsTest(TestCase):
    def setUp(self):
        # self.user = get_user_model().objects.create_user(username="johndoe123", email="jd@example.com", password="testpass456")
        self.user = UserFactory()
        self.trip = TripFactory(user=self.user)
        self.trip_report = TripReportFactory(user=self.user, trip=self.trip)
        self.trip_basic = TripBasicFactory(user=self.user, trip=self.trip)
        self.trip_advanced = TripAdvancedFactory(user=self.user, trip=self.trip)
        self.trip_checklist = TripPersonalChecklistFactory(user=self.user, trip=self.trip)
        self.trip_additional = TripAdditionalInfoFactory(user=self.user, trip=self.trip)
        self.trip_cost = TripCostFactory(user=self.user, trip=self.trip)

        self.trip_pages = [
            {"page": "trip:trips", "args": [],
             "template": "trip/trips.html"},
            {"page": "trip:single-trip", "args": [str(self.trip.id)],
             "template": "trip/single_trip.html"},
            {"page": "trip:add-trip", "args": [],
             "template": "trip/trip_form.html"},
            {"page": "trip:edit-trip", "args": [str(self.trip.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:delete-trip", "args": [str(self.trip.id)],
             "template": "trip/trip_delete_form.html"},

            {"page": "trip:add-trip-report", "args": [str(self.trip.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:edit-trip-report", "args": [str(self.trip_report.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:delete-trip-report", "args": [str(self.trip_report.id)],
             "template": "trip/trip_delete_form.html"},

            {"page": "trip:add-trip-basic", "args": [str(self.trip.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:edit-trip-basic", "args": [str(self.trip_basic.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:delete-trip-basic", "args": [str(self.trip_basic.id)],
             "template": "trip/trip_delete_form.html"},

            {"page": "trip:add-trip-advanced", "args": [str(self.trip.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:edit-trip-advanced", "args": [str(self.trip_advanced.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:delete-trip-advanced", "args": [str(self.trip_advanced.id)],
             "template": "trip/trip_delete_form.html"},

            {"page": "trip:add-trip-personal-checklist", "args": [str(self.trip.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:edit-trip-personal-checklist", "args": [str(self.trip_checklist.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:delete-trip-personal-checklist", "args": [str(self.trip_checklist.id)],
             "template": "trip/trip_delete_form.html"},

            {"page": "trip:add-trip-additional", "args": [str(self.trip.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:edit-trip-additional", "args": [str(self.trip_additional.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:delete-trip-additional", "args": [str(self.trip_additional.id)],
             "template": "trip/trip_delete_form.html"},

            {"page": "trip:add-trip-cost", "args": [str(self.trip.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:edit-trip-cost", "args": [str(self.trip_cost.id)],
             "template": "trip/trip_form.html"},
            {"page": "trip:delete-trip-cost", "args": [str(self.trip_cost.id)],
             "template": "trip/trip_delete_form.html"},
        ]

    def test_view_url_accessible_by_name_for_unauthenticated_user(self):
        """Test if view url is accessible by its name
        and returns redirect (302) for unauthenticated user."""
        for page in self.trip_pages:
            response_page = self.client.get(
                reverse(page["page"], args=page["args"]))
            self.assertEqual(response_page.status_code, 302)
            self.assertIn("login", response_page.url)

    def test_view_url_accessible_by_name_for_authenticated_user(self):
        """Test if view url is accessible by its name
         and returns desired page (200) for authenticated user."""
        self.client.force_login(self.user)
        for page in self.trip_pages:
            response_page = self.client.get(
                reverse(page["page"], args=page["args"]))
            self.assertEqual(response_page.status_code, 200)
            self.assertEqual(str(response_page.context["user"]), "testuser")

    def test_view_uses_correct_template(self):
        """Test if response returns correct page template."""
        # Test for authenticated user
        self.client.force_login(self.user)
        for page in self.trip_pages:
            response = self.client.get(reverse(page["page"], args=page["args"]))
            self.assertTemplateUsed(response, page["template"])


class TripViewTest(TestCase):
    """Test Trip views."""
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass456")
        self.trip = TripFactory(user=self.user, name="setup name", destination="setup place")
        self.test_trip = TripFactory(user=self.test_user, name="test name")
        self.trip_report = TripReportFactory(user=self.user, trip=self.trip)
        self.test_trip_report = TripReportFactory(
            user=self.test_user, trip=self.test_trip, description="test text")
        self.trip_basic = TripBasicFactory(user=self.user, trip=self.trip)
        self.test_trip_basic = TripBasicFactory(
            user=self.test_user, trip=self.test_trip, name="test name")
        self.trip_advanced = TripAdvancedFactory(user=self.user, trip=self.trip)
        self.test_trip_advanced = TripAdvancedFactory(
            user=self.test_user, trip=self.test_trip, name="test name")
        self.trip_personal_checklist = TripPersonalChecklistFactory(
            user=self.user, trip=self.trip)
        self.test_trip_personal_checklist = TripPersonalChecklistFactory(
            user=self.test_user, trip=self.test_trip, name="test name")
        self.trip_additional = TripAdditionalInfoFactory(
            user=self.user, trip=self.trip)
        self.test_trip_additional = TripAdditionalInfoFactory(
            user=self.test_user, trip=self.test_trip, name="test name")
        self.trip_cost = TripCostFactory(user=self.user, trip=self.trip)
        self.test_trip_cost = TripCostFactory(
            user=self.test_user, trip=self.test_trip, name="test name")

        self.payload = {
            "name": "New setup trip",
            "type": [TripChoices.CYCLING],
            "destination": "Setup place",
            "start_date": datetime.date(2020, 1, 1),
            "end_date": datetime.date(2020, 1, 11),
            "transport": "Bus",
            "estimated_cost": 1500,
            "participants_number": 3,
            "participants": "Jane, John, Jake",
            "access_granted": Access.ACCESS_GRANTED
        }

    def test_all_setup_instances_created(self):
        """Test if user account and trip model was created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 2)
        self.assertEqual(TripReport.objects.count(), 2)
        self.assertEqual(TripBasicChecklist.objects.count(), 2)
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)
        self.assertEqual(TripCost.objects.count(), 2)
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)

    def test_trips_302_redirect_if_unauthorized(self):
        """Test if trips page is unavailable for unauthorized users."""
        response = self.client.get(reverse("trip:trips"))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_trips_200_if_logged_in(self):
        """Test if trips page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:trips"))
        self.assertEqual(response_get.status_code, 200)

    def test_trips_correct_template_if_logged_in(self):
        """Test if trips page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:trips"))
        self.assertTemplateUsed(response_get, "trip/trips.html")

    def test_trips_initial_values_set_context_data(self):
        """Test if trips page displays correct context data."""
        trips = Trip.objects.filter(user=self.user).order_by("-updated")
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("trip:trips"))
        self.assertQuerysetEqual(response_get.context["trips"], trips)

    def test_trips_initial_values_set_trips_data(self):
        """Test if logged user can see data for trips without seeing
        trips of other users."""
        new_trip = TripFactory(user=self.user, name="new trip")

        # Test content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(reverse("trip:trips"))

        user = User.objects.get(id=self.client.session["_auth_user_id"])
        self.assertEqual(user, self.user)

        self.assertIn("johndoe123", response_get.content.decode())
        self.assertIn(self.trip.name, response_get.content.decode())
        self.assertIn(new_trip.name, response_get.content.decode())
        self.assertNotIn("testuser", response_get.content.decode())
        self.assertNotIn(self.test_trip.name, response_get.content.decode())

        self.client.logout()

        # Test content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(reverse("trip:trips"))

        user = User.objects.get(id=self.client.session["_auth_user_id"])
        self.assertEqual(user, self.test_user)

        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertNotIn(self.trip.name, response_get.content.decode())
        self.assertNotIn(new_trip.name, response_get.content.decode())
        self.assertIn("testuser", response_get.content.decode())
        self.assertIn(self.test_trip.name, response_get.content.decode())

    def test_single_trip_302_redirect_if_unauthorized(self):
        """ Test if single_trip page is unavailable for
        unauthenticated user (user is redirected to login page)."""
        response_get = self.client.get(
            reverse("trip:single-trip", args=[self.trip.id]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response_get.content.decode())
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(response_get.url.startswith("/login/"))

    def test_single_trip_200_if_logged_in(self):
        """Test if single_trip page return status code 200 for
        authenticated user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:single-trip", args=[self.trip.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_single_trip_correct_template_if_logged_in(self):
        """Test if single_trip page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:single-trip", args=[self.trip.id]))
        self.assertTemplateUsed(
            response_get, "trip/single_trip.html")

    def test_single_trip_initial_values_set_context_data(self):
        """Test if single_trip page displays correct context data."""
        trip_report = TripReport.objects.filter(trip=self.trip)
        basic_trip = TripBasicChecklist.objects.filter(trip=self.trip)
        advanced_trip = TripAdvancedChecklist.objects.filter(trip=self.trip)
        additional_trip = TripAdditionalInfo.objects.filter(trip=self.trip)
        trip_checklist = TripPersonalChecklist.objects.filter(trip=self.trip)
        trip_costs = TripCost.objects.filter(trip=self.trip)
        attachments = Attachment.objects.filter(trips=self.trip.id)
        queryset = TripCost.objects.filter(user=self.user, trip=self.trip)
        sum_of_costs = round(trip_costs[0].sum_of_trip_costs(queryset))
        cost_per_person = trip_costs[0].cost_per_person(queryset)
        cost_per_day = trip_costs[0].cost_per_day()
        cost_per_person_per_day = trip_costs[0].cost_per_person_per_day()
        days = (self.trip.end_date - self.trip.start_date).days + 1

        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:single-trip", args=[str(self.trip.id)]))
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertEqual(response_get.context["profile"], self.trip.user.profile)
        self.assertQuerysetEqual(response_get.context["trip_report"], trip_report)
        self.assertQuerysetEqual(response_get.context["trip_basic"], basic_trip)
        self.assertQuerysetEqual(response_get.context["trip_advanced"], advanced_trip)
        self.assertQuerysetEqual(response_get.context["trip_additional"],
                                 additional_trip)
        self.assertQuerysetEqual(response_get.context["trip_personal_checklist"],
                                 trip_checklist)
        self.assertQuerysetEqual(response_get.context["trip_costs"], trip_costs)
        self.assertQuerysetEqual(response_get.context["attachments"], attachments)
        self.assertEqual(round(response_get.context["sum_of_costs"], 0),
                         round(sum_of_costs, 0))
        self.assertEqual(response_get.context["cost_per_person"], cost_per_person)
        self.assertEqual(response_get.context["cost_per_day"], cost_per_day)
        self.assertEqual(response_get.context["cost_per_person_per_day"],
                         cost_per_person_per_day)
        self.assertEqual(response_get.context["days"], days)

    def test_single_trip_initial_values_set_trip_data(self):
        """Test if single_trip page displays correct trip data
        and data associated to that trip (only data of logged user)."""

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:single-trip", args=[self.trip.id]))

        self.assertIn(self.trip.name, response_get.content.decode())
        self.assertNotIn(self.test_trip.name, response_get.content.decode())
        self.assertIn(self.trip.destination, response_get.content.decode())
        self.assertNotIn(self.test_trip.destination,
                         response_get.content.decode())
        self.assertIn(self.trip_report.description, response_get.content.decode())
        self.assertNotIn(self.test_trip_report.description,
                         response_get.content.decode())
        self.assertIn(self.trip_basic.name, response_get.content.decode())
        self.assertNotIn(self.test_trip_basic.name, response_get.content.decode())
        self.assertIn(self.trip_advanced.name, response_get.content.decode())
        self.assertNotIn(self.test_trip_advanced.name,
                         response_get.content.decode())
        self.assertIn(self.trip_personal_checklist.name, response_get.content.decode())
        self.assertNotIn(self.test_trip_personal_checklist.name,
                         response_get.content.decode())
        self.assertIn(self.trip_additional.name, response_get.content.decode())
        self.assertNotIn(self.test_trip_additional.name,
                         response_get.content.decode())
        self.assertIn(self.trip_cost.name, response_get.content.decode())
        self.assertNotIn(self.test_trip_cost.name,
                         response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("trip:single-trip", args=[self.test_trip.id]))

        self.assertNotIn(self.trip.name, response_get.content.decode())
        self.assertIn(self.test_trip.name, response_get.content.decode())
        self.assertNotIn(self.trip.destination, response_get.content.decode())
        self.assertIn(self.test_trip.destination,
                      response_get.content.decode())
        self.assertNotIn(self.trip_report.description,
                         response_get.content.decode())
        self.assertIn(self.test_trip_report.description,
                      response_get.content.decode())
        self.assertNotIn(self.trip_basic.name, response_get.content.decode())
        self.assertIn(self.test_trip_basic.name, response_get.content.decode())
        self.assertNotIn(self.trip_advanced.name, response_get.content.decode())
        self.assertIn(self.test_trip_advanced.name, response_get.content.decode())
        self.assertNotIn(self.trip_personal_checklist.name,
                         response_get.content.decode())
        self.assertIn(self.test_trip_personal_checklist.name,
                      response_get.content.decode())
        self.assertNotIn(self.trip_additional.name,
                         response_get.content.decode())
        self.assertIn(self.test_trip_additional.name,
                      response_get.content.decode())
        self.assertNotIn(self.trip_cost.name, response_get.content.decode())
        self.assertIn(self.test_trip_cost.name, response_get.content.decode())

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_single_trip_initial_values_set_attachments(self):
        """Test if single_trip page displays correct attachments
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
        self.attachment.trips.add(self.trip)
        self.test_attachment.trips.add(self.test_trip)

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:single-trip", args=[self.trip.id]))
        trip_id = response_get.request["PATH_INFO"].split("/")[-2]
        self.assertQuerysetEqual(self.trip, Trip.objects.get(id=trip_id))
        self.assertIn(self.trip.name, response_get.content.decode())
        self.assertNotIn(self.test_trip.name, response_get.content.decode())
        self.assertIn(self.attachment.attachment_name,
                      response_get.content.decode())
        self.assertNotIn(self.test_attachment.attachment_name,
                         response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("trip:single-trip", args=[self.test_trip.id]))

        self.assertIn(self.test_trip.name, response_get.content.decode())
        self.assertNotIn(self.trip.name, response_get.content.decode())
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

    def test_single_trip_initial_values_set_counterparties_data(self):
        """Test if single_trip page displays correct counterparty data
        (only data of logged user)."""
        user_counterparty_1 = CounterpartyFactory(user=self.user, name="cp 1")
        user_counterparty_2 = CounterpartyFactory(user=self.user, name="cp 2")
        test_user_counterparty = CounterpartyFactory(user=self.test_user, name="test cp")
        self.assertEqual(Counterparty.objects.filter(user=self.user).count(), 2)
        self.assertEqual(Counterparty.objects.filter(user=self.test_user).count(), 1)
        user_counterparty_1.trips.add(self.trip)
        user_counterparty_1.save()
        user_counterparty_2.trips.add(self.trip)
        user_counterparty_2.save()
        test_user_counterparty.trips.add(self.test_trip)
        test_user_counterparty.save()

        # Page content for self.user
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:single-trip", args=[self.trip.id]))

        self.assertIn(user_counterparty_1.name, response_get.content.decode())
        self.assertIn(user_counterparty_2.name, response_get.content.decode())
        self.assertNotIn(test_user_counterparty.name, response_get.content.decode())

        self.client.logout()

        # Page content for self.test_user
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("trip:single-trip", args=[self.test_trip.id]))

        self.assertIn(test_user_counterparty.name, response_get.content.decode())
        self.assertNotIn(user_counterparty_1.name, response_get.content.decode())
        self.assertNotIn(user_counterparty_2.name, response_get.content.decode())

    def test_single_trip_forced_logout_if_security_breach(self):
        """Attempt to overview single trip of another user is forbidden and
        triggers logout."""

        # Attempt to see self.test_user data by self.test_user (successful response)
        self.client.force_login(self.test_user)
        response_get = self.client.get(
            reverse("trip:single-trip",
                    args=[self.test_trip.id]), follow=True)
        self.assertIn(self.test_trip.name, response_get.content.decode())
        self.client.logout()

        # Attempt to see self.test_user data by self.user (forbidden -> logout)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:single-trip",
                    args=[self.test_trip.id]), follow=True)
        self.assertNotIn(self.test_trip.name, response_get.content.decode())
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

    def test_add_trip_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add trip
        (user is redirected to login page)."""
        response = self.client.get(reverse("trip:add-trip"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_trip_200_if_logged_in(self):
        """Test if add_trip page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:add-trip"))
        self.assertEqual(response_get.status_code, 200)

    def test_add_trip_correct_template_if_logged_in(self):
        """Test if add_trip page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:add-trip"))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_add_trip_form_initial_values_set_context_data(self):
        """Test if add_trip page displays correct context data."""
        trip_names = list(Trip.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:add-trip"))
        self.assertEqual(response_get.context["page"], "add-trip")
        self.assertQuerysetEqual(response_get.context["trip_names"], trip_names)
        self.assertIsInstance(response_get.context["form"], TripForm)

    def test_add_trip_form_initial_values_set_form_data(self):
        """Test if add_trip page displays correct form data."""
        trip_fields = ["name", "type", "destination", "start_date",
                       "end_date", "transport", "estimated_cost",
                       "participants_number", "participants",
                       "reservations", "notes", "access_granted"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:add-trip"))
        for field in trip_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_trip_success_and_redirect(self):
        """Test if creating a trip is successful (status code 200) and
        redirecting is successful (status code 302)."""
        trip_names = list(Trip.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.force_login(self.user)
        response_post = self.client.post(
            reverse("trip:add-trip"),
            data=self.payload,
            trip_names=trip_names,
            follow=True)
        self.assertEqual(response_post.status_code, 200)
        self.assertTemplateUsed(response_post, template_name="trip/trips.html")

        self.assertRedirects(
            response_post,
            reverse("trip:trips"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Dodano podróż.", str(messages[0]))
        self.assertInHTML("New setup trip", response_post.content.decode())
        self.assertEqual(Trip.objects.count(), 3)
        self.assertTrue(Trip.objects.filter(
            user=self.user, name=self.payload["name"]).exists())

    def test_add_trip_successful_with_correct_user(self):
        """Test if creating a trip successfully has correct user."""
        trip_names = list(Trip.objects.filter(
            user=self.user).values_list("name", flat=True))
        self.client.force_login(self.user)
        self.client.post(reverse("trip:add-trip"),
                         data=self.payload,
                         trip_names=trip_names,
                         follow=True)
        trip = Trip.objects.get(name=self.payload["name"])
        self.assertEqual(trip.user, self.user)

    @parameterized.expand(
        [
            ("Empty field: name",
             {"access_granted": Access.ACCESS_GRANTED},
             "To pole jest wymagane."),
            ("Empty field: access_granted",
             {"name": "New name"},
             "To pole jest wymagane."),
            ("Not unique fields (unique together): name",
             {"name": "setup name", "access_granted": Access.ACCESS_GRANTED},
             "Istnieje już podróż o podanej nazwie w bazie danych. Podaj inną nazwę."),
            ("Incorrect date field",
             {"name": "some new name", "access_granted": Access.ACCESS_GRANTED,
              "start_date": "2020/11/11"},
             "Wpisz poprawną datę."),
            ("Incorrect date field - end date must cannot be before start date",
             {"name": "some new name", "access_granted": Access.ACCESS_GRANTED,
              "start_date": datetime.date(2020, 10, 10),
              "end_date": datetime.date(2020, 9, 9)},
             "Data zakończenia podróży nie może przypadać wcześniej niż "
             "data jej rozpoczęcia."),
            ("Incorrect estimated_cost field (negative values are not allowed)",
             {"name": "some new name", "access_granted": Access.ACCESS_GRANTED,
              "estimated_cost": -100},
             "Upewnij się, że ta wartość jest większa lub równa 0."),
            ("Incorrect participants_number field (negative values are not allowed)",
             {"name": "some new name", "access_granted": Access.ACCESS_GRANTED,
              "participants_number": -3},
             "Upewnij się, że ta wartość jest większa lub równa 0."),
        ]
    )
    def test_add_trip_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a trip is not successful if data is incorrect."""
        self.client.force_login(self.user)
        trip_names = list(Trip.objects.filter(
            user=self.trip.user).values_list("name", flat=True))
        response_post = self.client.post(
            reverse("trip:add-trip"),
            data=payload,
            trip_names=trip_names)
        self.assertEqual(Trip.objects.count(), 2)
        self.assertEqual(response_post.status_code,
                         200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_trip_302_redirect_if_unauthorized(self):
        """Test if edit_trip page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:edit-trip", args=[self.trip.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_trip_200_if_logged_in(self):
        """Test if edit_trip page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip", args=[self.trip.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_trip_correct_template_if_logged_in(self):
        """Test if edit_trip page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip", args=[self.trip.id]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_edit_trip_form_initial_values_set_context_data(self):
        """Test if edit_trip page displays correct context data."""
        trip_names = list(Trip.objects.filter(
            user=self.user).exclude(
            id=self.trip.id).values_list("name", flat=True))
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip", args=[str(self.trip.id)]))
        self.assertEqual(response_get.context["page"], "edit-trip")
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertQuerysetEqual(response_get.context["trip_names"],
                                 trip_names)
        self.assertIsInstance(response_get.context["form"], TripForm)

    def test_edit_trip_form_initial_values_set_form_data(self):
        """Test if edit_trip page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip", args=[str(self.trip.id)]))
        self.assertIn(self.trip.destination, response_get.content.decode())
        self.assertIn(self.trip.name, response_get.content.decode())

    def test_edit_trip_success_and_redirect(self):
        """Test if updating a trip is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        trip_names = list(Trip.objects.filter(
            user=self.user).exclude(
            id=self.trip.id).values_list("name", flat=True))

        payload = {
            "name": "yet another one",
            "type": [TripChoices.FISHING],
            "destination": "New place for holidays",
            "start_date": self.trip.start_date,
            "end_date": self.trip.end_date,
            "transport": "plane",
            "estimated_cost": 5500,
            "participants_number": 2,
            "participants": "Clark, Cloe",
            "access_granted": Access.ACCESS_GRANTED,
        }
        self.assertNotEqual(self.trip.name, payload["name"])
        self.assertNotEqual(self.trip.destination, payload["destination"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:edit-trip", args=[str(self.trip.id)]),
            data=payload,
            instance=self.trip,
            trip_names=trip_names,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip",
                    args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.", str(messages[0]))
        self.trip.refresh_from_db()
        self.assertEqual(Trip.objects.count(), 2)
        self.assertEqual(self.trip.destination, payload["destination"])
        self.assertEqual(self.trip.name, payload["name"])

    def test_edit_trip_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)
        trip_names = list(Trip.objects.filter(
            user=self.user).exclude(
            id=self.trip.id).values_list(
            "name", flat=True))

        # PATCH
        payload = {
            "name": "yet another one",
            "destination": "New place for holidays",
            "access_granted": Access.ACCESS_GRANTED,
        }
        response_patch = self.client.patch(
            reverse("trip:edit-trip", args=[str(self.trip.id)]),
            data=payload,
            instance=self.trip,
            trip_names=trip_names,
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "name": "yet another one",
            "type": self.trip.type,
            "destination": "New place for holidays",
            "start_date": self.trip.start_date,
            "end_date": self.trip.end_date,
            "transport": self.trip.transport,
            "estimated_cost": self.trip.estimated_cost,
            "participants_number": self.trip.participants_number,
            "participants": self.trip.participants,
            "access_granted": Access.ACCESS_GRANTED,
        }
        response_put = self.client.put(
            reverse("trip:edit-trip", args=[str(self.trip.id)]),
            data=payload,
            instance=self.trip,
            trip_names=trip_names,
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:edit-trip", args=[str(self.trip.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_trip_logout_if_security_breach(self):
        """Editing trip of another user is unsuccessful and triggers logout."""
        trip_names = list(Trip.objects.filter(
            user=self.user).exclude(
            id=self.trip.id).values_list(
            "name", flat=True))

        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_trip.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "yet another one",
            "type": [TripChoices.FISHING],
            "destination": "New place for holidays",
            "start_date": self.trip.start_date,
            "end_date": self.trip.end_date,
            "transport": "plane",
            "estimated_cost": 5500,
            "participants_number": 2,
            "participants": "Clark, Cloe",
            "access_granted": Access.ACCESS_GRANTED,
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("trip:edit-trip", args=[str(self.test_trip.id)]),
            data=payload,
            content_type="text/html",
            trip_names=trip_names,
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
        self.assertEqual(Trip.objects.count(), 2)
        self.assertNotIn(self.test_trip.destination, payload["destination"])

    def test_delete_trip_302_redirect_if_unauthorized(self):
        """Test if delete_trip page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:delete-trip", args=[self.trip.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_trip_200_if_logged_in(self):
        """Test if delete_trip page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip", args=[self.trip.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_trip_correct_template_if_logged_in(self):
        """Test if delete_trip page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip", args=[self.trip.id]))
        self.assertTemplateUsed(response_get, "trip/trip_delete_form.html")

    def test_delete_trip_initial_values_set_context_data(self):
        """Test if delete_trip page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:delete-trip", args=[str(self.trip.id)]))
        self.assertIn(str(self.trip), response_get.content.decode())
        self.assertEqual(response_get.context["page"], "delete-trip")
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)

    def test_delete_trip_successful_and_redirect(self):
        """Deleting trip with all trip related information
        is successful (status code 200) and redirect is successful
        (status code 302)."""
        self.client.force_login(self.user)
        response_delete = self.client.post(
            reverse("trip:delete-trip", args=[self.trip.id]),
            content_type="text/html", follow=True)
        self.assertRedirects(
            response_delete,
            reverse("trip:trips"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto podróż wraz z informacjami dodatkowymi.",
                      str(messages[0]))

        response = self.client.get(reverse("trip:trips"))
        self.assertEqual(Trip.objects.count(), 1)
        self.assertNotIn(self.trip.name, response.content.decode())
        self.assertNotIn(self.test_trip.name, response.content.decode())
        self.assertEqual(TripCost.objects.count(), 1)
        self.assertEqual(TripReport.objects.count(), 1)
        self.assertEqual(TripBasicChecklist.objects.count(), 1)
        self.assertEqual(TripAdvancedChecklist.objects.count(), 1)
        self.assertEqual(TripAdditionalInfo.objects.count(), 1)
        self.assertEqual(TripPersonalChecklist.objects.count(), 1)

    def test_delete_trip_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("trip:delete-trip", args=[str(self.trip.id)]),
            follow=False
        )
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:delete-trip", args=[str(self.trip.id)]),
            follow=False
        )
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:delete-trip", args=[str(self.trip.id)]),
            follow=False
        )
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_trip_logout_if_security_breach(self):
        """Deleting trip of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(Trip.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_trip.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("trip:delete-trip", args=[str(self.test_trip.id)]),
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
        self.assertEqual(Trip.objects.count(), 2)


class TripReportViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass456")
        self.trip = TripFactory(user=self.user, name="setup name")
        self.test_trip = TripFactory(user=self.test_user, name="test name")
        self.trip_report = TripReportFactory(user=self.user, trip=self.trip)
        self.test_trip_report = TripReportFactory(
            user=self.test_user, trip=self.test_trip, description="test trip")

        self.payload = {
            "start_date": datetime.date(2020, 10, 10),
            "end_date": datetime.date(2020, 10, 12),
            "description": "Report from short trip",
            "notes": self.trip_report.notes,
            "facebook": self.trip_report.facebook,
            "youtube": self.trip_report.youtube,
            "instagram": self.trip_report.instagram,
            "pinterest": "https://pl.pinterest.com/",
            "link": self.trip_report.link,
        }

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 2)
        self.assertEqual(TripReport.objects.count(), 2)

    def test_add_trip_report_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add trip report
        (user is redirected to login page)."""
        response = self.client.get(reverse("trip:add-trip-report",
                                           args=[str(self.trip_report.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_trip_report_result_200_if_logged_in(self):
        """Test if add_trip_report page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-report", args=[str(self.trip.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_trip_report_correct_template_if_logged_in(self):
        """Test if add_trip_report page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:add-trip-report",
                                               args=[str(self.trip.id)]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_add_trip_report_form_initial_values_set_context_data(self):
        """Test if add_trip_report page displays correct context data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-report", args=[str(self.trip.id)]))
        self.assertEqual(response_get.context["page"], "add-trip-report")
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_report"], TripReportForm)

    def test_add_trip_report_form_initial_values_set_form_data(self):
        """Test if add_trip_report page displays correct form data."""
        trip_fields = ["start_date", "end_date", "description", "notes",
                       "facebook", "youtube", "instagram", "pinterest", "link"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-report", args=[str(self.trip.id)]))
        for field in trip_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_trip_report_success_and_redirect(self):
        """Test if creating a trip report successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(TripReport.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-report", args=[str(self.trip.id)]),
            data=self.payload, follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.",
                      str(messages[0]))
        self.assertInHTML(self.payload["description"],
                          response_post.content.decode())
        self.assertEqual(TripReport.objects.count(), 3)
        self.assertTrue(TripReport.objects.filter(
            user=self.user, end_date=self.payload["end_date"]).exists())

    def test_add_trip_report_successful_with_correct_user(self):
        """Test if creating a trip report successfully has correct user."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-report", args=[str(self.trip.id)]),
            self.payload, follow=True)

        report = TripReport.objects.get(description=self.payload["description"])
        self.assertEqual(report.user, self.user)

    def test_add_trip_report_successful_with_correct_trip(self):
        """Test if creating a trip report successfully has correct
        trip as foreign key."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-report", args=[str(self.trip.id)]),
            self.payload, follow=True)

        report = TripReport.objects.get(description=self.payload["description"])
        self.assertQuerysetEqual(report.trip, self.trip)
        self.assertNotEqual(report.trip, self.test_trip)

    @parameterized.expand(
        [
            ("Incorrect date field",
             {"description": "sth new", "start_date": "2020/11/11"},
             "Wpisz poprawną datę."),
            ("Incorrect url field",
             {"link": "yahoo"},
             "Wpisz poprawny URL."),
            ("Incorrect date field - end date must cannot be before start date",
             {"start_date": datetime.date(2020, 10, 10),
              "end_date": datetime.date(2020, 9, 9)},
             "Data zakończenia relacji nie może przypadać wcześniej niż "
             "data jej rozpoczęcia."),
        ]
    )
    def test_add_trip_report_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a trip_report is not successful if data is incorrect."""
        self.assertEqual(TripReport.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-report", args=[str(self.trip.id)]),
            payload)
        self.assertEqual(TripReport.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_trip_report_302_redirect_if_unauthorized(self):
        """Test if edit_trip_report page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:edit-trip-report", args=[self.trip_report.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_trip_report_200_if_logged_in(self):
        """Test if edit_trip_report page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-report", args=[self.trip_report.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_trip_report_correct_template_if_logged_in(self):
        """Test if edit_trip_report page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-report", args=[self.trip_report.id]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_edit_trip_report_form_initial_values_set_context_data(self):
        """Test if edit_trip_report page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-report", args=[str(self.trip_report.id)]))
        self.assertEqual(response_get.context["page"], "edit-trip-report")
        self.assertQuerysetEqual(response_get.context["trip_report"],
                                 self.trip_report)
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_report"], TripReportForm)

    def test_edit_trip_report_form_initial_values_set(self):
        """Test if edit_trip_report page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-report", args=[str(self.trip_report.id)]))
        self.assertIn(self.trip_report.description, response_get.content.decode())
        self.assertIn(self.trip_report.youtube, response_get.content.decode())

    def test_edit_trip_report_success_and_redirect(self):
        """Test if updating a trip_report is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        payload = {
            "start_date": datetime.date(2020, 11, 11),
            "end_date": datetime.date(2020, 12, 12),
            "description": "New report from a trip",
            "notes": "Sth new to check",
            "facebook": self.trip_report.facebook,
            "youtube": self.trip_report.youtube,
            "instagram": self.trip_report.instagram,
            "pinterest": self.trip_report.pinterest,
            "link": self.trip_report.link,
        }
        self.assertNotEqual(self.trip_report.description, payload["description"])
        self.assertNotEqual(self.trip_report.notes, payload["notes"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:edit-trip-report", args=[str(self.trip_report.id)]),
            data=payload,
            instance=self.trip_report,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.", str(messages[0]))
        self.trip_report.refresh_from_db()
        self.assertEqual(TripReport.objects.count(), 2)
        self.assertEqual(self.trip_report.notes, payload["notes"])
        self.assertEqual(self.trip_report.description, payload["description"])

    def test_edit_trip_report_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "start_date": datetime.date(2020, 11, 11),
            "end_date": datetime.date(2020, 12, 12),
            "description": "New report from a trip",
            "notes": "Sth new to check",
        }
        response_patch = self.client.patch(
            reverse("trip:edit-trip-report", args=[str(self.trip_report.id)]),
            data=payload,
            instance=self.trip_report,
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        payload = {
            "start_date": datetime.date(2020, 11, 11),
            "end_date": datetime.date(2020, 12, 12),
            "description": "New report from a trip",
            "notes": "Sth new to check",
            "facebook": self.trip_report.facebook,
            "youtube": self.trip_report.youtube,
            "instagram": self.trip_report.instagram,
            "pinterest": self.trip_report.pinterest,
            "link": self.trip_report.link,
        }
        response_put = self.client.put(
            reverse("trip:edit-trip-report", args=[str(self.trip_report.id)]),
            data=payload,
            instance=self.trip_report,
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:edit-trip-report", args=[str(self.trip_report.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_trip_report_logout_if_security_breach(self):
        """Editing trip_report of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_trip_report.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "start_date": datetime.date(2020, 11, 11),
            "end_date": datetime.date(2020, 12, 12),
            "description": "SECURITY BREACH",
            "notes": "SECURITY BREACH",
            "facebook": self.trip_report.facebook,
            "youtube": self.trip_report.youtube,
            "instagram": self.trip_report.instagram,
            "pinterest": self.trip_report.pinterest,
            "link": self.trip_report.link,
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("trip:edit-trip-report",
                    args=[str(self.test_trip_report.id)]),
            data=payload,
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)

        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(TripReport.objects.count(), 2)
        self.assertNotIn(self.test_trip_report.notes, payload["notes"])

    def test_delete_trip_report_302_redirect_if_unauthorized(self):
        """Test if delete_trip_report page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:delete-trip-report", args=[self.trip_report.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_trip_report_200_if_logged_in(self):
        """Test if delete_trip_report page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-report", args=[self.trip_report.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_trip_report_correct_template_if_logged_in(self):
        """Test if delete_trip_report page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-report", args=[self.trip_report.id]))
        self.assertTemplateUsed(response_get,
                                "trip/trip_delete_form.html")

    def test_delete_trip_report_initial_values_set_context_data(self):
        """Test if delete_trip_report page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:delete-trip-report", args=[str(self.trip_report.id)]))
        self.assertEqual(response_get.context["page"], "delete-trip-report")
        self.assertQuerysetEqual(response_get.context["trip_report"], self.trip_report)
        self.assertEqual(str(response_get.context["trip_id"]), str(self.trip.id))

    def test_delete_trip_report_and_redirect(self):
        """Deleting trip report is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(TripReport.objects.count(), 2)
        self.client.force_login(self.user)

        response_delete = self.client.post(
            reverse("trip:delete-trip-report", args=[str(self.trip_report.id)]),
            content_type="text/html", follow=True,)
        self.assertRedirects(
            response_delete,
            reverse("trip:single-trip", args=[self.trip.id]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto opis podróży.", str(messages[0]))

        response = self.client.get(
            reverse("trip:single-trip", args=[str(self.trip.id)]))
        self.assertEqual(TripReport.objects.count(), 1)
        self.assertNotIn(self.trip_report.notes, response.content.decode())
        self.assertNotIn(self.test_trip_report.notes, response.content.decode())

    def test_delete_trip_report_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("trip:delete-trip-report",
                    args=[str(self.trip_report.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:delete-trip-report",
                    args=[str(self.trip_report.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:delete-trip-report",
                    args=[str(self.trip_report.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_trip_report_logout_if_security_breach(self):
        """Deleting trip report of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(TripReport.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_trip_report.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("trip:delete-trip-report",
                    args=[str(self.test_trip_report.id)]),
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
        self.assertEqual(TripReport.objects.count(), 2)


class TripBasicChecklistViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456"
        )
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass456"
        )
        self.trip = TripFactory(user=self.user, name="setup name")
        self.test_trip = TripFactory(user=self.test_user, name="test name")
        self.trip_basic = TripBasicFactory(
            user=self.user, trip=self.trip, name="setup basic name")
        self.test_trip_basic = TripBasicFactory(
            user=self.test_user, trip=self.test_trip, name="test basic name")
        self.payload = {
            "name": "New basic equipment",
            "wallet": "Paszport",
            "keys": ["Samochód", "Bagażnik"],
            "cosmetics": ["Szczotka do zębów", "Dezodorant"],
            "electronics": ["Ładowarka", "Baterie", "Kable"],
            "useful_stuff": [],
            "basic_drugs": "Wit. C, wit. D",
            "additional_drugs": "coldrex, gripex",
        }

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 2)
        self.assertEqual(TripBasicChecklist.objects.count(), 2)

    def test_add_trip_basic_checklist_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add trip basic checklist
        (user is redirected to login page)."""
        response = self.client.get(reverse("trip:add-trip-basic",
                                           args=[str(self.trip_basic.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_trip_basic_checklist_result_200_if_logged_in(self):
        """Test if add_trip_basic page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-basic", args=[str(self.trip.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_trip_basic_checklist_correct_template_if_logged_in(self):
        """Test if add_trip_basic page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:add-trip-basic",
                                               args=[str(self.trip.id)]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_add_trip_basic_checklist_form_initial_values_set_context_data(self):
        """Test if add_trip_basic page displays correct context data."""
        trip_names = TripBasicChecklist.objects.filter(
            user=self.user).values_list("name", flat=True)
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-basic", args=[str(self.trip.id)]))
        self.assertEqual(response_get.context["page"], "add-trip-basic")
        self.assertQuerysetEqual(response_get.context["trip_names"], trip_names)
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_basic"], TripBasicChecklistForm)

    def test_add_trip_basic_checklist_form_initial_values_set_form_data(self):
        """Test if add_trip_basic page displays correct form data."""
        trip_fields = ["name", "wallet", "keys", "cosmetics", "electronics",
                       "useful_stuff", "basic_drugs", "additional_drugs"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-basic", args=[str(self.trip.id)]))
        for field in trip_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_trip_basic_checklist_success_and_redirect(self):
        """Test if creating a trip basic checklist successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(TripBasicChecklist.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-basic", args=[str(self.trip.id)]),
            data=self.payload, follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.",
                      str(messages[0]))
        self.assertInHTML(self.payload["name"],
                          response_post.content.decode())
        self.assertEqual(TripBasicChecklist.objects.count(), 3)
        self.assertTrue(TripBasicChecklist.objects.filter(
            user=self.user, additional_drugs=self.payload["additional_drugs"]).exists())

    def test_add_trip_basic_checklist_successful_with_correct_user(self):
        """Test if creating a trip basic checklist successfully has correct user."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-basic", args=[str(self.trip.id)]),
            self.payload, follow=True)

        checklist = TripBasicChecklist.objects.get(
            additional_drugs=self.payload["additional_drugs"])
        self.assertEqual(checklist.user, self.user)

    def test_add_trip_basic_checklist_successful_with_correct_trip(self):
        """Test if creating a trip basic successfully has correct
        trip as foreign key."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-basic", args=[str(self.trip.id)]),
            self.payload, follow=True)

        checklist = TripBasicChecklist.objects.get(
            additional_drugs=self.payload["additional_drugs"])
        self.assertQuerysetEqual(checklist.trip, self.trip)
        self.assertNotEqual(checklist.trip, self.test_trip)

    @parameterized.expand(
        [
            ("Empty field: name", {"additional_drugs": "ABCD"},
             "To pole jest wymagane."),
            ("Not unique field: name", {"name": "setup basic name"},
             "Istnieje już wyposażenie o podanej nazwie w bazie danych."),
        ]
    )
    def test_add_trip_basic_checklist_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a trip basic checklist is not successful if data is incorrect."""
        trip_names = TripBasicChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_basic.id).values_list("name", flat=True)
        self.assertEqual(TripBasicChecklist.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-basic", args=[str(self.trip.id)]),
            payload, trip_names=trip_names)
        self.assertEqual(TripBasicChecklist.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_trip_basic_checklist_302_redirect_if_unauthorized(self):
        """Test if edit_trip_basic page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:edit-trip-basic", args=[self.trip_basic.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_trip_basic_checklist_200_if_logged_in(self):
        """Test if edit_trip_basic page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-basic", args=[self.trip_basic.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_trip_basic_checklist_correct_template_if_logged_in(self):
        """Test if edit_trip_basic page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-basic", args=[self.trip_basic.id]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_edit_trip_basic_checklist_form_initial_values_set_context_data(self):
        """Test if edit_trip_basic page displays correct context data."""
        trip_names = TripBasicChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_basic.id).values_list("name", flat=True)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-basic", args=[str(self.trip_basic.id)]))
        self.assertEqual(response_get.context["page"], "edit-trip-basic")
        self.assertQuerysetEqual(response_get.context["trip_basic"],
                                 self.trip_basic)
        self.assertQuerysetEqual(response_get.context["trip_names"], trip_names)
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_basic"],
                              TripBasicChecklistForm)

    def test_edit_trip_basic_checklist_form_initial_values_set(self):
        """Test if edit_trip_basic page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-basic", args=[str(self.trip_basic.id)]))
        self.assertIn(self.trip_basic.name, response_get.content.decode())
        self.assertIn(self.trip_basic.additional_drugs, response_get.content.decode())

    def test_edit_trip_basic_checklist_success_and_redirect(self):
        """Test if updating a trip_basic_checklist is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        trip_names = TripBasicChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_basic.id).values_list("name", flat=True)
        self.assertNotEqual(self.trip_basic.additional_drugs,
                            self.payload["additional_drugs"])
        self.assertNotEqual(self.trip_basic.name, self.payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:edit-trip-basic", args=[str(self.trip_basic.id)]),
            data=self.payload,
            instance=self.trip_basic,
            trip_names=trip_names,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.", str(messages[0]))
        self.trip_basic.refresh_from_db()
        self.assertEqual(TripBasicChecklist.objects.count(), 2)
        self.assertEqual(self.trip_basic.name, self.payload["name"])
        self.assertEqual(self.trip_basic.additional_drugs,
                         self.payload["additional_drugs"])

    def test_edit_trip_basic_checklist_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        trip_names = TripBasicChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_basic.id).values_list("name", flat=True)
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "New sth",
            "wallet": self.payload["wallet"],
            "keys": self.payload["keys"],
        }
        response_patch = self.client.patch(
            reverse("trip:edit-trip-basic", args=[str(self.trip_basic.id)]),
            data=payload,
            instance=self.trip_basic,
            trip_names=trip_names,
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:edit-trip-basic", args=[str(self.trip_basic.id)]),
            data=self.payload,
            instance=self.trip_basic,
            trip_names=trip_names,
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:edit-trip-basic", args=[str(self.trip_basic.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_trip_basic_checklist_logout_if_security_breach(self):
        """Editing trip_basic of another user is unsuccessful and triggers logout."""
        trip_names = TripBasicChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_basic.id).values_list("name", flat=True)
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_trip_basic.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "wallet": "Paszport",
            "keys": ["Samochód", "Bagażnik"],
            "cosmetics": ["Szczotka do zębów", "Dezodorant"],
            "electronics": ["Ładowarka", "Baterie", "Kable"],
            "useful_stuff": [],
            "basic_drugs": "Wit. C, wit. D",
            "additional_drugs": "SECURITY BREACH",
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("trip:edit-trip-basic",
                    args=[str(self.test_trip_basic.id)]),
            data=payload,
            trip_names=trip_names,
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)

        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(TripBasicChecklist.objects.count(), 2)
        self.assertNotIn(self.test_trip_basic.name, payload["name"])

    def test_delete_trip_basic_checklist_302_redirect_if_unauthorized(self):
        """Test if delete_trip_basic page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:delete-trip-basic", args=[self.trip_basic.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_trip_basic_checklist_200_if_logged_in(self):
        """Test if delete_trip_basic page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-basic", args=[self.trip_basic.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_trip_basic_checklist_correct_template_if_logged_in(self):
        """Test if delete_trip_basic page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-basic", args=[self.trip_basic.id]))
        self.assertTemplateUsed(response_get,
                                "trip/trip_delete_form.html")

    def test_delete_trip_basic_checklist_initial_values_set_context_data(self):
        """Test if delete_trip_basic page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:delete-trip-basic", args=[str(self.trip_basic.id)]))
        self.assertEqual(response_get.context["page"], "delete-trip-basic")
        self.assertQuerysetEqual(response_get.context["trip_basic"], self.trip_basic)
        self.assertEqual(str(response_get.context["trip_id"]), str(self.trip.id))

    def test_delete_trip_basic_checklist_and_redirect(self):
        """Deleting trip basic checklist is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(TripBasicChecklist.objects.count(), 2)
        self.client.force_login(self.user)

        response_delete = self.client.post(
            reverse("trip:delete-trip-basic", args=[str(self.trip_basic.id)]),
            content_type="text/html", follow=True,)
        self.assertRedirects(
            response_delete,
            reverse("trip:single-trip", args=[self.trip.id]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto podstawowe wyposażenie podróży.",
                      str(messages[0]))

        response = self.client.get(
            reverse("trip:single-trip", args=[str(self.trip.id)]))
        self.assertEqual(TripBasicChecklist.objects.count(), 1)
        self.assertNotIn(self.trip_basic.name, response.content.decode())
        self.assertNotIn(self.test_trip_basic.name, response.content.decode())

    def test_delete_trip_basic_checklist_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("trip:delete-trip-basic",
                    args=[str(self.trip_basic.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:delete-trip-basic",
                    args=[str(self.trip_basic.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:delete-trip-basic",
                    args=[str(self.trip_basic.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_trip_basic_checklist_logout_if_security_breach(self):
        """Deleting trip basic checklist of another user is unsuccessful and
        triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(TripBasicChecklist.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_trip_basic.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("trip:delete-trip-basic",
                    args=[str(self.test_trip_basic.id)]),
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
        self.assertEqual(TripBasicChecklist.objects.count(), 2)


class TripAdvancedChecklistViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456")
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass456")
        self.trip = TripFactory(user=self.user, name="setup name")
        self.test_trip = TripFactory(user=self.test_user, name="test name")
        self.trip_advanced = TripAdvancedFactory(
            user=self.user, trip=self.trip, name="setup advanced name")
        self.test_trip_advanced = TripAdvancedFactory(
            user=self.test_user, trip=self.test_trip, name="test advanced name")

        self.payload = {
            "name": "New advanced equipment",
            "trekking": ["Scyzoryk", "Pokrowiec na plecak"],
            "hiking": ["Liny", "Uprząż", "Śruby", "Haki"],
            "cycling": "Okulary/google",
            "camping": ["Karimata", "Materac"],
            "fishing": [],
            "sunbathing": ["Nakrycie głowy"],
            "business": ["Dokumenty"],
        }

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 2)
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)

    def test_add_trip_advanced_checklist_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add trip advanced checklist
        (user is redirected to login page)."""
        response = self.client.get(reverse("trip:add-trip-advanced",
                                           args=[str(self.trip_advanced.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_trip_advanced_checklist_result_200_if_logged_in(self):
        """Test if add_trip_advanced page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-advanced", args=[str(self.trip.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_trip_advanced_checklist_correct_template_if_logged_in(self):
        """Test if add_trip_advanced page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:add-trip-advanced",
                                               args=[str(self.trip.id)]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_add_trip_advanced_checklist_form_initial_values_set_context_data(self):
        """Test if add_trip_advanced page displays correct context data."""
        trip_names = TripAdvancedChecklist.objects.filter(
            user=self.user).values_list("name", flat=True)
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-advanced", args=[str(self.trip.id)]))
        self.assertEqual(response_get.context["page"], "add-trip-advanced")
        self.assertQuerysetEqual(response_get.context["trip_names"], trip_names)
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_advanced"],
                              TripAdvancedChecklistForm)

    def test_add_trip_advanced_checklist_form_initial_values_set_form_data(self):
        """Test if add_trip_advanced page displays correct form data."""
        trip_fields = ["name", "trekking", "hiking", "cycling", "camping",
                       "fishing", "sunbathing", "business"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-advanced", args=[str(self.trip.id)]))
        for field in trip_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_trip_advanced_checklist_success_and_redirect(self):
        """Test if creating a trip advanced checklist successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-advanced", args=[str(self.trip.id)]),
            data=self.payload, follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.",
                      str(messages[0]))
        self.assertInHTML(self.payload["name"],
                          response_post.content.decode())
        self.assertEqual(TripAdvancedChecklist.objects.count(), 3)
        self.assertTrue(TripAdvancedChecklist.objects.filter(
            user=self.user, trekking=",".join(self.payload["trekking"])).exists())

    def test_add_trip_advanced_checklist_successful_with_correct_user(self):
        """Test if creating a trip advanced checklist successfully has correct user."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-advanced", args=[str(self.trip.id)]),
            self.payload, follow=True)

        checklist = TripAdvancedChecklist.objects.get(
            trekking=",".join(self.payload["trekking"]))
        self.assertEqual(checklist.user, self.user)

    def test_add_trip_advanced_checklist_successful_with_correct_trip(self):
        """Test if creating a trip advanced successfully has correct
        trip as foreign key."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-advanced", args=[str(self.trip.id)]),
            self.payload, follow=True)

        checklist = TripAdvancedChecklist.objects.get(
            trekking=",".join(self.payload["trekking"]))
        self.assertQuerysetEqual(checklist.trip, self.trip)
        self.assertNotEqual(checklist.trip, self.test_trip)

    @parameterized.expand(
        [
            ("Empty field: name", {"trekking": ["Czekan"]},
             "To pole jest wymagane."),
            ("Not unique field: name", {"name": "setup advanced name"},
             "Istnieje już wyposażenie o podanej nazwie w bazie danych."),
        ]
    )
    def test_add_trip_advanced_checklist_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a trip advanced checklist is not successful if data is incorrect."""
        trip_names = TripAdvancedChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_advanced.id).values_list("name", flat=True)
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-advanced", args=[str(self.trip.id)]),
            payload, trip_names=trip_names)
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_trip_advanced_checklist_302_redirect_if_unauthorized(self):
        """Test if edit_trip_advanced page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:edit-trip-advanced", args=[self.trip_advanced.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_trip_advanced_checklist_200_if_logged_in(self):
        """Test if edit_trip_advanced page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-advanced", args=[self.trip_advanced.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_trip_advanced_checklist_correct_template_if_logged_in(self):
        """Test if edit_trip_advanced page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-advanced", args=[self.trip_advanced.id]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_edit_trip_advanced_checklist_form_initial_values_set_context_data(self):
        """Test if edit_trip_advanced page displays correct context data."""
        trip_names = TripAdvancedChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_advanced.id).values_list("name", flat=True)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-advanced", args=[str(self.trip_advanced.id)]))
        self.assertEqual(response_get.context["page"], "edit-trip-advanced")
        self.assertQuerysetEqual(response_get.context["trip_advanced"],
                                 self.trip_advanced)
        self.assertQuerysetEqual(response_get.context["trip_names"], trip_names)
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_advanced"],
                              TripAdvancedChecklistForm)

    def test_edit_trip_advanced_checklist_form_initial_values_set(self):
        """Test if edit_trip_advanced page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-advanced", args=[str(self.trip_advanced.id)]))
        self.assertIn(self.trip_advanced.name, response_get.content.decode())
        self.assertIn(self.trip_advanced.trekking[0], response_get.content.decode())

    def test_edit_trip_advanced_checklist_success_and_redirect(self):
        """Test if updating a trip_advanced_checklist is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        trip_names = TripAdvancedChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_advanced.id).values_list("name", flat=True)
        self.assertNotEqual(self.trip_advanced.trekking,
                            self.payload["trekking"])
        self.assertNotEqual(self.trip_advanced.name, self.payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:edit-trip-advanced", args=[str(self.trip_advanced.id)]),
            data=self.payload,
            instance=self.trip_advanced,
            trip_names=trip_names,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.", str(messages[0]))
        self.trip_advanced.refresh_from_db()
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)
        self.assertEqual(self.trip_advanced.name, self.payload["name"])
        self.assertEqual(self.trip_advanced.trekking, ",".join(self.payload["trekking"]))

    def test_edit_trip_advanced_checklist_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        trip_names = TripAdvancedChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_advanced.id).values_list("name", flat=True)
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "New sth",
            "trekking": ["Scyzoryk", "Pokrowiec na plecak"],
            "cycling": "Okulary/google",
        }
        response_patch = self.client.patch(
            reverse("trip:edit-trip-advanced", args=[str(self.trip_advanced.id)]),
            data=payload,
            instance=self.trip_advanced,
            trip_names=trip_names,
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:edit-trip-advanced", args=[str(self.trip_advanced.id)]),
            data=self.payload,
            instance=self.trip_advanced,
            trip_names=trip_names,
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:edit-trip-advanced", args=[str(self.trip_advanced.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_trip_advanced_checklist_logout_if_security_breach(self):
        """Editing trip_basic of another user is unsuccessful and triggers logout."""
        trip_names = TripAdvancedChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_advanced.id).values_list("name", flat=True)
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_trip_advanced.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "trekking": [TrekkingChecklist.THERMOS, TrekkingChecklist.SNOWSHOES,
                         TrekkingChecklist.TREKKING_POLES],
            "hiking": self.payload["hiking"],
            "cycling": self.payload["cycling"],
            "camping": self.payload["camping"],
            "fishing": self.payload["fishing"],
            "sunbathing": self.payload["sunbathing"],
            "business": self.payload["business"],
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("trip:edit-trip-advanced",
                    args=[str(self.test_trip_advanced.id)]),
            data=payload,
            trip_names=trip_names,
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)

        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)
        self.assertNotIn(self.test_trip_advanced.name, payload["name"])

    def test_delete_trip_advanced_checklist_302_redirect_if_unauthorized(self):
        """Test if delete_trip_basic page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:delete-trip-advanced", args=[self.trip_advanced.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_trip_advanced_checklist_200_if_logged_in(self):
        """Test if delete_trip_advanced page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-advanced", args=[self.trip_advanced.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_trip_advanced_checklist_correct_template_if_logged_in(self):
        """Test if delete_trip_advanced page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-advanced", args=[self.trip_advanced.id]))
        self.assertTemplateUsed(response_get,
                                "trip/trip_delete_form.html")

    def test_delete_trip_advanced_checklist_initial_values_set_context_data(self):
        """Test if delete_trip_advanced page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:delete-trip-advanced", args=[str(self.trip_advanced.id)]))
        self.assertEqual(response_get.context["page"], "delete-trip-advanced")
        self.assertQuerysetEqual(response_get.context["trip_advanced"],
                                 self.trip_advanced)
        self.assertEqual(str(response_get.context["trip_id"]), str(self.trip.id))

    def test_delete_trip_advanced_checklist_and_redirect(self):
        """Deleting trip advanced checklist is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)
        self.client.force_login(self.user)

        response_delete = self.client.post(
            reverse("trip:delete-trip-advanced", args=[str(self.trip_advanced.id)]),
            content_type="text/html", follow=True,)
        self.assertRedirects(
            response_delete,
            reverse("trip:single-trip", args=[self.trip.id]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto zaawansowane wyposażenie podróży.",
                      str(messages[0]))

        response = self.client.get(
            reverse("trip:single-trip", args=[str(self.trip.id)]))
        self.assertEqual(TripAdvancedChecklist.objects.count(), 1)
        self.assertNotIn(self.trip_advanced.name, response.content.decode())
        self.assertNotIn(self.test_trip_advanced.name, response.content.decode())

    def test_delete_trip_advanced_checklist_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("trip:delete-trip-advanced",
                    args=[str(self.trip_advanced.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:delete-trip-advanced",
                    args=[str(self.trip_advanced.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:delete-trip-advanced",
                    args=[str(self.trip_advanced.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_trip_advanced_checklist_logout_if_security_breach(self):
        """Deleting trip advanced checklist of another user is unsuccessful and
        triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_trip_advanced.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("trip:delete-trip-advanced",
                    args=[str(self.test_trip_advanced.id)]),
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
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)


class TripPersonalChecklistViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456"
        )
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass456"
        )
        self.trip = TripFactory(user=self.user, name="setup name")
        self.test_trip = TripFactory(user=self.test_user, name="test name")
        self.trip_personal = TripPersonalChecklistFactory(
            user=self.user, trip=self.trip, name="setup personal name")
        self.test_trip_personal = TripPersonalChecklistFactory(
            user=self.test_user, trip=self.test_trip, name="test personal name")
        self.payload = {
            "name": "New personal equipment",
            "checklist": "Sth, sth new, sth other",
        }

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 2)
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)

    def test_add_trip_personal_checklist_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add trip personal checklist
        (user is redirected to login page)."""
        response = self.client.get(reverse("trip:add-trip-personal-checklist",
                                           args=[str(self.trip_personal.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_trip_personal_checklist_result_200_if_logged_in(self):
        """Test if add_trip_personal page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-personal-checklist", args=[str(self.trip.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_trip_personal_checklist_correct_template_if_logged_in(self):
        """Test if add_trip_personal page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:add-trip-personal-checklist",
                                               args=[str(self.trip.id)]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_add_trip_personal_checklist_form_initial_values_set_context_data(self):
        """Test if add_trip_personal page displays correct context data."""
        trip_names = TripPersonalChecklist.objects.filter(
            user=self.user).values_list("name", flat=True)
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-personal-checklist", args=[str(self.trip.id)]))
        self.assertEqual(response_get.context["page"], "add-trip-personal-checklist")
        self.assertQuerysetEqual(response_get.context["trip_names"], trip_names)
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_checklist"],
                              TripPersonalChecklistForm)

    def test_add_trip_personal_checklist_form_initial_values_set_form_data(self):
        """Test if add_trip_personal page displays correct form data."""
        trip_fields = ["name", "checklist"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-personal-checklist", args=[str(self.trip.id)]))
        for field in trip_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_trip_personal_checklist_success_and_redirect(self):
        """Test if creating a trip personal checklist successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-personal-checklist", args=[str(self.trip.id)]),
            data=self.payload, follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.",
                      str(messages[0]))
        self.assertInHTML(self.payload["name"],
                          response_post.content.decode())
        self.assertEqual(TripPersonalChecklist.objects.count(), 3)
        self.assertTrue(TripPersonalChecklist.objects.filter(
            user=self.user, checklist=self.payload["checklist"]).exists())

    def test_add_trip_personal_checklist_successful_with_correct_user(self):
        """Test if creating a trip personal checklist successfully has correct user."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-personal-checklist", args=[str(self.trip.id)]),
            self.payload, follow=True)

        checklist = TripPersonalChecklist.objects.get(
            checklist=self.payload["checklist"])
        self.assertEqual(checklist.user, self.user)

    def test_add_trip_personal_checklist_successful_with_correct_trip(self):
        """Test if creating a trip personal successfully has correct
        trip as foreign key."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-personal-checklist", args=[str(self.trip.id)]),
            self.payload, follow=True)

        checklist = TripPersonalChecklist.objects.get(
            checklist=self.payload["checklist"])
        self.assertQuerysetEqual(checklist.trip, self.trip)
        self.assertNotEqual(checklist.trip, self.test_trip)

    @parameterized.expand(
        [
            ("Empty field: name", {"checklist": "One more thing"},
             "To pole jest wymagane."),
            ("Not unique field: name", {"name": "setup personal name"},
             "Istnieje już lista o podanej nazwie w bazie danych."),
        ]
    )
    def test_add_trip_personal_checklist_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a trip personal checklist is not successful if data
        is incorrect."""
        trip_names = TripPersonalChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_personal.id).values_list("name", flat=True)
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-personal-checklist", args=[str(self.trip.id)]),
            payload, trip_names=trip_names)
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_trip_personal_checklist_302_redirect_if_unauthorized(self):
        """Test if edit_trip_personal page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:edit-trip-personal-checklist",
                    args=[self.trip_personal.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_trip_personal_checklist_200_if_logged_in(self):
        """Test if edit_trip_personal page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-personal-checklist",
                    args=[self.trip_personal.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_trip_personal_checklist_correct_template_if_logged_in(self):
        """Test if edit_trip_personal page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-personal-checklist",
                    args=[self.trip_personal.id]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_edit_trip_personal_checklist_form_initial_values_set_context_data(self):
        """Test if edit_trip_personal page displays correct context data."""
        trip_names = TripPersonalChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_personal.id).values_list("name", flat=True)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]))
        self.assertEqual(response_get.context["page"], "edit-trip-personal-checklist")
        self.assertQuerysetEqual(response_get.context["trip_checklist"],
                                 self.trip_personal)
        self.assertQuerysetEqual(response_get.context["trip_names"], trip_names)
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_checklist"],
                              TripPersonalChecklistForm)

    def test_edit_trip_personal_checklist_form_initial_values_set(self):
        """Test if edit_trip_personal page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]))
        self.assertIn(self.trip_personal.name, response_get.content.decode())
        self.assertIn(self.trip_personal.checklist, response_get.content.decode())

    def test_edit_trip_personal_checklist_success_and_redirect(self):
        """Test if updating a trip_personal_checklist is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        trip_names = TripPersonalChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_personal.id).values_list("name", flat=True)
        self.assertNotEqual(self.trip_personal.checklist,
                            self.payload["checklist"])
        self.assertNotEqual(self.trip_personal.name, self.payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:edit-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]),
            data=self.payload,
            instance=self.trip_personal,
            trip_names=trip_names,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.", str(messages[0]))
        self.trip_personal.refresh_from_db()
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)
        self.assertEqual(self.trip_personal.name, self.payload["name"])
        self.assertEqual(self.trip_personal.checklist, self.payload["checklist"])

    def test_edit_trip_personal_checklist_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        trip_names = TripPersonalChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_personal.id).values_list("name", flat=True)
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "New sth",
            "checklist": "TV, radio, earphones",
        }
        response_patch = self.client.patch(
            reverse("trip:edit-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]),
            data=payload,
            instance=self.trip_personal,
            trip_names=trip_names,
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:edit-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]),
            data=self.payload,
            instance=self.trip_personal,
            trip_names=trip_names,
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:edit-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_trip_personal_checklist_logout_if_security_breach(self):
        """Editing trip_basic of another user is unsuccessful and triggers logout."""
        trip_names = TripPersonalChecklist.objects.filter(
            user=self.user).exclude(
            id=self.trip_personal.id).values_list("name", flat=True)
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_trip_personal.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "checklist": "SECURITY BREACH",
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("trip:edit-trip-personal-checklist",
                    args=[str(self.test_trip_personal.id)]),
            data=payload,
            trip_names=trip_names,
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)

        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)
        self.assertNotIn(self.test_trip_personal.name, payload["name"])

    def test_delete_trip_personal_checklist_302_redirect_if_unauthorized(self):
        """Test if delete_trip_basic page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:delete-trip-personal-checklist",
                    args=[self.trip_personal.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_trip_personal_checklist_200_if_logged_in(self):
        """Test if delete_trip_personal page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-personal-checklist",
                    args=[self.trip_personal.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_trip_personal_checklist_correct_template_if_logged_in(self):
        """Test if delete_trip_personal page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-personal-checklist",
                    args=[self.trip_personal.id]))
        self.assertTemplateUsed(response_get,
                                "trip/trip_delete_form.html")

    def test_delete_trip_personal_checklist_initial_values_set_context_data(self):
        """Test if delete_trip_personal page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:delete-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]))
        self.assertEqual(response_get.context["page"], "delete-trip-personal-checklist")
        self.assertQuerysetEqual(response_get.context["trip_checklist"],
                                 self.trip_personal)
        self.assertEqual(str(response_get.context["trip_id"]), str(self.trip.id))

    def test_delete_trip_personal_checklist_successful_and_redirect(self):
        """Deleting trip personal checklist is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)
        self.client.force_login(self.user)

        response_delete = self.client.post(
            reverse("trip:delete-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]),
            content_type="text/html", follow=True,)
        self.assertRedirects(
            response_delete,
            reverse("trip:single-trip", args=[self.trip.id]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto dodatkowe elementy podróży.",
                      str(messages[0]))

        response = self.client.get(
            reverse("trip:single-trip", args=[str(self.trip.id)]))
        self.assertEqual(TripPersonalChecklist.objects.count(), 1)
        self.assertNotIn(self.trip_personal.name, response.content.decode())
        self.assertNotIn(self.test_trip_personal.name, response.content.decode())

    def test_delete_trip_personal_checklist_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("trip:delete-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:delete-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:delete-trip-personal-checklist",
                    args=[str(self.trip_personal.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_trip_personal_checklist_logout_if_security_breach(self):
        """Deleting trip personal checklist of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_trip_personal.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("trip:delete-trip-personal-checklist",
                    args=[str(self.test_trip_personal.id)]),
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
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)


class TripAdditionalInfoViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456"
        )
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass456"
        )
        self.trip = TripFactory(user=self.user, name="setup name")
        self.test_trip = TripFactory(user=self.test_user, name="test name")
        self.trip_additional = TripAdditionalInfoFactory(
            user=self.user, trip=self.trip, name="setup additional info name")
        self.test_trip_additional = TripAdditionalInfoFactory(
            user=self.test_user, trip=self.test_trip, name="test additional info name")
        self.payload = {
            "name": "New additional info",
            "info": "Video + photos on demand",
            "notes": "New info about trip",
        }

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 2)
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)

    def test_add_trip_additional_info_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add trip additional info
        (user is redirected to login page)."""
        response = self.client.get(reverse("trip:add-trip-additional",
                                           args=[str(self.trip_additional.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_trip_additional_info_result_200_if_logged_in(self):
        """Test if add_trip_additional page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-additional", args=[str(self.trip.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_trip_additional_info_correct_template_if_logged_in(self):
        """Test if add_trip_additional page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:add-trip-additional",
                                               args=[str(self.trip.id)]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_add_trip_additional_info_form_initial_values_set_context_data(self):
        """Test if add_trip_additional page displays correct context data."""
        trip_names = TripAdditionalInfo.objects.filter(
            user=self.user).values_list("name", flat=True)
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-additional", args=[str(self.trip.id)]))
        self.assertEqual(response_get.context["page"], "add-trip-additional")
        self.assertQuerysetEqual(response_get.context["trip_names"], trip_names)
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_additional"],
                              TripAdditionalInfoForm)

    def test_add_trip_additional_info_form_initial_values_set_form_data(self):
        """Test if add_trip_additional page displays correct form data."""
        trip_fields = ["name", "info", "notes"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-additional", args=[str(self.trip.id)]))
        for field in trip_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_trip_additional_info_success_and_redirect(self):
        """Test if creating a trip additional info successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-additional", args=[str(self.trip.id)]),
            data=self.payload, follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.",
                      str(messages[0]))
        self.assertInHTML(self.payload["name"],
                          response_post.content.decode())
        self.assertEqual(TripAdditionalInfo.objects.count(), 3)
        self.assertTrue(TripAdditionalInfo.objects.filter(
            user=self.user, info=self.payload["info"]).exists())

    def test_add_trip_additional_info_successful_with_correct_user(self):
        """Test if creating a trip additional info successfully has correct user."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-additional", args=[str(self.trip.id)]),
            self.payload, follow=True)

        additional_info = TripAdditionalInfo.objects.get(info=self.payload["info"])
        self.assertEqual(additional_info.user, self.user)

    def test_add_trip_additional_info_successful_with_correct_trip(self):
        """Test if creating a trip additional info successfully has correct
        trip as foreign key."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-additional", args=[str(self.trip.id)]),
            self.payload, follow=True)

        additional_info = TripAdditionalInfo.objects.get(
            info=self.payload["info"])
        self.assertQuerysetEqual(additional_info.trip, self.trip)
        self.assertNotEqual(additional_info.trip, self.test_trip)

    @parameterized.expand(
        [
            ("Empty field: name", {"info": "One more thing"},
             "To pole jest wymagane."),
            ("Not unique field: name", {"name": "setup additional info name"},
             "Istnieje już element o podanej nazwie w bazie danych."),
        ]
    )
    def test_add_trip_additional_info_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a trip additional info is not successful if data is incorrect."""
        trip_names = TripAdditionalInfo.objects.filter(
            user=self.user).exclude(
            id=self.trip_additional.id).values_list("name", flat=True)
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-additional", args=[str(self.trip.id)]),
            payload, trip_names=trip_names)
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_trip_additional_info_302_redirect_if_unauthorized(self):
        """Test if edit_trip_additional page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:edit-trip-additional",
                    args=[self.trip_additional.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_trip_additional_info_200_if_logged_in(self):
        """Test if edit_trip_additional page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-additional",
                    args=[self.trip_additional.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_trip_additional_info_correct_template_if_logged_in(self):
        """Test if edit_trip_additional page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-additional",
                    args=[self.trip_additional.id]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_edit_trip_additional_info_form_initial_values_set_context_data(self):
        """Test if edit_trip_additional page displays correct context data."""
        trip_names = TripAdditionalInfo.objects.filter(
            user=self.user).exclude(
            id=self.trip_additional.id).values_list("name", flat=True)
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-additional",
                    args=[str(self.trip_additional.id)]))
        self.assertEqual(response_get.context["page"], "edit-trip-additional")
        self.assertQuerysetEqual(response_get.context["trip_additional"],
                                 self.trip_additional)
        self.assertQuerysetEqual(response_get.context["trip_names"], trip_names)
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_additional"],
                              TripAdditionalInfoForm)

    def test_edit_trip_additional_info_form_initial_values_set(self):
        """Test if edit_trip_additional page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-additional",
                    args=[str(self.trip_additional.id)]))
        self.assertIn(self.trip_additional.name, response_get.content.decode())
        self.assertIn(self.trip_additional.info, response_get.content.decode())

    def test_edit_trip_additional_info_success_and_redirect(self):
        """Test if updating a trip additional info is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        trip_names = TripAdditionalInfo.objects.filter(
            user=self.user).exclude(
            id=self.trip_additional.id).values_list("name", flat=True)
        self.assertNotEqual(self.trip_additional.info, self.payload["info"])
        self.assertNotEqual(self.trip_additional.name, self.payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:edit-trip-additional",
                    args=[str(self.trip_additional.id)]),
            data=self.payload,
            instance=self.trip_additional,
            trip_names=trip_names,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.", str(messages[0]))
        self.trip_additional.refresh_from_db()
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)
        self.assertEqual(self.trip_additional.name, self.payload["name"])
        self.assertEqual(self.trip_additional.info, self.payload["info"])

    def test_edit_trip_additional_info_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        trip_names = TripAdditionalInfo.objects.filter(
            user=self.user).exclude(
            id=self.trip_additional.id).values_list("name", flat=True)
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "New sth",
            "info": "TV, radio, earphones",
            "notes": "ABCD",
        }
        response_patch = self.client.patch(
            reverse("trip:edit-trip-additional",
                    args=[str(self.trip_additional.id)]),
            data=payload,
            instance=self.trip_additional,
            trip_names=trip_names,
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:edit-trip-additional",
                    args=[str(self.trip_additional.id)]),
            data=self.payload,
            instance=self.trip_additional,
            trip_names=trip_names,
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:edit-trip-additional",
                    args=[str(self.trip_additional.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_trip_additional_info_logout_if_security_breach(self):
        """Editing trip additional info of another user is unsuccessful and
        triggers logout."""
        trip_names = TripAdditionalInfo.objects.filter(
            user=self.user).exclude(
            id=self.trip_additional.id).values_list("name", flat=True)
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_trip_additional.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "info": "SECURITY BREACH",
            "notes": "ABCD"
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("trip:edit-trip-additional",
                    args=[str(self.test_trip_additional.id)]),
            data=payload,
            trip_names=trip_names,
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)

        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)
        self.assertNotIn(self.test_trip_additional.name, payload["name"])

    def test_delete_trip_additional_info_302_redirect_if_unauthorized(self):
        """Test if delete_trip_basic page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:delete-trip-additional",
                    args=[self.trip_additional.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_trip_additional_info_200_if_logged_in(self):
        """Test if delete_trip_additional page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-additional",
                    args=[self.trip_additional.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_trip_additional_info_correct_template_if_logged_in(self):
        """Test if delete_trip_personal page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-additional",
                    args=[self.trip_additional.id]))
        self.assertTemplateUsed(response_get,
                                "trip/trip_delete_form.html")

    def test_delete_trip_additional_info_initial_values_set_context_data(self):
        """Test if delete_trip_additional page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:delete-trip-additional",
                    args=[str(self.trip_additional.id)]))
        self.assertEqual(response_get.context["page"], "delete-trip-additional")
        self.assertQuerysetEqual(response_get.context["trip_additional"],
                                 self.trip_additional)
        self.assertEqual(str(response_get.context["trip_id"]), str(self.trip.id))

    def test_delete_trip_additional_info_successful_and_redirect(self):
        """Deleting trip additional info is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)
        self.client.force_login(self.user)

        response_delete = self.client.post(
            reverse("trip:delete-trip-additional",
                    args=[str(self.trip_additional.id)]),
            content_type="text/html", follow=True,)
        self.assertRedirects(
            response_delete,
            reverse("trip:single-trip", args=[self.trip.id]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto dodatkowe informacje o podróży.",
                      str(messages[0]))

        response = self.client.get(
            reverse("trip:single-trip", args=[str(self.trip.id)]))
        self.assertEqual(TripAdditionalInfo.objects.count(), 1)
        self.assertNotIn(self.trip_additional.name, response.content.decode())
        self.assertNotIn(self.test_trip_additional.name, response.content.decode())

    def test_delete_trip_additional_info_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("trip:delete-trip-additional",
                    args=[str(self.trip_additional.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:delete-trip-additional",
                    args=[str(self.trip_additional.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:delete-trip-additional",
                    args=[str(self.trip_additional.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_trip_additional_info_logout_if_security_breach(self):
        """Deleting trip additional info of another user is unsuccessful and
        triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_trip_additional.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("trip:delete-trip-additional",
                    args=[str(self.test_trip_additional.id)]),
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
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)


class TripCostViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com", password="testpass456"
        )
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass456"
        )
        self.trip = TripFactory(user=self.user, name="setup name")
        self.test_trip = TripFactory(user=self.test_user, name="test name")
        self.trip_cost = TripCostFactory(
            user=self.user, trip=self.trip, name="setup cost", currency="PLN")
        self.test_trip_cost = TripCostFactory(
            user=self.test_user, trip=self.test_trip, name="test cost", currency="USD")
        self.payload = {
            "name": "New cost",
            "cost_group": CostGroup.FUEL,
            "cost_paid": 134,
            "currency": "CHF",
            "exchange_rate": 5.2000,
            "notes": "ordinary cost",
        }

    def test_all_setup_instances_created(self):
        """Test if all instances has been created in setUp."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 2)
        self.assertEqual(TripCost.objects.count(), 2)

    def test_add_trip_cost_302_redirect_if_unauthorized(self):
        """Test if unauthenticated user cannot add trip cost
        (user is redirected to login page)."""
        response = self.client.get(reverse("trip:add-trip-cost",
                                           args=[str(self.trip_cost.id)]))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_add_trip_cost_result_200_if_logged_in(self):
        """Test if add_trip_cost page returns status code 200
        for authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-cost", args=[str(self.trip.id)]))
        self.assertEqual(response_get.status_code, 200)

    def test_add_trip_cost_correct_template_if_logged_in(self):
        """Test if add_trip_cost page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(reverse("trip:add-trip-cost",
                                               args=[str(self.trip.id)]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_add_trip_cost_form_initial_values_set_context_data(self):
        """Test if add_trip_cost page displays correct context data."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-cost", args=[str(self.trip.id)]))
        self.assertEqual(response_get.context["page"], "add-trip-cost")
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_cost"], TripCostForm)

    def test_add_trip_cost_form_initial_values_set_form_data(self):
        """Test if add_trip_cost page displays correct form data."""
        trip_fields = ["name", "cost_group", "cost_paid", "cost_paid",
                       "exchange_rate", "notes"]
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:add-trip-cost", args=[str(self.trip.id)]))
        for field in trip_fields:
            self.assertIn(field, response_get.content.decode())
        self.assertIn("Zapisz", response_get.content.decode())   # input type="submit"

    def test_add_trip_cost_success_and_redirect(self):
        """Test if creating a trip cost successful (status code 200) and
        redirecting is successful (status code 302)."""
        self.assertEqual(TripCost.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-cost", args=[str(self.trip.id)]),
            data=self.payload, follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono koszty podroży.",
                      str(messages[0]))
        self.assertInHTML(self.payload["name"],
                          response_post.content.decode())
        self.assertEqual(TripCost.objects.count(), 3)
        self.assertTrue(TripCost.objects.filter(
            user=self.user, currency=self.payload["currency"]).exists())

    def test_add_trip_cost_successful_with_correct_user(self):
        """Test if creating a trip cost successfully has correct user."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-cost", args=[str(self.trip.id)]),
            self.payload, follow=True)

        cost = TripCost.objects.get(currency=self.payload["currency"])
        self.assertEqual(cost.user, self.user)

    def test_add_trip_cost_successful_with_correct_trip(self):
        """Test if creating a trip cost successfully has correct
        trip as foreign key."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("trip:add-trip-cost", args=[str(self.trip.id)]),
            self.payload, follow=True)

        cost = TripCost.objects.get(currency=self.payload["currency"])
        self.assertQuerysetEqual(cost.trip, self.trip)
        self.assertNotEqual(cost.trip, self.test_trip)

    @parameterized.expand(
        [
            ("Empty field: name",
             {"cost_group": "Bilety", "cost_paid": 222, "exchange_rate": 1.5},
             "To pole jest wymagane."),
            ("Empty field: cost_group",
             {"name": "Bilety", "cost_paid": 222, "exchange_rate": 1.5},
             "To pole jest wymagane."),
            ("Empty field: cost_paid",
             {"cost_group": "Bilety", "name": "cost abc", "exchange_rate": 1.5},
             "To pole jest wymagane."),
            ("Empty field: exchange_rate",
             {"cost_group": "Bilety", "name": "cost abc", "cost_paid": 150},
             "To pole jest wymagane."),
            ("Incorrect field: exchange_rate (negative values are not allowed)",
             {"name": "new cost", "cost_group": "Bilety", "cost_paid": 150,
              "exchange_rate": -1.5},
             "Wartość kursu walutowego nie może być ujemna."),
        ]
    )
    def test_add_trip_cost_unsuccessful_with_incorrect_data(
            self,
            name: str,
            payload: dict,
            field_message: str,
    ):
        """Test creating a trip cost is not successful if data is incorrect."""
        self.assertEqual(TripCost.objects.count(), 2)
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:add-trip-cost", args=[str(self.trip.id)]), payload)
        self.assertEqual(TripCost.objects.count(), 2)
        self.assertEqual(response_post.status_code, 200)  # messages.error used instead of status_code 400
        self.assertIn("Wystąpił błąd podczas zapisu formularza. "
                      "Sprawdź poprawność danych.",
                      response_post.content.decode())
        self.assertIn(field_message, response_post.content.decode())

    def test_edit_trip_cost_302_redirect_if_unauthorized(self):
        """Test if edit_trip_cost page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:edit-trip-cost", args=[self.trip_cost.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_edit_trip_cost_200_if_logged_in(self):
        """Test if edit_trip_cost page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-cost", args=[self.trip_cost.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_edit_trip_cost_correct_template_if_logged_in(self):
        """Test if edit_trip_cost page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:edit-trip-cost", args=[self.trip_cost.id]))
        self.assertTemplateUsed(response_get, "trip/trip_form.html")

    def test_edit_trip_cost_form_initial_values_set_context_data(self):
        """Test if edit_trip_cost page displays correct context data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-cost", args=[str(self.trip_cost.id)]))
        self.assertEqual(response_get.context["page"], "edit-trip-cost")
        self.assertQuerysetEqual(response_get.context["trip_cost"],
                                 self.trip_cost)
        self.assertQuerysetEqual(response_get.context["trip"], self.trip)
        self.assertIsInstance(response_get.context["form_cost"], TripCostForm)

    def test_edit_trip_cost_form_initial_values_set(self):
        """Test if edit_trip_cost page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:edit-trip-cost", args=[str(self.trip_cost.id)]))
        self.assertIn(self.trip_cost.name, response_get.content.decode())
        self.assertIn(self.trip_cost.currency, response_get.content.decode())

    def test_edit_trip_cost_success_and_redirect(self):
        """Test if updating a trip cost is successful (status code 200)
        and redirecting is successful (status code 302)."""
        # Note: because of POST request method used in update view,
        # to partially update instance all fields must be provided.
        # PATCH method not allowed.
        self.assertNotEqual(self.trip_cost.currency, self.payload["currency"])
        self.assertNotEqual(self.trip_cost.name, self.payload["name"])
        self.client.force_login(self.user)

        response_post = self.client.post(
            reverse("trip:edit-trip-cost", args=[str(self.trip_cost.id)]),
            data=self.payload,
            instance=self.trip_cost,
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("trip:single-trip", args=[str(self.trip.id)]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)
        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Uzupełniono podróż.", str(messages[0]))
        self.trip_cost.refresh_from_db()
        self.assertEqual(TripCost.objects.count(), 2)
        self.assertEqual(self.trip_cost.name, self.payload["name"])
        self.assertEqual(self.trip_cost.currency, self.payload["currency"])

    def test_edit_trip_v_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        payload = {
            "name": "New cost",
            "cost_group": self.trip_cost.cost_group,
            "cost_paid": self.trip_cost.cost_paid,
            "currency": "JPY",
            "exchange_rate": self.trip_cost.exchange_rate,
            "notes": self.trip_cost.notes
        }
        response_patch = self.client.patch(
            reverse("trip:edit-trip-cost", args=[str(self.trip_cost.id)]),
            data=payload,
            instance=self.trip_cost,
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:edit-trip-cost", args=[str(self.trip_cost.id)]),
            data=self.payload,
            instance=self.trip_cost,
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:edit-trip-cost", args=[str(self.trip_cost.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda zapisu formularza.",
                          response_delete.content.decode())

    def test_edit_trip_cost_logout_if_security_breach(self):
        """Editing trip cost of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)  # login by user, not test_user
        self.assertNotEqual(self.user, self.test_trip_cost.user)
        self.assertIn("_auth_user_id", self.client.session)

        payload = {
            "name": "SECURITY BREACH",
            "notes": "SECURITY BREACH",
        }

        # Attempt to change data that belonged to test_user by user
        response_post = self.client.post(
            reverse("trip:edit-trip-cost",
                    args=[str(self.test_trip_cost.id)]),
            data=payload,
            content_type="text/html",
            follow=True)
        self.assertRedirects(
            response_post,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)

        messages = list(response_post.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Nie masz uprawnień do modyfikacji tych danych.",
                      str(messages[0]))

        response_redirect = self.client.get(reverse("login"))
        self.assertNotIn(str(self.user),
                         response_redirect.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(TripCost.objects.count(), 2)
        self.assertNotIn(self.test_trip_cost.name, payload["name"])

    def test_delete_trip_cost_302_redirect_if_unauthorized(self):
        """Test if delete_trip_basic page is unavailable for unauthorized users."""
        response = self.client.get(
            reverse("trip:delete-trip-cost", args=[self.trip_cost.id]))
        self.assertNotIn("johndoe123", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_delete_trip_cost_200_if_logged_in(self):
        """Test if delete_trip_cost page returns status code 200 for
        authorized user."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-cost", args=[self.trip_cost.id]))
        self.assertEqual(response_get.status_code, 200)

    def test_delete_trip_cost_correct_template_if_logged_in(self):
        """Test if delete_trip_personal page uses correct template."""
        self.client.login(username="johndoe123", password="testpass456")
        response_get = self.client.get(
            reverse("trip:delete-trip-cost", args=[self.trip_cost.id]))
        self.assertTemplateUsed(response_get,
                                "trip/trip_delete_form.html")

    def test_delete_trip_cost_initial_values_set_context_data(self):
        """Test if delete_trip_cost page displays correct initial data."""
        self.client.force_login(self.user)
        response_get = self.client.get(
            reverse("trip:delete-trip-cost", args=[str(self.trip_cost.id)]))
        self.assertEqual(response_get.context["page"], "delete-trip-cost")
        self.assertQuerysetEqual(response_get.context["trip_cost"], self.trip_cost)
        self.assertEqual(str(response_get.context["trip_id"]), str(self.trip.id))

    def test_delete_trip_cost_successful_and_redirect(self):
        """Deleting trip cost is successful (status code 200) and redirect
        is successful (status code 302)."""
        self.assertEqual(TripCost.objects.count(), 2)
        self.client.force_login(self.user)

        response_delete = self.client.post(
            reverse("trip:delete-trip-cost", args=[str(self.trip_cost.id)]),
            content_type="text/html", follow=True,)
        self.assertRedirects(
            response_delete,
            reverse("trip:single-trip", args=[self.trip.id]),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        messages = list(response_delete.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Usunięto koszt podróży.",
                      str(messages[0]))

        response = self.client.get(
            reverse("trip:single-trip", args=[str(self.trip.id)]))
        self.assertEqual(TripCost.objects.count(), 1)
        self.assertNotIn(self.trip_cost.name, response.content.decode())
        self.assertNotIn(self.test_trip_cost.name, response.content.decode())

    def test_delete_trip_cost_405_with_not_allowed_method(self):
        """Test if response has status code 405 if method is not allowed.
        Allowed methods: "POST", "GET"."""
        self.client.force_login(self.user)

        # PATCH
        response_patch = self.client.patch(
            reverse("trip:delete-trip-cost", args=[str(self.trip_cost.id)]),
            follow=False)
        self.assertEqual(response_patch.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_patch.content.decode())

        # PUT
        response_put = self.client.put(
            reverse("trip:delete-trip-cost", args=[str(self.trip_cost.id)]),
            follow=False)
        self.assertEqual(response_put.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_put.content.decode())

        # DELETE
        response_delete = self.client.delete(
            reverse("trip:delete-trip-cost", args=[str(self.trip_cost.id)]),
            follow=False)
        self.assertEqual(response_delete.status_code, 405)
        self.assertInHTML("Niepoprawna metoda.",
                          response_delete.content.decode())

    def test_delete_trip_cost_logout_if_security_breach(self):
        """Deleting trip cost of another user is unsuccessful and triggers logout."""
        self.client.force_login(self.user)
        self.assertEqual(TripCost.objects.count(), 2)
        self.assertNotEqual(self.user, self.test_trip_cost.user)
        self.assertIn("_auth_user_id", self.client.session)

        response_delete = self.client.post(
            reverse("trip:delete-trip-cost", args=[str(self.test_trip_cost.id)]),
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
        self.assertEqual(TripCost.objects.count(), 2)
