import datetime
import os
import shutil
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from reportlab.pdfgen.canvas import Canvas

from access.enums import Access
from connection.models import Counterparty, Attachment, user_upload_path

User = get_user_model()


class CounterpartyTests(TestCase):
    """Test model Counterparty."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123", email="jd@example.com",
            password="testpass456")

        # For testing upload of .pdf file
        if not os.path.exists(settings.TEST_ROOT):
            os.mkdir(settings.TEST_ROOT)
        path_temporary = os.path.join(settings.TEST_ROOT, str("temporary"))
        if not os.path.exists(path_temporary):
            os.mkdir(path_temporary)
        if not os.path.exists(os.path.join(path_temporary, str("temporary.pdf"))):
            canvas = Canvas(path_temporary + "/temporary.pdf")
            canvas.drawString(72, 22, "setup = 'temporary file'")
            canvas.save()
        if not os.path.exists(os.path.join(path_temporary,
                                           str("test_temporary.pdf"))):
            canvas = Canvas(path_temporary + "/test_temporary.pdf")
            canvas.drawString(72, 22, "TEST = 'temporary file'")
            canvas.save()
        path_user = os.path.join(path_temporary, str("temporary.pdf"))
        path_test_user = os.path.join(path_temporary, str("test_temporary.pdf"))

        self.counterparty = Counterparty.objects.create(user=self.user,
                                                        name="setup cp")
        self.test_counterparty = Counterparty.objects.create(user=self.user,
                                                             name="test cp")
        self.attachment = Attachment.objects.create(
            user=self.user,
            attachment_name="setup attachment",
            attachment_path=path_user,
        )
        self.attachment.counterparties.add(self.counterparty)
        self.test_attachment = Attachment.objects.create(
            user=self.user,
            attachment_name="test attachment",
            attachment_path=path_test_user,
        )
        self.test_attachment.counterparties.add(self.counterparty)

    def tearDown(self):
        path = os.path.join(settings.TEST_ROOT, str(self.user.id))
        if os.path.exists(path):
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            else:
                shutil.rmtree(path)
        # os.rmdir(settings.TEST_ROOT)

    def test_create_counterparty_successful(self):
        """Test if creating a medicine with valid data is successful."""
        counterparties = Counterparty.objects.all()
        self.assertEqual(counterparties.count(), 2)
        self.assertTrue(counterparties[0].user, self.user)
        self.assertTrue(counterparties[0].name, "setup cp")
        Counterparty.objects.create(user=self.user, name="new name")
        self.assertEqual(counterparties.count(), 3)

    def test_counterparty_id_is_uuid(self):
        """Test if id is represented as uuid."""
        self.assertTrue(isinstance(self.counterparty.id, uuid.UUID))
        self.assertEqual(self.counterparty.id, uuid.UUID(str(
            self.counterparty.id)))

    def test_unique_constraint_for_name_field(self):
        """Test if user can only have name field with unique string for single user."""

        # The same user cannot have two instances with the same name
        with self.assertRaises(ValidationError):
            Counterparty.objects.create(user=self.user,
                                        name="setup cp",
                                        access_granted=Access.ACCESS_GRANTED)
        # Different user can have the same name of counterparty as has the other user
        new_user = User.objects.create_user(
            username="newuser123",
            email="new123@example.com",
            password="testpass456"
        )
        Counterparty.objects.create(user=new_user, name="setup cp",
                                    access_granted=Access.ACCESS_GRANTED)
        self.assertEqual(Counterparty.objects.count(), 3)

    def test_field_is_not_none(self):
        """Test if model without required fields cannot be saved in database."""
        # Empty name field
        with self.assertRaises(ValidationError):
            Counterparty.objects.create(user=self.user)
        # Empty access_granted field
        with self.assertRaises(ValidationError):
            Counterparty.objects.create(
                user=self.user,
                name="new cp",
                access_granted=None
            )

    def test_bank_account_field_has_incorrect_value(self):
        # Restricted characters in "bank_account" field
        # Correct data raises no error
        Counterparty.objects.create(
            user=self.user, name="new name",
            bank_account="GB 4678-0834-5678-9098-7654-5678")
        self.assertTrue(Counterparty.objects.filter(name="new name").exists())
        # Too short "cp_bank_account" field
        with self.assertRaises(ValidationError):
            Counterparty.objects.create(
                user=self.user, name="new name",
                bank_account="GB 4678-0834-5678-9098")

        # Restricted characters in "cp_bank_account" field
        with self.assertRaises(ValidationError):
            Counterparty.objects.create(
                user=self.user, name="new name",
                bank_account="GB 4678-0834-5678-9098-%^&*-*&%*")

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.counterparty), "setup cp")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        field_names = {
            "id": "id",
            "user": "Użytkownik",
            "name": "Nazwa",
            "phone_number": "Numer telefonu - infolinia",
            "email": "Adres email - ogólny",
            "address": "Adres korespondencyjny",
            "www": "Strona internetowa",
            "bank_account": "Numer konta do przelewów",
            "payment_app": "Aplikacja do zarządzania płatnościami",
            "client_number": "Numer płatnika (klienta)",
            "primary_contact_name": "Imię i nazwisko",
            "primary_contact_phone_number": "Numer telefonu",
            "primary_contact_email": "Adres email",
            "secondary_contact_name": "Imię i nazwisko (2)",
            "secondary_contact_phone_number": "Numer telefonu (2)",
            "secondary_contact_email": "Adres email (2)",
            "notes": "Uwagi",
            "access_granted": "Dostęp do danych",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }
        number = 0
        all_fields = list(field_names.values())
        all_values = list(self.counterparty.__dict__.values())
        for field, value in self.counterparty:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                if len(all_values[number]) > 1:
                    self.assertEqual(
                        value.replace(",", " "), " ".join(all_values[number])
                    )
                else:
                    self.assertEqual(value.split(), (all_values[number]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            elif value == "":
                self.assertEqual(all_values[number], None)
            else:
                self.assertEqual(value, str(all_values[number]))

    def test_counterparty_attachments_method(self):
        """Test if attachments method returns queryset of attachments
        assign to the counterparty"""
        # all attachments in database
        self.assertEqual(Attachment.objects.count(), 2)
        # attachments assigned to self.setup_counterparty
        setup_attachments = len(Attachment.objects.filter(
            counterparties=self.counterparty))
        self.assertEqual(len(self.counterparty.attachments()), setup_attachments)
        # attachments assigned to self.test_counterparty
        test_attachments = len(Attachment.objects.filter(
            counterparties=self.test_counterparty))
        self.assertEqual(len(self.test_counterparty.attachments()),
                         test_attachments)


class AttachmentTests(TestCase):
    """Test model Attachment."""

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe123",
            email="johndoe@example.com",
            password="testpass456"
        )

        # For testing upload of .pdf file
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

        self.counterparty = Counterparty.objects.create(user=self.user,
                                                        name="setup cp")
        self.test_counterparty = Counterparty.objects.create(user=self.user,
                                                             name="test cp")
        self.attachment = Attachment.objects.create(
            user=self.user,
            attachment_name="setup attachment",
            attachment_path=path_user,
        )
        self.attachment.counterparties.add(self.counterparty)
        self.test_attachment = Attachment.objects.create(
            user=self.user, attachment_name="test attachment",
            attachment_path=path_test_user)
        self.test_attachment.counterparties.add(self.counterparty)

    def tearDown(self):
        path = os.path.join(settings.TEST_ROOT, str(self.user.id))
        if os.path.exists(path):
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
                shutil.rmtree(path)
            else:
                shutil.rmtree(path)
        # os.rmdir(settings.TEST_ROOT)

    def test_create_attachment_successful(self):
        """Test if creating a medicine with valid data is successful."""
        attachments = Attachment.objects.all()
        self.assertEqual(attachments.count(), 2)
        self.assertTrue(attachments[0].user, self.user)
        self.assertTrue(attachments[0].attachment_name, "setup attachment")
        Attachment.objects.create(user=self.user,
                                  attachment_name="new attachment")
        self.assertEqual(attachments.count(), 3)

    def test_attachment_id_is_uuid(self):
        """Test if id is represented as uuid."""
        self.assertTrue(isinstance(self.attachment.id, uuid.UUID))
        self.assertEqual(self.attachment.id, uuid.UUID(str(self.attachment.id)))

    def test_unique_constraint_for_name_field(self):
        """Test if user can only have attachment_name field with unique string
        for single user."""

        # The same user cannot have two the same fields for attachment_name
        with self.assertRaises(ValidationError):
            Attachment.objects.create(user=self.user,
                                      attachment_name="setup attachment",
                                      access_granted=Access.ACCESS_GRANTED)
        # Different user can have the same field attachment_name as other user
        new_user = User.objects.create_user(
            username="newuser123",
            email="new123@example.com",
            password="testpass456"
        )
        Attachment.objects.create(user=new_user,
                                  attachment_name="setup attachment",
                                  access_granted=Access.ACCESS_GRANTED)
        self.assertEqual(Attachment.objects.count(), 3)

    def test_field_is_not_none(self):
        """Test if model without required fields cannot be saved in database."""
        # Empty name field
        with self.assertRaises(ValidationError):
            Attachment.objects.create(user=self.user,
                                      access_granted="Dostęp do danych")
        # Empty access_granted field
        with self.assertRaises(ValidationError):
            Attachment.objects.create(
                user=self.user,
                attachment_name="new attachment",
                access_granted=None
            )

    def test_object_name_has_correct_string_representation(self):
        """Test if __str__ method returns correct string."""
        self.assertEqual(str(self.attachment), "setup attachment")

    def test_iter_method(self):
        """Test if __iter__ returns correct verbose name and field value."""
        field_names = {
            "id": "id",
            "user": "Użytkownik",
            "slug": "slug",
            "attachment_name": "Nazwa dokumentu",
            "attachment_path": "Załącz dokument",
            "file_date": "Data zawarcia dokumentu",
            "file_info": "Informacja o dokumencie",
            "access_granted": "Dostęp do danych",
            "created": "Data dodania",
            "updated": "Data aktualizacji"
        }
        number = 0
        all_fields = list(field_names.values())
        all_values = list(self.attachment.__dict__.values())
        for field, value in self.attachment:
            self.assertEqual(field, all_fields[number])
            number += 1
            if isinstance(all_values[number], uuid.UUID):
                self.assertEqual(value, str(all_values[number]))
            elif isinstance(all_values[number], list):
                if len(all_values[number]) > 1:
                    self.assertEqual(
                        value.replace(",", " "), " ".join(all_values[number])
                    )
                else:
                    self.assertEqual(value.split(), (all_values[number]))
            elif isinstance(all_values[number], datetime.date):
                self.assertEqual(value, str(all_values[number]))
            elif value == "":
                self.assertEqual(all_values[number], None)
            else:
                self.assertEqual(value, str(all_values[number]))

    @override_settings(MEDIA_ROOT=settings.TEST_ROOT)
    def test_user_upload_path(self):
        """Test if user_upload_path method creates path comprised of correct
        user id and attachment slug."""

        # Create test data (user, profile, attachment)
        user = User.objects.create_user(
            username="johndoe123uploadfortestpurposes",
            email="jd@example.com",
            password="testpass456"
        )
        attachment = Attachment.objects.create(
            user=user, attachment_name="test attachment",)

        # Make sure that no user with the same user id as test user
        # has folder with files on server
        # (in case override_settings won't work)
        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, str(user.id))):
            os.mkdir(os.path.join(settings.MEDIA_ROOT, str(user.id)))
        else:
            raise ValidationError(
                "Cannot conduct test on register username because of conflict "
                "with already existing folder on server!")

        # time.sleep(5)

        path = os.path.join(settings.MEDIA_ROOT, str(user.id))
        if not os.path.exists(path):
            os.mkdir(path)
        canvas = Canvas(path + "/djangounittest1.pdf")
        canvas.drawString(72, 22, "test = 'upload test file'")
        canvas.save()
        attachment_file = os.path.basename(os.path.join(path, "djangounittest1.pdf"))

        attachment.attachment_path = attachment_file
        attachment.save()

        # Conduct test
        instance = Attachment.objects.get(user=user)
        result = f"{instance.user.id}/{instance.slug}.pdf"
        filename = "djangounittest1.pdf"
        self.assertEqual(result, user_upload_path(instance, filename))

        # Clean test directory
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, str(user.id)))

    def test_attachment_file_path_method(self):
        """Test if attachment_file_path method creates path to user's file."""
        user = self.user
        object = Attachment.objects.create(user=user, attachment_name="new file")
        path = os.path.join(settings.TEST_ROOT, str(self.user.id))
        if os.path.exists(os.path.join(path)):
            pass
        else:
            os.mkdir(path)
            self.assertTrue(os.path.exists(path))
        with open(os.path.join(path, "djangounittest.txt"), "w+") as file:
            content = "test = 'test file'"
            file.write(content)
        file_path = os.path.join(path, "djangounittest.txt")
        object.attachment_path = file_path
        self.assertEqual(object.attachment_file_path(), object.attachment_path)
        # shutil.rmtree(path)

    def test_delete_attachment_method(self):
        """Test if delete_attachment method removes single file from server
        without removing folder path."""
        object = Attachment.objects.first()

        # creating single file in user's folder
        path = os.path.join(settings.TEST_ROOT, str(self.user.id))
        if os.path.exists(os.path.join(path)):
            pass
        else:
            os.mkdir(path)
            self.assertTrue(os.path.exists(path))
        with open(os.path.join(path, "djangounittest.txt"), "w+") as file:
            content = "test = 'test file'"
            file.write(content)
        file_path = os.path.join(path, "djangounittest.txt")
        object.attachment_path = file_path
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(os.path.exists(path))

        # deleting single file without deleting user's folder
        object.delete_attachment()
        self.assertFalse(os.path.exists(file_path))
        self.assertTrue(os.path.exists(path))

        # shutil.rmtree(path)

    def test_delete_all_files_method(self):
        """Test if delete_all_files method removes all files from server via
        removing user's folder path."""
        object = Attachment.objects.first()

        # creating user's folder with single file
        path = os.path.join(settings.TEST_ROOT, str(self.user.id))
        if os.path.exists(os.path.join(path)):
            pass
        else:
            os.mkdir(path)
            self.assertTrue(os.path.exists(path))
        with open(os.path.join(path, "djangounittest.txt"), "w+") as file:
            content = "test = 'test file'"
            file.write(content)
        file_path = os.path.join(path, "djangounittest.txt")

        self.assertTrue(os.path.exists(file_path))

        # deleting user's folder by deleting it's path
        object.delete_all_files(user=object.user, delete_path=settings.TEST_ROOT)
        self.assertFalse(os.path.exists(file_path))

    def test_attachment_validators(self):
        """Test if user can upload file with forbidden file extension
        Allowed extensions: pdf, png, jpg."""
        self.assertEqual(Attachment.objects.count(), 2)

        # creating a file with forbidden extension
        path = os.path.join(settings.TEST_ROOT, str(self.user.id))
        if os.path.exists(os.path.join(path)):
            pass
        else:
            os.mkdir(path)
            self.assertTrue(os.path.exists(path))
        with open(os.path.join(path, "djangounittest.py"), "w+") as file:
            content = "test = 'test file'"
            file.write(content)
        file_path = os.path.join(path, "djangounittest.py")

        attachment_file = os.path.basename(file_path)

        # attempt to save a file
        with self.assertRaises(ValidationError):
            self.wrong_attachment = Attachment.objects.create(
                user=self.user,
                attachment_name="python file attachment",
                attachment_path=attachment_file,
            )
        self.assertEqual(Attachment.objects.count(), 2)

        # shutil.rmtree(path)
