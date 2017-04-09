# -*- coding: utf-8 -*-

'''views'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging
import os
import random
import six

from django.contrib.auth import login
from django.db.models import Q
from djangae.contrib.gauth.datastore.models import GaeDatastoreUser
from rest_framework import mixins, permissions, views, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework_jwt.settings import api_settings

from .models import Match, Player, Image
from .serializers import MatchSerializer, PlayerSerializer, ImageSerializer
from .utils import random_string

LOGGER = logging.getLogger(__name__)


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
        player = self.request.user.player
        return player.matches.all().prefetch_related('player_match_details', 'rounds')

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

        matches = self.filter_queryset(self.get_queryset())
        if request.query_params.get('status'):
            matches = matches.filter(status=request.query_params['status'])
        matches = matches.order_by('-last_modified')

        page = self.paginate_queryset(matches)
        if page is not None:
            serializer = self.get_serializer(instance=page, player=player, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(instance=matches, player=player, many=True)
        return Response(serializer.data)

    @list_route(methods=['post'], permission_classes=())
    def statuses(self, request, *args, **kwargs):
        LOGGER.info(request.data)
        result = {}
        for match in self.get_queryset():
            match = match.check_status()
            match.score()
            result[match.pk] = match.status
        return Response(result)

    @detail_route(methods=['post'], permission_classes=())
    def check(self, request, pk=None, *args, **kwargs):
        match = self.get_object().check_status()
        match.score()

        try:
            player = request.user.player

            if match.players.filter(pk=player.pk).exists():
                serializer = self.get_serializer(instance=match, player=player)
                return Response(serializer.data)

            else:
                return Response('ok')

        except AttributeError:
            return Response('ok')

    @detail_route(methods=['post'])
    def accept(self, request, pk, *args, **kwargs):
        player = request.user.player
        match = self.get_object()
        match = match.respond(player.pk, accept=True)
        serializer = self.get_serializer(instance=match, player=player)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def decline(self, request, pk, *args, **kwargs):
        player = request.user.player
        match = self.get_object()
        match = match.respond(player.pk, accept=False)
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

        rounds = match.rounds
        if request.query_params.get('round'):
            rounds = rounds.filter(number=request.query_params['round'])

        images = [details.image
                  for round_ in rounds.all().prefetch_related('player_round_details')
                  if round_.display_images_to(player)
                  for details in round_.player_round_details.all().prefetch_related('image')
                  if details.image]

        serializer = ImageSerializer(instance=images, many=True)
        return Response(serializer.data)


def upload_image(request, owner=None, file_extension=None):
    image = request.data['file']
    orig_extension = (os.path.splitext(image.name)[1]
                      if hasattr(image, 'name') and isinstance(image.name, six.string_types)
                      else None)
    file_extension = file_extension or orig_extension or '.jpeg'
    image.name = random_string() + file_extension

    copyright = request.data.get('copyright') or request.query_params.get('copyright')
    if copyright not in {c[0] for c in Image.COPYRIGHTS}:
        copyright = Image.OWNER if owner else Image.RESTRICTED

    return Image.objects.create(file=image, owner=owner, copyright=copyright)


class MatchImageView(views.APIView):
    parser_classes = (MultiPartParser, FileUploadParser)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, match_pk, round_number, filename):
        player = request.user.player

        match = Match.objects.filter(players__contains=player.pk).all().get(pk=match_pk)
        round_ = match.rounds.get(number=round_number)
        details = round_.player_round_details.get(player=player)

        image = upload_image(request, player)

        story = request.data.get('story') or request.query_params.get('story')

        details.submit_image(image, story=story)

        serializer = MatchSerializer(instance=match, player=player)
        return Response(serializer.data)


class MatchVoteView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, match_pk, round_number, image_pk):
        player = request.user.player

        match = Match.objects.filter(players__contains=player.pk).all().get(pk=match_pk)
        round_ = match.rounds.get(number=round_number)
        details = round_.player_round_details.get(player=player)

        details.submit_vote(image_pk)

        serializer = MatchSerializer(instance=match, player=player)
        return Response(serializer.data)


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

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


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    default_random_size = 5

    @list_route()
    def random(self, request, *args, **kwargs):
        try:
            player = request.user.player
        except AttributeError:
            player = None

        query = Q(is_available_publically=True)
        if player:
            query |= Q(owner=player)
        images = self.get_queryset().filter(query)

        try:
            size = int(request.query_params.get('size'))
            size = size if size > 0 else self.default_random_size
        except (TypeError, ValueError):
            size = self.default_random_size
        size = min(size, len(images))

        serializer = self.get_serializer(instance=random.sample(images, size), many=True)
        return Response(serializer.data)


class ImageUploadView(views.APIView):
    parser_classes = (MultiPartParser, FileUploadParser)

    def put(self, request, filename):
        try:
            owner = request.user.player
        except AttributeError:
            owner = None

        image = image = upload_image(request, owner)
        serializer = ImageSerializer(instance=image)
        return Response(serializer.data)
