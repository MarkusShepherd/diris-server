from rest_framework import serializers
from matches.models import Match, Round, Player, Image

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ('id', 'players', 'total_rounds', 'status', 'timeout', 'created', 'last_modified')
