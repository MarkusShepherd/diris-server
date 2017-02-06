# -*- coding: utf-8 -*-

'''admin settings'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

from django.contrib import admin

from .models import Match, Round, Player, Image, PlayerMatchDetails, PlayerRoundDetails

admin.site.register(Match)
admin.site.register(Round)
admin.site.register(Player)
admin.site.register(Image)
admin.site.register(PlayerMatchDetails)
admin.site.register(PlayerRoundDetails)
