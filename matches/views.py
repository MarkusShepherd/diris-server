# -*- coding: utf-8 -*-

'''views'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import json
import logging
import os.path
# import random

from base64 import b64decode

import six

from django.conf import settings
from django.contrib.auth import login
from django.db.models import Q
from django.utils.crypto import random
from djangae.contrib.gauth_datastore.models import GaeDatastoreUser
from rest_framework import mixins, permissions, status, views, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework_jwt.settings import api_settings

from .models import Player, Image
from .serializers import MatchSerializer, PlayerSerializer, ImageSerializer
from .utils import merge, normalize_space, random_string

LOGGER = logging.getLogger(__name__)


def upload_image(request, owner=None, file_extension=None):
    image = request.data['file']
    orig_extension = (os.path.splitext(image.name)[1]
                      if hasattr(image, 'name') and isinstance(image.name, six.string_types)
                      else None)
    file_extension = file_extension or orig_extension or '.jpeg'
    image.name = random_string() + file_extension

    copyright = (normalize_space(request.data.get('copyright'))
                 or normalize_space(request.query_params.get('copyright')))
    if copyright not in {c[0] for c in Image.COPYRIGHTS}:
        copyright = Image.OWNER if owner else Image.RESTRICTED

    # TODO catch errors
    info = merge(request.query_params or {}, json.loads(request.data.get('info') or '{}'))

    return Image.objects.create_image(file=image, owner=owner, copyright=copyright, info=info)


class MatchViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet
):
    serializer_class = MatchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    ordering = ('-last_modified',)

    def get_queryset(self):
        return self.request.user.player.matches.all()

    def create(self, request, *args, **kwargs):
        player = request.user.player
        request.data['inviting_player'] = player.pk
        return super(MatchViewSet, self).create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        player = request.user.player
        match = self.get_object()
        serializer = self.get_serializer(instance=match, player=player)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        player = request.user.player

        matches = self.filter_queryset(self.get_queryset()).order_by('-last_modified')

        if request.query_params.get('status'):
            matches = matches.filter(status=request.query_params['status'])

        page = self.paginate_queryset(matches)
        if page is not None:
            serializer = self.get_serializer(instance=page, player=player, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(instance=matches, player=player, many=True)
        return Response(serializer.data)

    @list_route(methods=['post'], permission_classes=())
    def statuses(self, request, *args, **kwargs):
        result = {}
        for match in self.get_queryset():
            match.check_status()
            match.score()
            match.save()
            result[match.pk] = match.status
        return Response(result)

    @detail_route(methods=['post'], permission_classes=())
    def check(self, request, pk=None, *args, **kwargs):
        match = self.get_object()
        match.check_status()
        match.score()
        match.save()

        try:
            player = request.user.player

            if player.pk in match.players_ids:
                serializer = self.get_serializer(instance=match, player=player)
                return Response(serializer.data)

            else:
                return Response(status=status.HTTP_204_NO_CONTENT)

        except AttributeError:
            return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'])
    def accept(self, request, pk, *args, **kwargs):
        player = request.user.player

        match = self.get_object()
        match.respond(player.pk, accept=True)
        match.save()

        serializer = self.get_serializer(instance=match, player=player)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def decline(self, request, pk, *args, **kwargs):
        player = request.user.player

        match = self.get_object()
        match.respond(player.pk, accept=False)
        match.save()

        serializer = self.get_serializer(instance=match, player=player)
        return Response(serializer.data)

    @detail_route()
    def players(self, request, pk=None, *args, **kwargs):
        match = self.get_object()
        serializer = PlayerSerializer(instance=match.players, many=True)
        return Response(serializer.data)

    @detail_route()
    def images(self, request, pk=None, *args, **kwargs):
        player = request.user.player
        match = self.get_object()

        rounds = ([match.rounds_list[int(request.query_params['round'])]]
                  if request.query_params.get('round') else match.rounds_list)

        image_pks = {details.image
                     for round_ in rounds
                     if round_.display_images_to(player.pk)
                     for details in round_.details_dict.values()
                     if details.image}

        serializer = ImageSerializer(instance=Image.objects.filter(pk__in=image_pks), many=True)
        return Response(serializer.data)


class MatchImageView(views.APIView):
    parser_classes = (MultiPartParser, FileUploadParser)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, match_pk, round_number, filename):
        player = request.user.player

        match = player.matches.get(pk=match_pk)
        round_ = match.rounds_list[int(round_number) - 1]

        file_extension = (os.path.splitext(filename)[1] if isinstance(filename, six.string_types)
                          else None)
        image = upload_image(request, player, file_extension)

        story = (normalize_space(request.data.get('story'))
                 or normalize_space(request.query_params.get('story')))

        round_.submit_image(player_pk=player.pk, image_pk=image.pk, story=story)
        match.save()

        serializer = MatchSerializer(instance=match, player=player)
        return Response(serializer.data)


class MatchVoteView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, match_pk, round_number, image_pk):
        player = request.user.player

        match = player.matches.get(pk=match_pk)
        round_ = match.rounds_list[int(round_number) - 1]

        round_.submit_vote(player_pk=player.pk, image_pk=int(image_pk))
        match.save()

        serializer = MatchSerializer(instance=match, player=player)
        return Response(serializer.data)


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    ordering = ('-last_modified',)

    def create(self, request, *args, **kwargs):
        response = super(PlayerViewSet, self).create(request, *args, **kwargs)

        player = response.data
        user = GaeDatastoreUser.objects.get(pk=player['user']['pk'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response.data['token'] = token

        return response

    @list_route(methods=['post'], permission_classes=())
    def send(self, request, *args, **kwargs):
        if request.query_params.get('key') != settings.GCM_SERVER_KEY:
            raise NotAuthenticated('the supplied key "{}" is not valid'
                                   .format(request.query_params.get('key')))

        if request.data.get('message') and request.data.get('subscription'):
            msg_obj = request.data.get('message')
            attributes = msg_obj.get('attributes') or {}
            try:
                add_data = json.loads(b64decode(msg_obj.get('data') or 'e30='))
                data = merge(attributes, add_data)
            except Exception as exc:
                LOGGER.warning('could not process data "%s"', msg_obj.get('data'))
                LOGGER.warning(exc)
                data = attributes

        else:
            data = request.data

        player_pk = data.pop('player_pk', None)
        player_pks = data.pop('player_pks', ())

        if isinstance(player_pks, (list, tuple, set, frozenset)):
            player_pks = set(player_pks)
        elif player_pks:
            player_pks = {player_pks}
        else:
            player_pks = set()

        if player_pk:
            player_pks.add(player_pk)

        LOGGER.info(player_pks)
        LOGGER.info(data)

        for player in Player.objects.filter(pk__in=player_pks):
            LOGGER.info(player.pk)
            LOGGER.info(player.send_message(**data))

        return Response(status=status.HTTP_204_NO_CONTENT)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    parser_classes = (MultiPartParser, FileUploadParser)
    ordering = ('random_order',)

    default_random_size = 5
    default_shuffle_size = 100

    # def create(self, request, *args, **kwargs):
    #     if not request.data.get('owner'):
    #         try:
    #             request.data['owner'] = request.user.player
    #         except AttributeError:
    #             request.data['owner'] = None

    #     return super(ImageViewSet, self).create(request, *args, **kwargs)

    @list_route(methods=['get', 'post'])
    def shuffle(self, request, *args, **kwargs):
        try:
            size = int(request.query_params.get('size'))
            size = size if size > 0 else self.default_shuffle_size
        except (TypeError, ValueError):
            size = self.default_shuffle_size

        images = self.get_queryset().order_by('last_modified')
        for image in images[:size]:
            image.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route()
    def random(self, request, *args, **kwargs):
        try:
            player = request.user.player
        except AttributeError:
            player = None

        query = Q(is_available_publically=True)
        if player:
            query |= Q(owner=player)

        images = self.get_queryset().filter(query).order_by('random_order')
        images = images.reverse() if random.random() < .5 else images
        total = images.count()

        try:
            size = int(request.query_params.get('size'))
            size = size if size > 0 else self.default_random_size
        except (TypeError, ValueError):
            size = self.default_random_size
        size = min(size, total)

        start = random.randint(0, total - size)

        serializer = self.get_serializer(instance=images[start:start + size], many=True)
        return Response(serializer.data)


class ImageUploadView(views.APIView):
    parser_classes = (MultiPartParser, FileUploadParser)

    def put(self, request, filename):
        try:
            owner = request.user.player
        except AttributeError:
            owner = None

        file_extension = (os.path.splitext(filename)[1] if isinstance(filename, six.string_types)
                          else None)
        image = upload_image(request, owner, file_extension)
        serializer = ImageSerializer(instance=image)
        return Response(serializer.data)
