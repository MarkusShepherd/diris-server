# -*- coding: utf-8 -*-

'''views'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging
import os

from django.contrib.auth import login
from djangae.contrib.gauth.datastore.models import GaeDatastoreUser
from rest_framework import views, viewsets, permissions
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from rest_framework_jwt.settings import api_settings

from .models import Match, Player, Image
from .serializers import MatchSerializer, PlayerSerializer, ImageSerializer, RoundSerializer
from .utils import random_string

LOGGER = logging.getLogger(__name__)


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        player = request.user.player
        serializer = PlayerSerializer(player, context={'request': request})
        request.data['inviting_player'] = serializer.data['url']
        return super(MatchViewSet, self).create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        try:
            player = request.user.player
        except AttributeError:
            player = None

        match = self.get_object()
        serializer = self.get_serializer(match)
        return Response(serializer.filtered_data(player))

    @detail_route(methods=['post'])
    def accept(self, request, pk, *args, **kwargs):
        player = request.user.player
        match = self.get_object()
        match = match.respond(player.pk, accept=True)
        serializer = self.get_serializer(match, context={'request': request})
        return Response(serializer.filtered_data(player))

    @detail_route(methods=['post'])
    def decline(self, request, pk, *args, **kwargs):
        player = request.user.player
        match = self.get_object()
        match = match.respond(player.pk, accept=False)
        serializer = self.get_serializer(match, context={'request': request})
        return Response(serializer.filtered_data(player))

    @detail_route()
    def images(self, request, pk=None, *args, **kwargs):
        try:
            player = request.user.player
        except AttributeError:
            player = None

        match = self.get_object()
        rounds = match.rounds
        if request.query_params.get('round'):
            rounds = rounds.filter(number=request.query_params['round'])

        images = [details.image
                  for round_ in rounds.all()
                  if round_.display_images_to(player)
                  for details in round_.player_round_details.all()
                  if details.image]

        serializer = ImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)


class MatchImageView(views.APIView):
    parser_classes = (FileUploadParser,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, match_pk, round_number, filename):
        player = request.user.player

        match = Match.objects.get(pk=match_pk)
        round_ = match.rounds.get(number=round_number)
        details = round_.player_round_details.get(player=player)

        file = request.data.get('file')
        file.name = random_string() + os.path.splitext(file.name)[1]
        image = Image.objects.create(file=file, owner=player)

        details.submit_image(image, story=request.query_params.get('story'))

        serializer = MatchSerializer(match, context={'request': request})
        return Response(serializer.filtered_data(player))


class MatchVoteView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, match_pk, round_number, image_pk):
        player = request.user.player

        match = Match.objects.get(pk=match_pk)
        round_ = match.rounds.get(number=round_number)
        details = round_.player_round_details.get(player=player)

        details.submit_vote(image_pk)

        serializer = RoundSerializer(round_, context={'request': request})
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

    @detail_route()
    def matches(self, request, pk=None, *args, **kwargs):
        player = self.get_object()
        matches = player.matches.all()
        if request.query_params.get('status'):
            matches = matches.filter(status=request.query_params['status'])
        matches = matches.order_by('-last_modified')
        serializer = MatchSerializer(matches, many=True, context={'request': request})
        return Response(serializer.data)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer


class ImageUploadView(views.APIView):
    parser_classes = (FileUploadParser,)

    def put(self, request, filename):
        file = request.data.get('file')
        file.name = random_string() + os.path.splitext(file.name)[1]
        owner = (request.user.player
                 if hasattr(request, 'user') and hasattr(request.user, 'player')
                 else None)
        image = Image.objects.create(file=file, owner=owner)
        serializer = ImageSerializer(image, context={'request': request})
        return Response(serializer.data)
