# -*- coding: utf-8 -*-

'''serializers'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging
import random

from rest_framework import serializers
from djangae.contrib.gauth_datastore.models import GaeDatastoreUser

from .models import Match, Player, Image, MatchDetailsSerializer, RoundSerializer

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
            'size',
            'is_available_publically',
            'created',
            'last_modified',
        )


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
            'current_round',
            'images',
            'status',
            'created',
            'last_modified',
        )

    def to_representation(self, obj):
        data = super(MatchSerializer, self).to_representation(obj)

        all_images = set()
        viewing_player = self.player.pk if self.player else None

        for round_data, round_obj in zip(data['rounds'], obj.rounds_list):
            assert round_data['number'] == round_obj.number

            images = []

            for player_pk in obj.players_ids:
                details_data = round_data['details'][str(player_pk)]
                details_obj = round_obj.details_dict[player_pk]

                if details_data.get('image'):
                    images.append(details_data['image'])

                if not details_obj.display_vote_to(match_round=round_obj,
                                                   player_pk=viewing_player):
                    details_data['image'] = bool(details_data.get('image'))
                    details_data['vote'] = bool(details_data.get('vote'))
                    details_data['vote_player'] = bool(details_data.get('vote_player'))

            if round_obj.display_images_to(player_pk=viewing_player):
                random.shuffle(images)
                round_data['images'] = images
                all_images.update(images)
            else:
                round_data['images'] = None

        all_images = list(all_images)
        random.shuffle(all_images)
        data['images'] = all_images

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
            'gcm_registration_id',
            'total_matches',
            'created',
            'last_modified',
        )
        read_only_fields = (
            'created',
            'last_modified',
        )

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        password = user_data.pop('password')

        user = GaeDatastoreUser.objects.create_user(**user_data)

        user.set_password(password)
        user.save()

        player = Player.objects.create(user=user, **validated_data)

        return player

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user

            user.username = user_data.get('username') or user.username
            user.email = user_data.get('email') or user.email
            user.first_name = user_data.get('first_name') or user.first_name
            user.last_name = user_data.get('last_name') or user.last_name

            password = user_data.pop('password')
            if password:
                user.set_password(password)

            user.save()

        instance.avatar = validated_data.get('avatar') or instance.avatar
        instance.gcm_registration_id = (validated_data.get('gcm_registration_id')
                                        or instance.gcm_registration_id)
        instance.save()

        return instance
