# -*- coding: utf-8 -*-

'''utility functions'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import random
import string

from collections import OrderedDict
from functools import reduce

from django.db.models import Model
from djangae.db.consistency import ensure_instance_consistent

try:
    str = unicode
except NameError:
    pass  # Forward compatibility with Py3k

try:
    long
except NameError:
    long = int


def random_string(length=20, choices=string.digits + string.ascii_letters):
    return ''.join(random.choice(choices) for _ in range(length))


def ensure_consistency(queryset, *updates):
    update_pks = []

    for update in updates:
        if isinstance(update, (str, int, long, Model)):
            update_pks.append(update)
        elif update:
            update_pks.extend(filter(None, update))

    return reduce(ensure_instance_consistent, update_pks, queryset)


def clear_list(items):
    return list(OrderedDict.fromkeys(item for item in items if item))
