from __future__ import unicode_literals

import random
import string

def random_string(length=20, choices=string.digits + string.ascii_letters):
    return ''.join(random.choice(choices) for _ in range(length))
