import logging
import os

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from .models import Profile

logger = logging.getLogger("memento")


def send_email(instance, recipient, text_content, html_content, subject):
    """
    Sends email in form of EmailMultiAlternatives from user (instance) to  receiver (recipient).
    Use only for signal purposes with specified message and context.

    :param instance: instance of class User or class Profile
    :param recipient: email address of receiver of the message
    :param text_content: email message in .txt
    :param html_content: email message in .html
    :param subject: message subject (string)
    :return: None (signal sent)
    """

    sender = settings.EMAIL_HOST_USER
    recipient = recipient

    context = {
        "name": instance.username,
        "access_from": instance.email,
        "access_to": recipient
        }

    text_content_to_mail = render_to_string(text_content, context)
    html_content_to_mail = render_to_string(html_content , context)

    try:
        # EmailMultiAlternatives to send both text and html message
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content_to_mail,
            from_email=sender,
            to=[
                recipient,
            ],
            reply_to=[
                sender,
            ],
        )
        email_message.attach_alternative(html_content_to_mail, "text/html")
        email_message.send(fail_silently=False)
    except Exception as e:
        logger.error("🛑 There was an error while sending an email: ", e)
        error = {
            "message": ",".join(map(str, e.args)) if len(e.args) > 0 else "Unknown Error"
        }
        raise Exception(error)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)   # instance == User
def create_profile(sender, instance, created, **kwargs):
    """Function for creating user's profile at registration."""
    # print(f'📂 Instance: {instance} \nCreated: {created}')
    if created:
        # Profile.objects.create(user=instance)
        user = instance
        profile = Profile.objects.create(
            user=user,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )

        send_email(
            instance,
            recipient=profile.email,
            text_content="welcome_email.txt",
            html_content="welcome_email.html",
            subject=_("Witaj na portalu Memento!")
        )


@receiver(pre_save, sender=Profile)
def cache_previous_access(sender, instance, *args, **kwargs):
    original_access_granted_to = None
    try:
        if instance.id:
            original_access_granted_to = sender.objects.get(
                pk=instance.id).access_granted_to
    except Profile.DoesNotExist:
        original_access_granted_to = None
    instance.__original_access_granted_to = original_access_granted_to


@receiver(post_save, sender=Profile)
def post_save_access_handler(sender, instance, created, **kwargs):
    profile = instance
    email_sender = settings.EMAIL_HOST_USER

    if instance.__original_access_granted_to != instance.access_granted_to:

        # Change of access from one user to another
        if instance.__original_access_granted_to and instance.access_granted_to:
            # Access granted email
            send_email(
                instance,
                recipient=instance.access_granted_to,
                text_content="access_email.txt",
                html_content="access_email.html",
                subject=_("Dostęp do danych w Memento!")
            )
            # Access revoked email
            send_email(
                instance,
                recipient=instance.__original_access_granted_to,
                text_content="access_delete_email.txt",
                html_content="access_delete_email.html",
                subject=_("Cofnięto dostęp do danych w Memento!")
            )

        # New access, no previous one
        elif instance.access_granted_to:
            # Access granted email
            send_email(
                instance,
                recipient=instance.access_granted_to,
                text_content="access_email.txt",
                html_content="access_email.html",
                subject=_("Dostęp do danych w Memento!")
            )

        # Delete an access (no new access)
        else:
            # Access revoked email
            send_email(
                instance,
                recipient=instance.__original_access_granted_to,
                text_content="access_delete_email.txt",
                html_content="access_delete_email.html",
                subject=_("Cofnięto dostęp do danych w Memento!")
            )


@receiver(post_save, sender=Profile)
def update_user(sender, instance, created, **kwargs):
    profile = instance
    user = profile.user
    if not created:  # UWAGA NA INFINITE LOOP!!!!!
        # user.first_name = profile.first_name  # commented because it causes error if field first_name is empty (field is not required)
        user.username = profile.username
        user.email = profile.email
        user.first_name = profile.first_name
        user.last_name = profile.last_name
        user.save()


@receiver(post_delete, sender=settings.AUTH_USER_MODEL)     # instance == User
def delete_user(sender, instance, **kwargs):
    user = instance

    send_email(
        instance,
        recipient=user.email,
        text_content="delete_email.txt",
        html_content="delete_email.html",
        subject=_("Konto usunięte")
    )

    path = os.path.join(settings.MEDIA_ROOT, user.username)
    try:
        os.path.exists(path) is False
    except Exception:
        logger.error(
            "🛑 Folder with files still exists after deleting user: %s (id: %s)"
            % (user.username, user.id),
        )
        error = {
            "message": f"Folder with files still exists after deleting user: "
                       f"{user.username} (id: {user.id})",
        }
        raise Exception(error)
