from rest_framework import serializers
from matches.models import Match, Round, Player, Image

class MatchSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Match
        fields = ('url', 'pk', 'id',
        	'players', 'total_rounds', 'status',
        	'timeout', 'created', 'last_modified')

class RoundSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Round
        fields = ('url', 'pk', 'id',
        	'match', 'players', 'number',
        	'is_current_round', 'status', 'story', 'last_modified')

class PlayerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Player
        fields = ('url', 'pk', 'id', 'external_id',
        	'name', 'email', 'avatar',
        	'gcm_registration_id', 'created', 'last_modified')

class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = ('url', 'pk', 'id', 'image_url')
