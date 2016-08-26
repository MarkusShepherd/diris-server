from rest_framework import serializers
from matches.models import Match, Round, Player, Image, PlayerMatchDetails, PlayerRoundDetails
from django.contrib.auth.models import User
import datetime
import random

class PlayerMatchDetailsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PlayerMatchDetails
        fields = ('pk', 'id',
            'player', 'is_inviting_player', 'date_invited',
            'invitation_status', 'date_responded', 'score')

class PlayerRoundDetailsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PlayerRoundDetails
        fields = ('pk', 'id',
            'player', 'is_storyteller', 'image',
            'score', 'vote')

class RoundSerializer(serializers.HyperlinkedModelSerializer):
    player_round_details = PlayerRoundDetailsSerializer(many=True)

    class Meta:
        model = Round
        fields = ('pk', 'id',
            'match', 'number',
            'is_current_round', 'player_round_details',
            'status', 'story', 'last_modified')

class MatchSerializer(serializers.HyperlinkedModelSerializer):
    players = serializers.HyperlinkedRelatedField(many=True,
        required=False,
        view_name='player-detail',
        queryset=Player.objects.all())
    player_match_details = PlayerMatchDetailsSerializer(many=True, required=False)
    rounds = RoundSerializer(many=True, required=False)
    total_rounds = serializers.IntegerField(required=False)

    class Meta:
        model = Match
        fields = ('url', 'pk', 'id',
            'players', 'player_match_details',
            'total_rounds', 'rounds', 'status',
            'timeout', 'created', 'last_modified')

    def create(self, validated_data):
        player_details_data = validated_data.pop('player_match_details', None)

        if not player_details_data:
            players_data = validated_data.pop('players', None)
            if not players_data:
                # TODO some meaningful error
                raise Error()
            player_details_data = [{'player': player, 'is_inviting_player': False}
                for player in players_data]
            player_details_data[0]['is_inviting_player'] = True

        total_rounds = validated_data.get('total_rounds', len(player_details_data))
        data = {'total_rounds': total_rounds}
        if validated_data.get('timeout'):
            data['timeout'] = validated_data['timeout']

        match = Match.objects.create(**data)

        for player_detail in player_details_data:
            is_inviting_player = player_detail.get('is_inviting_player', False)
            player_detail['match'] = match
            player_detail['invitation_status'] = (PlayerMatchDetails.ACCEPTED
                if is_inviting_player else PlayerMatchDetails.INVITED)
            player_detail['date_responded'] = datetime.datetime.now() if is_inviting_player else None
            PlayerMatchDetails.objects.create(**player_detail)

        players = [player_detail['player'] for player_detail in player_details_data]
        random.shuffle(players)

        for i in range(total_rounds):
            data = {
                'match': match,
                'number': i + 1,
                'is_current_round': i == 0,
                'status': Round.WAITING,
            }
            round = Round.objects.create(**data)

            for player in players:
                data = {
                    'player': player,
                    'round': round,
                    'is_storyteller': players[i % len(players)] == player,
                }
                PlayerRoundDetails.objects.create(**data)

        return match

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('pk', 'id', 'username', 'email')

class PlayerSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()
    matches = serializers.HyperlinkedRelatedField(many=True, view_name='match-detail', read_only=True)

    class Meta:
        model = Player
        fields = ('url', 'pk', 'id',
            'external_id', 'gcm_registration_id',
            'avatar', 'matches',
            'created', 'last_modified', 'user')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create(**user_data)
        player = Player.objects.create(user=user, **validated_data)
        return player

class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = ('url', 'pk', 'id', 'image_url')
