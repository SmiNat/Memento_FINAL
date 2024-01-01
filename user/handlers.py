import datetime
import string
import random

from django.template.defaultfilters import slugify

CHARACTERS = string.ascii_letters + string.digits

FORBIDDEN_USERNAME_LIST = [
    "forbidenusername",
    "johndoe123uploadfortestpurposesforbidde",
    "johndoe123uploadfortestpurposesforbidden",
]  # for test use only


def create_slug(user: str | None = None) -> str:
    """
    Creates custom slug for given string.
    Allowed characters:
        Unicode alphabet letters (a-z) and (A-Z)
        Digits (0-9)
        Hyphens and underscore
    Maximal length of slug string: 50 characters.
    """
    username = user if user else ""
    random_string = ''.join(random.choices(CHARACTERS, k=22))
    before_shuffle = str(slugify(username))[::-2] \
                     + random_string \
                     + str(slugify(datetime.date.today())[::-1])
    shuffle_list = list(element for element in before_shuffle)
    random.shuffle(shuffle_list)
    slug = ''.join(shuffle_list)
    if len(slug) > 50:
        slug = slug[0:49]
    return slug


def is_memento_slug_correct(name: str) -> bool:
    """Verifies if slug contains only allowed characters."""
    allowed_characters = CHARACTERS + "_-"
    allowed_characters_list = list(element for element in allowed_characters)
    slug = create_slug(name)
    slug_list = list(element for element in slug)
    for character in slug_list:
        if character not in allowed_characters_list:
            raise ValueError("SLUG ERROR: Forbidden character in slug: "
                             "'%s'." % character)
    if len(slug) > 50:
        raise ValueError("SLUG ERROR: Too many characters in slug. "
                         "Length of slug cannon exceed 50 characters. "
                         "Actual length of slug: %s characters." % len(slug))
    return True
