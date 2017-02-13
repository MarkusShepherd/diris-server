# -*- coding: utf-8 -*-

'''serializers'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging

from rest_framework import serializers
from djangae.contrib.gauth.datastore.models import GaeDatastoreUser

from .models import Match, Round, Player, Image, PlayerMatchDetails, PlayerRoundDetails

LOGGER = logging.getLogger(__name__)


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta(object):
        model = Image
        fields = (
            'url',
            'pk',
            'file',
            'owner',
            'copyright',
            'created',
            'last_modified',
        )
        read_only_fields = (
            'file',
            'created',
            'last_modified',
        )


class PlayerMatchDetailsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta(object):
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
    image = ImageSerializer(read_only=True)

    class Meta(object):
        model = PlayerRoundDetails
        fields = (
            'pk',
            'player',
            'is_storyteller',
            'image',
            'score',
            'vote',
            'vote_player',
        )


class RoundSerializer(serializers.HyperlinkedModelSerializer):
    player_round_details = PlayerRoundDetailsSerializer(many=True)

    class Meta(object):
        model = Round
        fields = (
            'pk',
            'match',
            'number',
            'is_current_round',
            'storyteller',
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

    class Meta(object):
        model = Match
        fields = (
            'url',
            'pk',
            'players',
            'inviting_player',
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
            # 'player_details': validated_data.get('player_match_details'),
            'players': validated_data.get('players'),
            'inviting_player': validated_data.get('inviting_player'),
            'total_rounds': validated_data.get('total_rounds'),
            'timeout': validated_data.get('timeout'),
        }

        return Match.objects.create_match(**data)

    def update(self, instance, validated_data):
        pass


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta(object):
        model = GaeDatastoreUser
        fields = (
            'pk',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
        )
        extra_kwargs = {'password': {'write_only': True}}


class PlayerSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()
    matches = serializers.HyperlinkedRelatedField(
        many=True,
        view_name='match-detail',
        read_only=True,
    )
    # images = serializers.HyperlinkedRelatedField(
    #     many=True,
    #     view_name='image-detail',
    #     read_only=True,
    # )
    # images = ImageSerializer(many=True, read_only=True)

    class Meta(object):
        model = Player
        fields = (
            'url',
            'pk',
            'user',
            # 'external_id',
            # 'gcm_registration_id',
            'avatar',
            'matches',
            # 'images',
            'created',
            'last_modified',
        )
        read_only_fields = (
            'created',
            'last_modified',
        )

    def create(self, validated_data):
        LOGGER.info(validated_data)
        user_data = validated_data.pop('user')
        password = user_data.pop('password')

        user = GaeDatastoreUser.objects.create_user(**user_data)

        user.set_password(password)
        user.save()

        LOGGER.info('created new user %s', user)
        player = Player.objects.create(user=user, **validated_data)

        return player

    def update(self, instance, validated_data):
        # TODO do something
        pass
