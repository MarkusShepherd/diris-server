from rest_framework import serializers
from matches.models import Match, Round, Player, Image, PlayerMatchDetails, PlayerRoundDetails
from django.contrib.auth.models import User

class PlayerMatchDetailsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PlayerMatchDetails
        fields = (
            'pk',
            'player',
            'is_inviting_player',
            'date_invited',
            'invitation_status',
            'date_responded',
            'score',
        )

class PlayerRoundDetailsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PlayerRoundDetails
        fields = (
            'pk',
            'player',
            'is_storyteller',
            'image',
            'score',
            'vote',
        )

class RoundSerializer(serializers.HyperlinkedModelSerializer):
    player_round_details = PlayerRoundDetailsSerializer(many=True)

    class Meta:
        model = Round
        fields = (
            'pk',
            'match',
            'number',
            'is_current_round',
            'player_round_details',
            'status',
            'story',
            'last_modified',
        )
        read_only_fields = (
            'last_modified',
        )

class MatchSerializer(serializers.HyperlinkedModelSerializer):
    players = serializers.HyperlinkedRelatedField(
        many=True,
        required=False,
        view_name='player-detail',
        queryset=Player.objects.all(),
    )
    player_match_details = PlayerMatchDetailsSerializer(many=True, required=False)
    rounds = RoundSerializer(many=True, required=False)
    total_rounds = serializers.IntegerField(required=False)

    class Meta:
        model = Match
        fields = (
            'url',
            'pk',
            'players',
            'player_match_details',
            'total_rounds',
            'rounds',
            'status',
            'timeout',
            'created',
            'last_modified',
        )
        read_only_fields = (
            'created',
            'last_modified',
        )

    def create(self, validated_data):
        data = {
            'player_details': validated_data.get('player_match_details'),
            'players': validated_data.get('players'),
            'total_rounds': validated_data.get('total_rounds'),
            'timeout': validated_data.get('timeout'),
        }

        return Match.objects.create_match(**data)

    def update(self, instance, validated_data):
        pass

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = (
            'pk',
            'username',
            'email',
        )

class PlayerSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()
    matches = serializers.HyperlinkedRelatedField(
        many=True,
        view_name='match-detail',
        read_only=True,
    )

    class Meta:
        model = Player
        fields = (
            'url',
            'pk',
            'user',
            'external_id',
            'gcm_registration_id',
            'avatar',
            'matches',
            'created',
            'last_modified',
        )
        read_only_fields = (
            'created',
            'last_modified',
        )

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create(**user_data)
        player = Player.objects.create(user=user, **validated_data)
        return player

    def update(self, instance, validated_data):
        # TODO do something
        pass

class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = (
            'url',
            'pk',
            'image_url',
            'file',
            'created',
            'last_modified',
        )
        read_only_fields = (
            'file',
            'created',
            'last_modified',
        )
