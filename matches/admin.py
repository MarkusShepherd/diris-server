# -*- coding: utf-8 -*-

'''admin settings'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

from django.contrib import admin

from .models import Match, Player, Image

admin.site.register(Match)
admin.site.register(Player)
admin.site.register(Image)
