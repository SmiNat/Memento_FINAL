from __future__ import annotations
import logging

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger("all")


class ValidateChoices():
    """
    Verifies if model's field values are selected from correct list of choices.
    Usad mainly for validation of MultiSelectField (external library) used in model fields.
    """

    def __init__(self, choices: list, fields: list):
        self.choices = choices
        self.fields = fields
        self.class_field_choices = {}

    def field_choices(self):
        for number, class_name in enumerate(self.choices):
            self.class_field_choices[number] = list(x[0] for x in class_name.choices)
        # logger.info("🖥️ ValidateChoices - class_field_choices: %s" % self.class_field_choices)
        return self.class_field_choices, self.fields

    @property
    def validate(self) -> None:
        class_field_choices, model_fields_with_choices = self.field_choices()
        for number, field in enumerate(model_fields_with_choices):
            if not field:
                pass
            elif not isinstance(field, list):
                logger.warning("Trip - Validators - Nieprawidłowy typ danych. "
                               "Wartość pola '%s' musi być wprowadzona jako typ: "
                               "lista" % field)
                raise ValidationError(
                    "Nieprawidłowy typ danych. Wartość pola '%s' musi być "
                    "wprowadzona jako typ: lista" % field
                )
            elif len(field) == 1 and field[0] not in class_field_choices[number]:
                logger.warning("Trip - Validators - Niewłaściwa wartość dla pola ('%s'). "
                               "Możliwe opcje: %s" % (field, class_field_choices[number]))
                raise ValidationError(
                    _("Niewłaściwa wartość dla pola ('%s'). Możliwe opcje: %s"
                      % (field, class_field_choices[number]))
                )
            else:
                for choice in field:
                    if choice not in class_field_choices[number]:
                        logger.warning(
                            "Trip - Validators - Niewłaściwa wartość dla pola ('%s'). "
                            "Możliwe opcje: %s" % (choice, class_field_choices[number]))
                        raise ValidationError(
                            _("Niewłaściwa wartość dla pola ('%s'). Możliwe opcje: %s"
                              % (choice, class_field_choices[number]))
                        )
        return
