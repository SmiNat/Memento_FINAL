import datetime
import logging
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from parameterized import parameterized

from user.handlers import create_slug, is_memento_slug_correct
from user.models import Profile

User = get_user_model()
logger = logging.getLogger("test")


class UserModelTests(TestCase):
    """Test model User."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456",
        )

    def test_create_user_with_email_and_username_successful(self):
        """Test that creating a user with an email and a username is successful."""
        user = self.user
        self.assertTrue(User.objects.count(), 1)
        self.assertEqual(user.email, "jd@example.com")
        self.assertEqual(user.username, "johndoe123")
        self.assertTrue(user.check_password("testpass456"))

    def test_user_id_is_uuid(self):
        """Test if id is represented as uuid."""
        user = self.user
        uuid_value = user.id
        self.assertEqual(uuid_value, uuid.UUID(str(uuid_value)))

    def test_new_user_email_normalized(self):
        """Test if email is normalized for new users."""
        sample_emails = [
            [1, "test1@EXAMPLE.com", "test1@example.com"],
            [2, "Test2@Example.com", "Test2@example.com"],
            [3, "TEST3@EXAMPLE.COM", "TEST3@example.com"],
            [4, "test4@example.com", "test4@example.com"],
        ]
        for number, email, expected in sample_emails:
            user = User.objects.create_user(
                username=f"username{number}",
                email=email,
                password="testpass456",
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username="testuser123",
                email="",
                password="testpass456",
            )

    def test_new_user_without_username_raises_error(self):
        """Test that creating a user without a username raises a ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username="",
                email="test@example.com",
                password="testpass123",
            )

    def test_new_user_with_too_short_username_raises_error(self):
        """Test that creating a user with username of less than 8 characters
        raises a ValidationError."""
        with self.assertRaises(ValidationError):
            User.objects.create_user(
                username="user",
                email="user@example.com",
                password="testpass123",
            )

    def test_new_user_with_forbidden_characters_in_username_raises_error(self):
        """Test that creating a user with username with forbidden characters
        raises a ValidationError."""
        with self.assertRaises(ValidationError):
            User.objects.create_user(
                username="$%^&*#@$^",
                email="test@example.com",
                password="testpass123",
            )

    def test_new_user_without_unique_username_raises_error(self):
        """Test that creating a user with username that already exists
        in database raises a IntegrityError."""
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="johndoe123",
                email="test@example.com",
                password="testpass456",
            )

    def test_new_user_without_unique_email_raises_error(self):
        """Test that creating a user with email that already exists in database
        raises a IntegrityError."""
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="testuser123",
                email="jd@example.com",
                password="testpass456",
            )

    def test_create_superuser(self):
        """Test if creating a superuser is successful."""
        user = User.objects.create_superuser(
            username="testsuperuser123",
            email="test@example.com",
            password="testpass456",
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


class ProfileModelTest(TestCase):
    """Test model Profile."""

    @classmethod
    def setUp(cls):
        """Set up modified objects used by all test methods."""
        Profile.objects.create(
            username="johndoe123",
            email="johndoe@example.com",
            first_name="John",
            last_name="Doe",
            phone_number="111 222 333",
            city="NY",
            street="Pulaskiego",
            building_number=13,
            post_code="10001",
            country="USA",
            access_granted_to="access@example.com",
        )

    def test_field_labels(self):
        """Test if field labels are consistent with verbose names."""
        profile = Profile.objects.first()
        field_label_user = profile._meta.get_field("user").verbose_name
        field_label_username = profile._meta.get_field("username").verbose_name
        field_label_slug = profile._meta.get_field("slug").verbose_name
        field_label_first_name = profile._meta.get_field("first_name").verbose_name
        field_label_last_name = profile._meta.get_field("last_name").verbose_name
        field_label_phone_number = profile._meta.get_field("phone_number").verbose_name
        field_label_city = profile._meta.get_field("city").verbose_name
        field_label_street = profile._meta.get_field("street").verbose_name
        field_label_building_number = profile._meta.get_field(
            "building_number"
        ).verbose_name
        field_label_apartment_number = profile._meta.get_field(
            "apartment_number"
        ).verbose_name
        field_label_post_code = profile._meta.get_field("post_code").verbose_name
        field_label_country = profile._meta.get_field("country").verbose_name
        field_label_access_granted_to = profile._meta.get_field(
            "access_granted_to"
        ).verbose_name
        field_label_created = profile._meta.get_field("created").verbose_name
        field_label_updated = profile._meta.get_field("updated").verbose_name
        self.assertEqual(field_label_user, "Użytkownik")
        self.assertEqual(field_label_username, "Nazwa użytkownika")
        self.assertEqual(field_label_slug, "slug")
        self.assertEqual(field_label_first_name, "Imię")
        self.assertEqual(field_label_last_name, "Nazwisko")
        self.assertEqual(field_label_phone_number, "Numer telefonu")
        self.assertEqual(field_label_city, "Miasto")
        self.assertEqual(field_label_street, "Ulica")
        self.assertEqual(field_label_building_number, "Numer budynku")
        self.assertEqual(field_label_apartment_number, "Numer mieszkania")
        self.assertEqual(field_label_post_code, "Kod pocztowy")
        self.assertEqual(field_label_country, "Kraj zamieszkania")
        self.assertEqual(
            field_label_access_granted_to, "Adres email osoby z dostępem do danych"
        )
        self.assertEqual(field_label_created, "Data dodania")
        self.assertEqual(field_label_updated, "Data aktualizacji")

    def test_profile_id_is_uuid(self):
        """Test if id is represented as uuid."""
        profile = Profile.objects.get(username="johndoe123")
        uuid_value = profile.id
        self.assertEqual(uuid_value, uuid.UUID(str(uuid_value)))

    @parameterized.expand(
        [
            ("all good", "good_username"),
            ("not unique field", "johndoe123"),
            ("too short username", "test"),
            ("forbidden characters in username", "%^&*@#$$#"),
            ("empty field", ""),
        ],
    )
    def test_invalid_username(self, name: str, invalid_username: str):
        """Invalid username raises ValidationError."""
        if name == "all good":
            Profile.objects.create(username=invalid_username, email="test@example.com")
            self.assertTrue(Profile.objects.filter(username=invalid_username).exists())
        else:
            with self.assertRaises(ValidationError):
                Profile.objects.create(username=invalid_username, email="test@example.com")

    @parameterized.expand(
        [
            ("unique field", "johndoevalid"),
            ("valid username (not too short)", "test123valid"),
        ],
    )
    def test_valid_username(self, name: str, valid_username: str):
        """Instance is created with valid username."""
        # valid usernames don't raise ValidationError
        Profile.objects.create(username=valid_username,  email="test@example.com")
        self.assertEqual(Profile.objects.all().count(), 2)

    def test_field_is_unique(self):
        """Test if unique fields has unique values.
            Unique fields: id, username, email, slug."""
        profile_db = Profile.objects.get(username="johndoe123")
        profile_test = Profile.objects.create(
            username="testuser123",
            email="test@example.com",
        )
        profile_db_slug = profile_db.slug
        profile_test_slug = profile_test.slug
        uuid_value_db = profile_db.id
        uuid_value_test = profile_test.id
        self.assertNotEqual(uuid_value_db, uuid_value_test)
        self.assertNotEqual(profile_db_slug, profile_test_slug)
        with self.assertRaises(ValidationError):
            Profile.objects.create(
                username="testuser123",
                email="johndoe@example.com",
            )
        with self.assertRaises(ValidationError):
            Profile.objects.create(
                username="johndoe123",
                email="test@example.com",
            )

    @parameterized.expand(
        [
            ("email without @ and dot (.)", "testexamplecom"),
            ("email without dot (.)", "test@examplecom"),
            ("email without @", "testexample.com"),
            ("empty field", ""),
        ],
    )
    def test_incorrect_email_field_raises_error(self, name: str, invalid_email: str):
        """Test if creating an email with invalid data raises ValidationError."""
        with self.assertRaises(ValidationError):
            Profile.objects.create(username="testuser123", email=invalid_email)

    @parameterized.expand(
        [
            ("email without @ and dot (.)", "testexamplecom"),
            ("email without dot (.)", "test@examplecom"),
            ("email without @", "testexample.com"),
        ],
    )
    def test_incorrect_access_granted_to_field_raises_error(
            self,  name: str, invalid_email: str):
        """Test if creating access_granted_to field with invalid data
        raises ValidationError."""
        with self.assertRaises(ValidationError):
            Profile.objects.create(
                username="testuser123",
                email="test@example.com",
                access_granted_to=invalid_email
            )

    def test_unique_username_for_user_with_profile(self):
        """Tests if creating a User with the same username as in Profile
        raises ValidationError."""
        with self.assertRaises(ValidationError):
            User.objects.create_user(
                username="johndoe123",
                email="test@example.com",
                password="testpass456",
            )

    def test_unique_email_for_user_with_profile(self):
        """Test if creating a User with the same email as in Profile
        raises ValidationError."""
        with self.assertRaises(ValidationError):
            User.objects.create_user(
                username="testuser123",
                email="johndoe@example.com",
                password="testpass456",
            )

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        profile = Profile.objects.get(username="johndoe123")
        if profile.first_name and profile.last_name:
            self.assertEqual(
                str(profile),
                f"{profile.first_name} {profile.last_name} ({profile.username})"
            )
        elif profile.first_name:
            self.assertEqual(str(profile),
                             f"{profile.first_name} ({profile.username})")
        elif profile.last_name:
            self.assertEqual(str(profile),
                             f"{profile.last_name} ({profile.username})")
        else:
            self.assertEqual(str(profile), profile.username)
        self.assertEqual(str(profile), "John Doe (johndoe123)")

    def slug_len_test(self):
        """Test if length of slug is correct."""
        profile = Profile.objects.get(username="johndoe123")
        username = profile.username
        slug = profile.slug
        max_length = (len(str(datetime.datetime.today()))
                      + len(username[::-2])
                      + 22)
        self.assertEqual(len(slug), max(max_length, 50))

    @parameterized.expand(
        [
            ("Real user instance", "johndoe123",),
            ("Latin characters in username", "śżźćąłóęńŚĄŻŹĆŃÓŁĘ"),
            ("Forbidden characters in username",
             "!@#$%^&*<>?.,+=[]{}:;'|\\\""),
        ]
    )
    def test_slug_field_with_no_forbidden_characters(
            self, name: str, username: str):
        """
        Test if save method creates correct string for slug field.
        Allowed characters for slug field:
            Unicode alphabet letters (a-z) and (A-Z)
            Numbers (0-9)
            Hyphens and underscore
        Maximal length of slug: 50 characters.
        """
        slug = create_slug(username)
        self.assertTrue(is_memento_slug_correct(slug))

    def test_unique_slug_field(self):
        """Test if there can only be unique field slug for model
        (for all users)."""
        slug_test = "test_slug_for_users"
        User.objects.create_user(
            username="testuser1",
            email="test1@example.com",
            password="newtestpassFORnewUSER"
        )
        profile1 = Profile.objects.get(username="testuser1")
        profile1.slug = slug_test
        profile1.save()

        User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="newtestpassFORnewUSER"
        )
        profile2 = Profile.objects.get(username="testuser2")
        profile2.slug = slug_test
        profile2.save()

        User.objects.create_user(
            username="testuser3",
            email="test3@example.com",
            password="newtestpassFORnewUSER"
        )
        profile3 = Profile.objects.get(username="testuser3")
        profile3.slug = slug_test
        profile3.save()

        self.assertEqual(slug_test, profile1.slug)
        self.assertNotEqual(slug_test, profile2.slug)
        self.assertNotEqual(slug_test, profile3.slug)
