from rest_framework import serializers
from matches.models import Match, Round, Player, Image

class MatchSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Match
        fields = ('url', 'pk', 'id',
        	'players', 'total_rounds', 'status',
        	'timeout', 'created', 'last_modified')
