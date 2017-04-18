# -*- coding: utf-8 -*-

'''serializers'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging

from rest_framework import serializers
from djangae.contrib.gauth.datastore.models import GaeDatastoreUser

from .models import Match, Round, Player, Image, MatchDetailsSerializer, RoundSerializer

LOGGER = logging.getLogger(__name__)


class ImageSerializer(serializers.ModelSerializer):
    url = serializers.URLField(required=False, read_only=True)
    info = serializers.DictField(required=False)

    class Meta(object):
        model = Image
        fields = (
            'pk',
            'url',
            'width',
            'height',
            'size',
            'owner',
            'copyright',
            'info',
            'is_available_publically',
            'created',
            'last_modified',
        )
        read_only_fields = (
            'url',
            'width',
            'height',
            'is_available_publically',
            'created',
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
    players = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all(), many=True)
    inviting_player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all(),
                                                         required=False)
    details = serializers.DictField(child=MatchDetailsSerializer(), required=False)
    rounds = RoundSerializer(many=True, required=False)
    total_rounds = serializers.IntegerField(required=False, min_value=Match.MINIMUM_PLAYER)

    def __init__(self, player=None, *args, **kwargs):
        super(MatchSerializer, self).__init__(*args, **kwargs)
        self.player = player

    class Meta(object):
        model = Match
        fields = (
            'pk',
            'players',
            'inviting_player',
            'details',
            'rounds',
            'total_rounds',
            'current_round',
            'images',
            'status',
            'timeout',
            'created',
            'last_modified',
        )
        read_only_fields = (
            'created',
            'last_modified',
        )

    # def to_representation(self, obj):
    #     data = super(MatchSerializer, self).to_representation(obj)

    #     for round_data in data['rounds']:
    #         images = []

    #         for details_data in round_data['player_round_details']:
    #             if details_data.get('image'):
    #                 images.append(details_data['image'])

    #             if not display_vote(round_data, details_data, self.player):
    #                 details_data['image'] = bool(details_data.get('image'))
    #                 details_data['vote'] = bool(details_data.get('vote'))
    #                 details_data['vote_player'] = bool(details_data.get('vote_player'))

    #         round_data['images'] = images if display_images(round_data, self.player) else None

    #     return data

    def create(self, validated_data):
        LOGGER.info(validated_data)
        return Match.objects.create_match(**validated_data)


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
