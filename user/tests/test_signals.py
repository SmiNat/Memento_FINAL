import logging

from django.contrib.auth import get_user_model
from django.core import mail
from django.template.loader import render_to_string
from django.test import TestCase
from django.utils.html import escape

from user.models import Profile

logger = logging.getLogger("test")
User = get_user_model()


class UserProfileTest(TestCase):
    """Test relations between creating, updating and deleting user / profile"""

    def test_profile_created_with_user(self):
        """Test if creating a user triggers creating a profile"""
        user1 = User.objects.create_user(
            username="johndoe123",
            email="jd1@example.com",
            password="testpass456"
        )
        user2 = User.objects.create_user(
            username="testuser123",
            password="testpass456",
            email="test@example.com",
        )

        profile1 = Profile.objects.get(username=user1.username)
        profile2 = Profile.objects.get(username=user2)
        self.assertEqual(profile1.username, user1.username)
        self.assertEqual(profile1.user, user1)
        self.assertEqual(profile2.email, user2.email)

    def test_profile_update_triggers_user_update(self):
        """Test if updating profile triggers updating user account"""
        user1 = User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456"
        )
        profile1 = Profile.objects.get(user=user1)
        logger.info("📂 Profile (original): %s, email: %s",
                    profile1, profile1.email)
        logger.info("📂 User (original): %s, email: %s", user1, user1.email)
        self.assertEqual(profile1.email, "jd@example.com")
        self.assertEqual(user1.email, "jd@example.com")

        # Update of profile account
        profile1.email = "test@example.com"
        profile1.save()
        logger.info("📂 Profile (new profile email): %s, email: %s",
                    profile1, profile1.email)
        self.assertEqual(profile1.email, "test@example.com")

        # Verify changes in user account
        user1 = User.objects.get(username=profile1.username)
        logger.info("📂 User (new profile email): %s, email: %s",
                    user1, user1.email)
        self.assertEqual(user1.email, "test@example.com")

    def test_user_delete_triggers_profile_delete(self):
        """Test if deleting profile triggers deleting user account"""
        user1 = User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456"
        )
        profile1 = Profile.objects.get(user=user1)
        logger.info("📂 Profile (original): %s", profile1)
        logger.info("📂 User (original): %s", user1)

        user1.delete()
        try:
            profile1 = Profile.objects.get(username="johndoe123")
        except Profile.DoesNotExist:
            profile1 = None
        try:
            user1 = User.objects.get(username="johndoe123")
        except User.DoesNotExist:
            user1 = None
        logger.info("📂 Profile (delete): %s", profile1)
        logger.info("📂 User (delete): %s", user1)
        self.assertIsNone(profile1)
        self.assertIsNone(user1)


class EmailTest(TestCase):
    """Test if creating or deleting user sends an email"""

    def test_send_email(self):
        mail.send_mail(
            "Subject here",
            "Here is the message.",
            "from@example.com",
            ["to@example.com"],
            fail_silently=False,
        )

        # Test that one message has been sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct
        self.assertEqual(mail.outbox[0].subject, "Subject here")

        # Verify that the correct message is sent
        self.assertEqual(mail.outbox[0].body, "Here is the message.")
        self.assertIn(escape("Here is the message."), mail.outbox[0].body)

    def test_send_EmailMultiAlternatives(self):
        subject = "Memento - TEST"
        sender = "serwis.memento@gmail.com"

        context = {"name": "TEST name"}
        text_content = render_to_string("welcome_email.txt", context)
        html_content = render_to_string("welcome_email.html", context)

        email_message = mail.EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=sender,
            to=[
                "test@example.com",
                "serwis.memento@gmail.com",
            ],
            reply_to=[
                sender,
            ],
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send(fail_silently=False)

        # Test that one message has been sent
        self.assertEqual(len(mail.outbox), 1)
        # Verify that the subject of the first message is correct
        self.assertEqual(mail.outbox[0].subject, "Memento - TEST")
        # Verify sender of the first message is correct
        self.assertEqual(mail.outbox[0].from_email, "serwis.memento@gmail.com")
        self.assertEqual(mail.outbox[0].reply_to, ["serwis.memento@gmail.com"])
        # Verify that recipients of the first message are correct
        self.assertEqual(mail.outbox[0].to,
                         ["test@example.com", "serwis.memento@gmail.com"])
        # Verify that the correct message is sent
        self.assertEqual(mail.outbox[0].body, text_content)
        self.assertIn(mail.outbox[0].alternatives[0][0], html_content)

    def test_creating_user_sends_email(self):
        """Test if creating a user triggers sending email"""
        User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456"
        )
        profile = Profile.objects.get(username="johndoe123")

        context = {"name": profile.username}
        text_content = render_to_string("welcome_email.txt", context)
        html_content = render_to_string("welcome_email.html", context)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Witaj na portalu Memento!")
        self.assertEqual(mail.outbox[0].from_email, "serwis.memento@gmail.com")
        self.assertEqual(mail.outbox[0].to, ["jd@example.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["serwis.memento@gmail.com"])
        self.assertEqual(mail.outbox[0].body, text_content)
        self.assertIn(mail.outbox[0].alternatives[0][0], html_content)

    def test_deleting_user_sends_email(self):
        """Test if deleting a user triggers sending email"""

        # Test creating user signals email send (first email)
        new_user = User.objects.create_user\
            (username="testuser123",
             email="test@example.com",
             password="testpass456"
             )
        profile = Profile.objects.get(username="testuser123")

        context = {"name": profile.username}
        text_content = render_to_string("welcome_email.txt", context)
        html_content = render_to_string("welcome_email.html", context)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Witaj na portalu Memento!")
        self.assertEqual(mail.outbox[0].from_email, "serwis.memento@gmail.com")
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["serwis.memento@gmail.com"])
        self.assertEqual(mail.outbox[0].body, text_content)
        self.assertIn(mail.outbox[0].alternatives[0][0], html_content)

        # Test deleting user signals email send (second email)
        new_user.delete()

        context = {"name": profile.username}
        text_content = render_to_string("delete_email.txt", context)
        html_content = render_to_string("delete_email.html", context)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].subject, "Konto usunięte")
        self.assertEqual(mail.outbox[1].from_email, "serwis.memento@gmail.com")
        self.assertEqual(mail.outbox[1].to, ["test@example.com"])
        self.assertEqual(mail.outbox[1].reply_to, ["serwis.memento@gmail.com"])
        self.assertEqual(mail.outbox[1].body, text_content)
        self.assertIn(mail.outbox[1].alternatives[0][0], html_content)

    def test_changing_access_granted_sends_email(self):
        User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456"
        )  # (first email, welcome email)
        profile = Profile.objects.get(username="johndoe123")
        profile.access_granted_to = "test@example.com"      # initial access granted (second email)
        profile.save()
        profile.access_granted_to = "newmail@example.com"   # change of access  (third and fourth email)
        profile.save()

        # Access granted email (second email)
        context = {"access_from": "jd@example.com", "access_to": "test@example.com"}
        text_content = render_to_string("access_email.txt", context)
        html_content = render_to_string("access_email.html", context)
        # Access granted email (third email)
        context_granted = {"access_from": "jd@example.com",
                           "access_to": "newmail@example.com"}
        text_content_granted = render_to_string("access_email.txt",
                                                context_granted)
        html_content_granted = render_to_string("access_email.html",
                                                context_granted)
        # Access revoked email (fourth email)
        context_revoked = {"access_from": "jd@example.com",
                           "access_to": "test@example.com"}
        text_content_revoked = render_to_string("access_delete_email.txt",
                                                context_revoked)
        html_content_revoked = render_to_string("access_delete_email.html",
                                                context_revoked)

        self.assertEqual(len(mail.outbox), 4)   # 4 emails (creating a user (1), setting first access (2), and changing access (3 and 4)
        # Access granted email (second email)
        self.assertEqual(mail.outbox[1].subject, "Dostęp do danych w Memento!")
        self.assertEqual(mail.outbox[1].from_email, "serwis.memento@gmail.com")
        self.assertEqual(mail.outbox[1].to, ["test@example.com"])
        self.assertEqual(mail.outbox[1].reply_to, ["serwis.memento@gmail.com"])
        self.assertEqual(mail.outbox[1].body, text_content)
        self.assertIn(mail.outbox[1].alternatives[0][0], html_content)
        # New access granted email (third email)
        self.assertEqual(mail.outbox[2].subject, "Dostęp do danych w Memento!")
        self.assertEqual(mail.outbox[2].from_email, "serwis.memento@gmail.com")
        self.assertEqual(mail.outbox[2].to, ["newmail@example.com"])
        self.assertEqual(mail.outbox[2].reply_to, ["serwis.memento@gmail.com"])
        self.assertEqual(mail.outbox[2].body, text_content_granted)
        self.assertIn(mail.outbox[2].alternatives[0][0], html_content_granted)
        # Access revoked email (fourth email)
        self.assertEqual(mail.outbox[3].subject, "Cofnięto dostęp do danych w Memento!")
        self.assertEqual(mail.outbox[3].from_email, "serwis.memento@gmail.com")
        self.assertEqual(mail.outbox[3].to, ["test@example.com"])
        self.assertEqual(mail.outbox[3].reply_to, ["serwis.memento@gmail.com"])
        self.assertEqual(mail.outbox[3].body, text_content_revoked)
        self.assertIn(mail.outbox[3].alternatives[0][0], html_content_revoked)

    def test_deleting_access_granted_sends_email(self):
        User.objects.create_user(
            username="johndoe123",
            email="jd@example.com",
            password="testpass456"
        )  # first email
        profile = Profile.objects.get(username="johndoe123")
        profile.access_granted_to = "test@example.com"  # second email
        profile.save()

        profile.access_granted_to = None    # third email
        profile.save()

        context = {"access_from": "jd@example.com",
                   "access_to": "test@example.com"}
        text_content = render_to_string("access_delete_email.txt", context)
        html_content = render_to_string("access_delete_email.html", context)

        self.assertEqual(len(mail.outbox), 3)  # 3 emails (creating a user and granting first access triggers email too)
        self.assertEqual(mail.outbox[2].subject, "Cofnięto dostęp do danych w Memento!")
        self.assertEqual(mail.outbox[2].from_email, "serwis.memento@gmail.com")
        self.assertEqual(mail.outbox[2].to, ["test@example.com"])
        self.assertEqual(mail.outbox[2].reply_to, ["serwis.memento@gmail.com"])
        self.assertEqual(mail.outbox[2].body, text_content)
        self.assertIn(mail.outbox[2].alternatives[0][0], html_content)
