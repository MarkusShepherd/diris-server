# -*- coding: utf-8 -*-

'''serializers'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging
import re

from builtins import str, zip
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.utils.crypto import random
from djangae.contrib.gauth_datastore.models import GaeDatastoreUser

from .models import Match, Player, Image, MatchDetailsSerializer, RoundSerializer

LOGGER = logging.getLogger(__name__)


class ImageSerializer(serializers.ModelSerializer):
    url = serializers.URLField(required=False, read_only=True)
    info = serializers.DictField(required=False)

    def __init__(self, player=None, *args, **kwargs):
        super(ImageSerializer, self).__init__(*args, **kwargs)
        self.player = player

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
            'is_available_publicly',
            'created',
            'last_modified',
        )
        read_only_fields = (
            'url',
            'width',
            'height',
            'size',
            'is_available_publicly',
            'created',
            'last_modified',
        )

    def to_representation(self, obj):
        data = super(ImageSerializer, self).to_representation(obj)

        if self.player and obj.owner_id and self.player.pk == obj.owner_id:
            return data

        data.pop('owner', None)
        data.pop('copyright', None)
        data.pop('info', None)
        data.pop('is_available_publicly', None)
        data.pop('created', None)
        data.pop('last_modified', None)

        return data


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
            'deadline_response',
            'deadline_action',
            'created',
            'last_modified',
            'finished',
        )
        read_only_fields = (
            'current_round',
            'images',
            'status',
            'deadline_response',
            'deadline_action',
            'created',
            'last_modified',
            'finished',
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
    username = serializers.RegexField(
        regex=re.compile(r'^\d{21}$|^[a-zA-Z][a-zA-Z0-9_.\-]{2,20}$'),
        min_length=3,
        max_length=21,
        validators=[UniqueValidator(queryset=GaeDatastoreUser.objects.all(), lookup='iexact')],
    )
    email = serializers.EmailField(
        max_length=254,
        validators=[UniqueValidator(queryset=GaeDatastoreUser.objects.all(), lookup='iexact')],
        write_only=True,
    )
    password = serializers.RegexField(
        regex=re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*(.)\1\1)'
                         r'[a-zA-Z0-9"!?,;.:@#$€£¥%&§/()<>=+*_-]{6,128}$'),
        min_length=6,
        max_length=128,
        write_only=True,
    )

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
