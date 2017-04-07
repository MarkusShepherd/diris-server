# -*- coding: utf-8 -*-

'''serializers'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging

from rest_framework import serializers
from djangae.contrib.gauth.datastore.models import GaeDatastoreUser

from .models import Match, Round, Player, Image, PlayerMatchDetails, PlayerRoundDetails

LOGGER = logging.getLogger(__name__)


class ImageSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Image
        fields = (
            'pk',
            'file',
            'width',
            'height',
            'owner',
            'copyright',
            'created',
            'last_modified',
        )
        read_only_fields = (
            'file',
            'width',
            'height',
            'created',
            'last_modified',
        )


class PlayerMatchDetailsSerializer(serializers.ModelSerializer):
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


class PlayerRoundDetailsSerializer(serializers.ModelSerializer):
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


class RoundSerializer(serializers.ModelSerializer):
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


def display_vote(round_, round_details, player=None):
    if (round_.get('status') == Round.FINISHED
            or (player and player.pk == round_details.get('player'))):
        return True

    elif not player:
        return False

    else:
        details = [d for d in round_.get('player_round_details') or ()
                   if d.get('player') == player.pk]
        return bool(details and (details[0]['is_storyteller'] or details[0]['vote']))


def display_images(round_data, player=None):
    return (round_data.get('status') == Round.SUBMIT_VOTES
            or round_data.get('status') == Round.FINISHED
            or (player and player.pk == round_data['storyteller']))


class MatchSerializer(serializers.ModelSerializer):
    players = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Player.objects.all(),
    )
    player_match_details = PlayerMatchDetailsSerializer(many=True, required=False)
    rounds = RoundSerializer(many=True, required=False)
    total_rounds = serializers.IntegerField(required=False)

    def __init__(self, player=None, *args, **kwargs):
        super(MatchSerializer, self).__init__(*args, **kwargs)
        self.player = player

    def to_representation(self, obj):
        data = super(MatchSerializer, self).to_representation(obj)

        for round_data in data['rounds']:
            images = []

            for details_data in round_data['player_round_details']:
                if details_data.get('image'):
                    images.append(details_data['image'])

                if not display_vote(round_data, details_data, self.player):
                    details_data['image'] = bool(details_data.get('image'))
                    details_data['vote'] = bool(details_data.get('vote'))
                    details_data['vote_player'] = bool(details_data.get('vote_player'))

            round_data['images'] = images if display_images(round_data, self.player) else None

        return data

    class Meta(object):
        model = Match
        fields = (
            'pk',
            'players',
            'inviting_player',
            'player_match_details',
            'total_rounds',
            'current_round',
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
        return Match.objects.create_match(**validated_data)

    def update(self, instance, validated_data):
        pass


class UserSerializer(serializers.ModelSerializer):
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


class PlayerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta(object):
        model = Player
        fields = (
            'pk',
            'user',
            'avatar',
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
