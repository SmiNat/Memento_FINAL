from django.db import models
from django.utils.translation import gettext_lazy as _


class Access(models.TextChoices):
    NO_ACCESS_GRANTED = _("Brak dostępu"), _("Brak dostępu")
    ACCESS_GRANTED = _("Udostępnij dane"), _("Udostępnij dane")
