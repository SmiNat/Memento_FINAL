import datetime
import logging
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.db import transaction
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from parameterized import parameterized

from trip.models import (Trip, TripReport, TripCost, TripAdditionalInfo,
                         TripPersonalChecklist, TripAdvancedChecklist,
                         TripBasicChecklist)
from trip.factories import (TripFactory, TripReportFactory, TripBasicFactory,
                            TripAdvancedFactory, TripCostFactory,
                            TripAdditionalInfoFactory, TripPersonalChecklistFactory)

User = get_user_model()
logger = logging.getLogger("test")


class TripModelTests(TestCase):
    """Test model Trip."""

    def setUp(self):
        self.trip = TripFactory()
        self.user = self.trip.user
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "name": "Nazwa podróży",
            "type": "Rodzaj podróży",
            "destination": "Miejsce podróży",
            "start_date": "Rozpoczęcie wyjazdu",
            "end_date": "Zakończenie wyjazdu",
            "transport": "Środki transportu",
            "estimated_cost": "Szacunkowy koszt podróży",
            "participants_number": "Liczba osób na wyjeździe",
            "participants": "Towarzysze podróży",
            "reservations": "Informacje o rezerwacjach",
            "notes": "Uwagi",
            "access_granted": "Dostęp do danych",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }

    def test_create_trip_successful(self):
        """Test if creating a trip with valid data is successful."""
        trips = Trip.objects.all()
        self.assertEqual(trips.count(), 1)
        self.assertTrue(trips[0].user, self.user)
        self.assertTrue(trips[0].name, "Test name")

    def test_trip_id_is_uuid(self):
        """Test if id is represented as uuid."""
        trip = self.trip
        uuid_value = trip.id
        self.assertTrue(isinstance(uuid.UUID(uuid_value), uuid.UUID))

    def test_unique_constraint_for_trip_name(self):
        """Test if user can only have trips with unique names."""
        Trip.objects.create(user=self.user, name="Some trip")
        self.assertEqual(Trip.objects.count(), 2)
        with self.assertRaises(IntegrityError):
            Trip.objects.create(user=self.user, name="Some trip")

    def test_integrity_error_for_empty_trip_name(self):
        """Test if model without required fields cannot be saved in database."""
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Trip.objects.create(
                  user=self.user,
                )

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.trip), "Test name")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        all_fields = list(self.field_names.values())
        all_values = list(self.trip.__dict__.values())
        for field, value in self.trip:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                self.assertEqual(value.replace(
                    ",", " ").replace(
                        "[", "").replace(
                            "]", "").replace(
                                "'", ""), str(all_values[number][0]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            else:
                self.assertEqual(value, str(all_values[number]))

    @parameterized.expand(
        [
            ("both dates are set",
             datetime.date(2020, 10, 10), datetime.date(2020, 10, 15), 6),
            ("start and end date has the same value",
             datetime.date(2020, 10, 10), datetime.date(2020, 10, 10), 1),
            ("only start date is set", datetime.date(2020, 10, 10), None, None),
            ("only end date is set", None, datetime.date(2020, 10, 10), None)
        ]
    )
    def test_trip_days_method(self, name, start_date, end_date, result):
        """Test if trip_days method returns correct number od days
        or string equal to None if dates are not set."""
        trip = Trip.objects.create(
            user=self.user,
            name="New trip",
            start_date=start_date,
            end_date=end_date,
        )
        self.assertEqual(trip.trip_days(), result)

    def test_get_all_costs_pln_method(self):
        """Test that get_all_costs_pln method returns correct sum of all costs in PLN."""
        cost1 = TripCost.objects.create(
            user=self.user, trip=self.trip, name="cost1",
            cost_group=["Bilety"], cost_paid=100
        )
        cost2 = TripCost.objects.create(
            user=self.user, trip=self.trip, name="cost2",
            cost_group=["Bilety"], cost_paid=200
        )
        cost3 = TripCost.objects.create(
            user=self.user, trip=self.trip, name="cost3",
            cost_group=["Bilety"], cost_paid=300, currency="USD", exchange_rate=3.5000
        )
        trip = Trip.objects.get(user=self.user)
        sum_of_costs = (cost1.cost_paid * cost1.exchange_rate
                        + cost2.cost_paid * cost2.exchange_rate
                        + cost3.cost_paid * cost3.exchange_rate)
        self.assertEqual(trip.get_all_costs_pln(), sum_of_costs)

    def test_get_all_costs_pln_method_return_zero(self):
        """Test that get_all_costs_pln method returns zero
        if no costs are associated to the trip."""
        trip = Trip.objects.get(user=self.user)
        self.assertEqual(trip.get_all_costs_pln(), None)

    def test_all_choices(self):
        """Test if all_choices method returns TextChoices class names
        and chosen values."""
        trip = self.trip
        self.assertEqual(len(trip.all_choices()[0]), 1)
        self.assertEqual(trip.type, trip.all_choices()[1][0])

    def test_validate_choices(self):
        """Test if save method validates choices before saving instance in database."""
        trip = self.trip
        # test correct trip type save method
        trip.type = ["Wyjazd nad morze"]
        trip.save()
        self.assertEqual(trip.type, ["Wyjazd nad morze"])
        # test incorrect trip type save method
        trip.type = ["Inny typ podróży"]
        with self.assertRaises(ValidationError):
            trip.save()


class TripReportModelTests(TestCase):
    """Test model TripReport."""

    def setUp(self):
        self.trip = TripFactory()
        self.user = self.trip.user
        self.trip_report = TripReportFactory(user=self.user, trip=self.trip)
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "trip": "Wyjazd",
            "start_date": "Rozpoczęcie relacji",
            "end_date": "Zakończenie relacji",
            "description": "Opis",
            "notes": "Uwagi",
            "facebook": "Facebook link",
            "youtube": "Youtube link",
            "instagram": "Instagram link",
            "pinterest": "Pinterest link",
            "link": "Link do relacji",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_trip_report_successful(self):
        """Test if creating a trip report with valid data is successful."""
        trip = TripReport.objects.all()
        self.assertEqual(trip.count(), 1)
        self.assertTrue(trip[0].user, self.user)
        self.assertTrue(trip[0].trip, self.trip)
        self.assertTrue(trip[0].youtube, "https://www.youtube.com")

    def test_trip_report_id_is_uuid(self):
        """Test if id is represented as uuid."""
        trip = self.trip_report
        uuid_value = trip.id
        self.assertTrue(isinstance(uuid.UUID(uuid_value), uuid.UUID))


class TripBasicModelTests(TestCase):
    """Test model TripBasicChecklist."""

    def setUp(self):
        self.trip = TripFactory()
        self.user = self.trip.user
        self.trip_basic = TripBasicFactory(user=self.user, trip=self.trip)
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "trip": "Wyjazd",
            "name": "Nazwa",
            "wallet": "Portfel",
            "keys": "Klucze",
            "cosmetics": "Kosmetyki",
            "electronics": "Elektronika",
            "useful_stuff": "Użyteczne rzeczy",
            "basic_drugs": "Podstawowe leki",
            "additional_drugs": "Dodatkowe leki",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_trip_basic_successful(self):
        """Test if creating a trip basic checklist with valid data is successful."""
        trip = TripBasicChecklist.objects.all()
        self.assertEqual(trip.count(), 1)
        self.assertTrue(trip[0].user, self.user)
        self.assertTrue(trip[0].trip, self.trip)
        self.assertTrue(trip[0].electronics, TripBasicFactory.electronics)

    def test_trip_basic_id_is_uuid(self):
        """Test if id is represented as uuid."""
        trip = self.trip_basic
        uuid_value = trip.id
        self.assertTrue(isinstance(uuid.UUID(uuid_value), uuid.UUID))

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        all_fields = list(self.field_names.values())
        all_values = list(self.trip_basic.__dict__.values())
        for field, value in self.trip_basic:
            # print("🖥️", field, value)
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                if len(all_values[number]) > 1:
                    self.assertEqual(
                        value.replace(
                            ",", "").replace(
                                "[", "").replace(
                                    "]", "").replace(
                                        "'", ""),
                        " ".join(str(i) for i in all_values[number])
                    )
                else:
                    self.assertEqual(value.replace(
                        ",", " ").replace(
                            "[", "").replace(
                                "]", "").replace(
                                    "'", "").split(), (all_values[number]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            else:
                self.assertEqual(value, str(all_values[number]))

    def test_unique_constraint_for_trip_basic_name(self):
        """Test if user can only have trips with unique basic names
        (or no basic name at all)."""
        TripBasicChecklist.objects.create(
            user=self.user, trip=self.trip, name="Some trip"
        )
        self.assertEqual(TripBasicChecklist.objects.count(), 2)
        with self.assertRaises(IntegrityError):
            TripBasicChecklist.objects.create(
                user=self.user, trip=self.trip, name="Some trip"
            )

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        if TripBasicFactory.name:
            self.assertEqual(
                str(self.trip_basic),
                "%s - %s" % (self.trip, TripBasicFactory.name)
            )
        else:
            self.assertEqual(str(self.trip_basic), f"{self.trip} - (basic)")

    def test_all_choices(self):
        """Test if all_choices method returns TextChoices class names
        and chosen values."""
        trip = self.trip_basic
        self.assertEqual(len(trip.all_choices()[0]), 5)
        self.assertEqual(trip.wallet, trip.all_choices()[1][0])

    def test_validate_choices(self):
        """Test if save method validates choices before saving instance in database."""
        trip = self.trip_basic
        # test correct trip type save method
        trip.wallet = [_("Karty kredytowe"), _("Ubezpieczenie")]
        trip.save()
        self.assertEqual(trip.wallet, [_("Karty kredytowe"), _("Ubezpieczenie")])
        # test incorrect trip type save method
        trip.wallet = [_("Inny element wyposażenia")]
        with self.assertRaises(ValidationError):
            trip.save()

    def test_string_to_list_method(self):
        """Test if basic_drugs_to_list method and additional_drugs_to_list
        converts string to a list  based on comma or semicolon separator."""
        trip = self.trip_basic
        self.assertEqual(trip.basic_drugs_to_list(), ["cynk", "wit. B i żelazo"])
        self.assertEqual(
            trip.additional_drugs_to_list(), ["Wit. C", "magnez", "espumisan"])


class TripAdvancedModelTests(TestCase):
    """Test model TripAdvancedChecklist."""

    def setUp(self):
        self.trip = TripFactory()
        self.user = self.trip.user
        self.trip_advanced = TripAdvancedFactory(user=self.user, trip=self.trip)
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "trip": "Wyjazd",
            "name": "Nazwa",
            "trekking": "Trekking",
            "hiking": "Wspinaczka",
            "cycling": "Rower",
            "camping": "Camping",
            "fishing": "Wędkarstwo",
            "sunbathing": "Plażowanie",
            "business": "Wyjazd służbowy",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_trip_advanced_successful(self):
        """Test if creating a trip advanced checklist with valid data is successful."""
        trip = TripAdvancedChecklist.objects.all()
        self.assertEqual(trip.count(), 1)
        self.assertTrue(trip[0].user, self.user)
        self.assertTrue(trip[0].trip, self.trip)
        self.assertTrue(trip[0].camping, TripAdvancedFactory.camping)

    def test_trip_advanced_id_is_uuid(self):
        """Test if id is represented as uuid."""
        trip = self.trip_advanced
        uuid_value = trip.id
        self.assertTrue(isinstance(uuid.UUID(uuid_value), uuid.UUID))

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        all_fields = list(self.field_names.values())
        all_values = list(self.trip_advanced.__dict__.values())
        for field, value in self.trip_advanced:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                if len(all_values[number]) > 1:
                    self.assertEqual(
                        value.replace(",", "").replace("[", "").replace("]", "").replace("'", ""),
                        " ".join(str(i) for i in all_values[number])
                    )
                else:
                    self.assertEqual(value.replace(
                        ",", " ").replace(
                            "[", "").replace(
                                "]", "").replace(
                                    "'", "").split(), (all_values[number]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            else:
                self.assertEqual(value, str(all_values[number]))

    def test_unique_constraint_for_trip_advanced_name(self):
        """Test if user can only have trips with unique basic names
        (or no basic name at all)."""
        TripAdvancedChecklist.objects.create(
            user=self.user, trip=self.trip, name="Some trip"
        )
        self.assertEqual(TripAdvancedChecklist.objects.count(), 2)
        with self.assertRaises(IntegrityError):
            TripAdvancedChecklist.objects.create(
                user=self.user, trip=self.trip, name="Some trip"
            )

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        if TripAdvancedFactory.name:
            self.assertEqual(
                str(self.trip_advanced),
                "%s - %s" % (self.trip, TripAdvancedFactory.name)
            )
        else:
            self.assertEqual(str(self.trip_advanced), f"{self.trip} - (basic)")

    def test_all_choices(self):
        """Test if all_choices method returns TextChoices class names
        and chosen values."""
        trip = self.trip_advanced
        self.assertEqual(len(trip.all_choices()[0]), 7)
        self.assertEqual(trip.trekking, trip.all_choices()[1][0])

    def test_validate_choices(self):
        """Test if save method validates choices before saving instance in database."""
        trip = self.trip_advanced
        # test correct trip type save method
        trip.trekking = ["Raki/raczki", "Apteczka"]
        trip.save()
        self.assertEqual(trip.trekking, ["Raki/raczki", "Apteczka"])
        # test incorrect trip type save method
        trip.trekking = ["Inny element wyposażenia"]
        with self.assertRaises(ValidationError):
            trip.save()


class TripPersonalChecklistModelTests(TestCase):
    """Test model TripPersonalChecklist."""

    def setUp(self):
        self.trip = TripFactory()
        self.user = self.trip.user
        self.trip_checklist = TripPersonalChecklistFactory(
            user=self.user, trip=self.trip
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "trip": "Wyjazd",
            "name": "Nazwa",
            "checklist": "Lista",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_trip_checklist_successful(self):
        """Test if creating a trip personal checklist with valid data
        is successful."""
        trip = TripPersonalChecklist.objects.all()
        self.assertEqual(trip.count(), 1)
        self.assertTrue(trip[0].user, self.user)
        self.assertTrue(trip[0].trip, self.trip)
        self.assertTrue(trip[0].checklist, TripPersonalChecklistFactory.checklist)

    def test_trip_checklist_id_is_uuid(self):
        """Test if id is represented as uuid."""
        trip = self.trip_checklist
        uuid_value = trip.id
        self.assertTrue(isinstance(uuid.UUID(uuid_value), uuid.UUID))

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        all_fields = list(self.field_names.values())
        all_values = list(self.trip_checklist.__dict__.values())
        for field, value in self.trip_checklist:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                if len(all_values[number]) > 1:
                    self.assertEqual(
                        value.replace(",", " "),
                        " ".join(str(i) for i in all_values[number])
                    )
                else:
                    self.assertEqual(value.split(), (all_values[number]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            else:
                self.assertEqual(value, str(all_values[number]))

    def test_unique_constraint_for_trip_checklist_name(self):
        """Test if user can only have trips with unique basic names
        (or no basic name at all)."""
        TripPersonalChecklist.objects.create(
            user=self.user, trip=self.trip, name="Some trip"
        )
        self.assertEqual(TripPersonalChecklist.objects.count(), 2)
        with self.assertRaises(IntegrityError):
            TripPersonalChecklist.objects.create(
                user=self.user, trip=self.trip, name="Some trip"
            )

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(
            str(self.trip_checklist),
            "%s - %s" % (self.trip, TripPersonalChecklistFactory.name)
        )

    def test_integrity_error_for_empty_checklist_name(self):
        """Test if model without required fields cannot be saved in database."""
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                TripPersonalChecklist.objects.create(
                  user=self.user, trip=self.trip, checklist="sth"
                )

    def test_string_to_list_method(self):
        """Test if checklist_to_list method converts string to a list
         based on comma or semicolon separator."""
        trip = self.trip_checklist
        self.assertEqual(
            trip.checklist_to_list(), ["Item 1", "item 2", "item3", "item 4"]
        )


class TripAdditionalInfoModelTests(TestCase):
    """Test model TripAdditionalInfo."""

    def setUp(self):
        self.trip = TripFactory()
        self.user = self.trip.user
        self.trip_additional_info = TripAdditionalInfoFactory(
            user=self.user, trip=self.trip
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "trip": "Wyjazd",
            "name": "Nazwa",
            "info": "Opis",
            "notes": "Uwagi",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_trip_additional_info_successful(self):
        """Test if creating a trip additional info with valid data
        is successful."""
        trip = TripAdditionalInfo.objects.all()
        self.assertEqual(trip.count(), 1)
        self.assertTrue(trip[0].user, self.user)
        self.assertTrue(trip[0].trip, self.trip)
        self.assertTrue(trip[0].name, TripAdditionalInfoFactory.name)

    def test_trip_additional_info_id_is_uuid(self):
        """Test if id is represented as uuid."""
        trip = self.trip_additional_info
        uuid_value = trip.id
        self.assertTrue(isinstance(uuid.UUID(uuid_value), uuid.UUID))

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        number = 0
        all_fields = list(self.field_names.values())
        all_values = list(self.trip_additional_info.__dict__.values())
        for field, value in self.trip_additional_info:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                if len(all_values[number]) > 1:
                    self.assertEqual(
                        value.replace(",", " "),
                        " ".join(str(i) for i in all_values[number])
                    )
                else:
                    self.assertEqual(value.split(), (all_values[number]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            else:
                self.assertEqual(value, str(all_values[number]))

    def test_unique_constraint_for_trip_checklist_name(self):
        """Test if user can only have trips with unique basic names
        (or no basic name at all)."""
        TripAdditionalInfo.objects.create(
            user=self.user, trip=self.trip, name="Add info"
        )
        self.assertEqual(TripAdditionalInfo.objects.count(), 2)
        with self.assertRaises(IntegrityError):
            TripAdditionalInfo.objects.create(
                user=self.user, trip=self.trip, name="Add info"
            )

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(
            str(self.trip_additional_info),
            "%s - %s" % (self.trip, TripAdditionalInfoFactory.name)
        )

    def test_integrity_error_for_empty_name(self):
        """Test if model without required fields cannot be saved in database."""
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                TripAdditionalInfo.objects.create(
                  user=self.user, trip=self.trip,
                )


class TripCostModelTests(TestCase):
    """Test model TripCost."""

    def setUp(self):
        self.trip = TripFactory()
        self.user = self.trip.user
        self.trip_cost = TripCostFactory(
            user=self.user, trip=self.trip
        )
        self.field_names = {
            "id": "id",
            "user": "Użytkownik",
            "trip": "Wyjazd",
            "name": "Nazwa",
            "cost_group": "Grupa kosztów",
            "cost_paid": "Wysokość wydatku",
            "currency": "Waluta",
            "exchange_rate": "Kurs wymiany waluty",
            "notes": "Uwagi",
            "created": "Data dodania",
            "updated": "Data aktualizacji",
        }

    def test_create_trip_cost_successful(self):
        """Test if creating a trip cost with valid data is successful."""
        trip = TripCost.objects.all()
        self.assertEqual(trip.count(), 1)
        self.assertTrue(trip[0].user, self.user)
        self.assertTrue(trip[0].trip, self.trip)
        self.assertTrue(trip[0].cost_group, TripCostFactory.cost_group)

    def test_trip_cost_id_is_uuid(self):
        """Test if id is represented as uuid."""
        trip = self.trip_cost
        uuid_value = trip.id
        self.assertTrue(isinstance(uuid.UUID(uuid_value), uuid.UUID))

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(
            str(self.trip_cost),
            "%s - %s" % (self.trip, TripCostFactory.name)
        )

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        trip = self.trip_cost
        number = 0
        trip_fields = list(self.field_names.values())   # model fields verbose names
        trip_values = list(trip.__dict__.values())      # model instance field values
        for field, value in trip:
            # print("🖥️", field, value)
            self.assertEqual(field, trip_fields[number])
            number += 1
            if isinstance(trip_values[number], uuid.UUID):
                self.assertEqual(value, str(trip_values[number]))
            elif isinstance(trip_values[number], list):
                if len(trip_values[number]) > 1:
                    self.assertEqual(
                        value.replace(",", " "), " ".join(trip_values[number])
                    )
                else:
                    self.assertEqual(value.split(), (trip_values[number]))
            elif isinstance(trip_values[number], datetime.date):
                self.assertEqual(value, str(trip_values[number]))
            else:
                self.assertEqual(value, str(trip_values[number]))

    def test_integrity_error_for_empty_required_fields(self):
        """Test if model without required fields cannot be saved in database."""
        # No cost name
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                TripCost.objects.create(
                    user=self.user, trip=self.trip,
                    cost_group=["Leki"], cost_paid=10, exchange_rate=1
                )
        # No cost group
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                TripCost.objects.create(
                    user=self.user, trip=self.trip, cost_group=None,
                    name="A name", cost_paid=10, exchange_rate=1
                )
        # No cost paid
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                TripCost.objects.create(
                    user=self.user, trip=self.trip,
                    name="A name", cost_group=["Leki"], exchange_rate=1
                )
        # No exchange rate
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                TripCost.objects.create(
                    user=self.user, trip=self.trip,
                    name="A name", cost_group=["Leki"],
                    cost_paid=10, exchange_rate=None
                )

    def test_calculate_cost_at_exchange_rate_method(self):
        """Test if calculate_cost_at_exchange_rate method calculates costs
        at given exchange rate."""
        trip = self.trip_cost
        cost_paid = trip.cost_paid
        exchange_rate = trip.exchange_rate
        self.assertEqual(
            trip.calculate_cost_at_exchange_rate(),
            round(cost_paid*exchange_rate, 2)
        )

    def test_sum_of_trip_costs_method(self):
        """Test if sum_of_trip_costs method calculates sum of all trip costs
        in domestic currency."""
        trip = self.trip_cost
        trip2 = TripCostFactory(user=self.user, trip=self.trip,
                                cost_group="Bilety", cost_paid=200,
                                exchange_rate=1.000)
        trip3 = TripCostFactory(user=self.user, trip=self.trip,
                                cost_group="Bilety", cost_paid=300,
                                exchange_rate=0.500)
        # Sum of cost of default queryset (on all trip costs)
        self.assertEqual(
            trip.sum_of_trip_costs(),
            round(TripCostFactory.cost_paid * TripCostFactory.exchange_rate
                  + trip2.cost_paid * trip2.exchange_rate
                  + trip3.cost_paid * trip3.exchange_rate, 2)
        )
        # Sum of cost of narrowed queryset (to trip costs paid for tickets ('Bilety'))
        queryset_tickets = TripCost.objects.filter(
            trip=self.trip, cost_group="Bilety")
        self.assertEqual(
            trip.sum_of_trip_costs(queryset_tickets),
            round(trip2.cost_paid * trip2.exchange_rate
                  + trip3.cost_paid * trip3.exchange_rate, 2)
        )

    def test_trip_duration_method(self):
        """Test if trip_duration method returns correct number of trip days."""
        # Model data
        trip = self.trip_cost
        self.assertEqual(
            trip.trip_duration(),
            (TripFactory.end_date - TripFactory.start_date).days + 1
        )
        # Custom data
        trip3 = TripCostFactory(user=self.user, trip=self.trip,
                                cost_group="Bilety", cost_paid=400,
                                exchange_rate=0.500)
        start_date = datetime.date(2022, 2, 2)
        end_date = datetime.date(2022, 2, 9)
        days = (end_date - start_date).days + 1
        self.assertEqual(
            trip.trip_duration(start_date=start_date, end_date=end_date,),
            days
        )

    def test_cost_per_person_method(self):
        """Test if cost_per_person method returns correct value of costs
        in domestic currency per person."""
        # Model data
        trip = self.trip_cost
        trip2 = TripCostFactory(user=self.user, trip=self.trip,
                                cost_group="Bilety", cost_paid=200,
                                exchange_rate=3.500)
        costs = (trip.cost_paid * trip.exchange_rate
                 + trip2.cost_paid * trip2.exchange_rate)
        participants = self.trip.participants_number
        self.assertEqual(
            trip.cost_per_person(),
            round(costs/participants, 2)
        )
        # Custom data
        trip3 = TripCostFactory(user=self.user, trip=self.trip,
                                cost_group="Bilety", cost_paid=400,
                                exchange_rate=0.500)
        queryset = TripCost.objects.filter(cost_group="Bilety")
        costs = (queryset[0].cost_paid * queryset[0].exchange_rate
                 + queryset[1].cost_paid * queryset[1].exchange_rate)
        participants = 4
        self.assertEqual(
            trip.cost_per_person(
                queryset=queryset,
                participants=participants
            ),
            round(costs / participants, 2)
        )

    def test_cost_per_day_method(self):
        """Test if cost_per_day method returns correct value of costs
        in domestic currency per one trip day."""
        # Model data
        trip = self.trip_cost
        trip2 = TripCostFactory(user=self.user, trip=self.trip,
                                cost_group="Bilety", cost_paid=200,
                                exchange_rate=3.500)
        costs = (trip.cost_paid * trip.exchange_rate
                 + trip2.cost_paid * trip2.exchange_rate)
        days = trip.trip_duration()
        self.assertEqual(
            trip.cost_per_day(),
            round(costs / days, 2)
        )
        # Custom data
        trip3 = TripCostFactory(user=self.user, trip=self.trip,
                                cost_group="Bilety", cost_paid=400,
                                exchange_rate=0.500)
        queryset = TripCost.objects.filter(cost_group="Bilety")
        costs = (queryset[0].cost_paid * queryset[0].exchange_rate
                 + queryset[1].cost_paid * queryset[1].exchange_rate)
        start_date = datetime.date(2022, 2, 2)
        end_date = datetime.date(2022, 2, 9)
        days = (end_date - start_date).days + 1
        self.assertEqual(
            trip.cost_per_day(
                queryset=queryset,
                start_date=start_date,
                end_date=end_date
            ),
            round(costs / days, 2)
        )

    def test_cost_per_person_per_day_method(self):
        """Test if cost_per_person_per_day method returns correct value of costs
        in domestic currency per one day of trip per one participant."""
        # Model data
        trip = self.trip_cost
        trip2 = TripCostFactory(user=self.user, trip=self.trip,
                                cost_group="Bilety", cost_paid=200,
                                exchange_rate=3.000)
        costs = (trip.cost_paid * trip.exchange_rate
                 + trip2.cost_paid * trip2.exchange_rate)
        participants = self.trip.participants_number
        days = trip.trip_duration()
        self.assertEqual(
            trip.cost_per_person_per_day(),
            round(costs/days/participants, 2)
        )
        # Custom data
        trip3 = TripCostFactory(user=self.user, trip=self.trip,
                                cost_group="Bilety", cost_paid=400,
                                exchange_rate=0.500)
        queryset = TripCost.objects.filter(cost_group="Bilety")
        costs = (queryset[0].cost_paid * queryset[0].exchange_rate
                 + queryset[1].cost_paid * queryset[1].exchange_rate)
        start_date = datetime.date(2022, 2, 2)
        end_date = datetime.date(2022, 2, 9)
        days = (end_date - start_date).days + 1
        participants = 4
        self.assertEqual(
            trip.cost_per_person_per_day(
                queryset=queryset,
                start_date=start_date,
                end_date=end_date,
                participants=participants
            ),
            round(costs / days / participants, 2)
        )
