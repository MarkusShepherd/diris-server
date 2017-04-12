# -*- coding: utf-8 -*-

'''serializers'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging

from rest_framework import serializers
from djangae.contrib.gauth.datastore.models import GaeDatastoreUser

from .models import Match, Round, Player, Image, MatchDetails, RoundDetails

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


class MatchDetailsSerializer(serializers.Serializer):
    player = serializers.IntegerField()
    is_inviting_player = serializers.BooleanField(default=False)
    date_invited = serializers.DateTimeField(required=False)
    invitation_status = serializers.ChoiceField(choices=MatchDetails.INVITATION_STATUSES,
                                                default=MatchDetails.INVITED)
    date_responded = serializers.DateTimeField(required=False)
    score = serializers.IntegerField(min_value=0, default=0)

    def create(self, validated_data):
        return MatchDetails(**validated_data)


class RoundDetailsSerializer(serializers.Serializer):
    player = serializers.IntegerField()
    is_storyteller = serializers.BooleanField(default=False)
    image = serializers.IntegerField(required=False)
    score = serializers.IntegerField(min_value=0, default=0)
    vote = serializers.IntegerField(required=False)
    vote_player = serializers.IntegerField(required=False, read_only=True)

    def create(self, validated_data):
        return RoundDetails(**validated_data)


class RoundSerializer(serializers.Serializer):
    number = serializers.IntegerField(min_value=1)
    storyteller = serializers.IntegerField()
    details = serializers.DictField(child=RoundDetailsSerializer())
    is_current_round = serializers.BooleanField(default=False)
    status = serializers.ChoiceField(choices=Round.ROUND_STATUSES,
                                     default=Round.WAITING)
    story = serializers.CharField(required=False, min_length=3,
                                  allow_blank=False, trim_whitespace=True)

    def create(self, validated_data):
        return Round(**validated_data)


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
    details = serializers.DictField(child=MatchDetailsSerializer(), required=False, read_only=True)
    rounds = RoundSerializer(many=True, required=False, read_only=True)
    total_rounds = serializers.IntegerField(required=False)

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

    def create(self, validated_data):
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
