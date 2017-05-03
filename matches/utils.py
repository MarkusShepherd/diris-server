# -*- coding: utf-8 -*-

'''utility functions'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging
# import random
import string

from collections import OrderedDict

import six

from django.utils.crypto import get_random_string, random
from rest_framework_jwt.utils import jwt_payload_handler

try:
    str = unicode
except NameError:
    pass  # Forward compatibility with Py3k

try:
    long
except NameError:
    long = int

LOGGER = logging.getLogger(__name__)


def random_integer(*args, **kwargs):
    return random.randint(-2147483648, 2147483647)


def random_string(length=20, choices=string.digits + string.ascii_letters):
    '''random string of given length sample from choices'''

    # return ''.join(random.choice(choices) for _ in range(length))
    return get_random_string(length=length, allowed_chars=choices)


def clear_list(items):
    '''remove duplicates and empty values from a list without changing the order'''

    return list(OrderedDict.fromkeys(filter(None, items)))


def merge(*dicts):
    '''merge a list of dictionaries'''

    if not dicts:
        return {}

    if len(dicts) == 1:
        return dicts[0]

    result = {}
    for dictionary in dicts:
        for key, value in six.iteritems(dictionary):
            old_value = result.get(key)
            if isinstance(old_value, dict) and isinstance(value, dict):
                value = merge(old_value, value)
            elif isinstance(old_value, (list, tuple)) and isinstance(value, (list, tuple)):
                value = old_value + type(old_value)(value)
            elif isinstance(old_value, (set, frozenset)) and isinstance(value, (set, frozenset)):
                value = old_value | type(old_value)(value)
            result[key] = value

    return result


def normalize_space(item, preserve_linebreaks=False):
    '''replace all runs of whitespace with a single space'''

    if not item:
        return None

    if preserve_linebreaks:
        return '\n'.join(normalize_space(s) or '' for s in str(item).splitlines()).strip()

    return ' '.join(str(item).split())


def jwt_payload(user):
    payload = jwt_payload_handler(user)
    payload['pk'] = user.player.pk
    LOGGER.info(payload)
    return payload


def find_current_round(match):
    for round_ in match.rounds_list:
        if round_.is_current_round:
            return round_.number

    return -1
