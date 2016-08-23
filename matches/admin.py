from django.contrib import admin

from .models import Match, Round, Player, Image, PlayerMatchDetails, PlayerRoundDetails

admin.site.register(Match)
admin.site.register(Round)
admin.site.register(Player)
admin.site.register(Image)
admin.site.register(PlayerMatchDetails)
admin.site.register(PlayerRoundDetails)
