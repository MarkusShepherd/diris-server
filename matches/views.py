from __future__ import absolute_import, print_function, unicode_literals

import os

from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from rest_framework import views, viewsets, permissions
from matches.models import Match, Player, Image, PlayerRoundDetails
from matches.serializers import MatchSerializer, PlayerSerializer, ImageSerializer

from .utils import random_string

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @detail_route(methods=['post'])
    def accept(self, request, pk=None, *args, **kwargs):
        match = self.get_object()
        match = match.respond(request.user.player.pk, accept=True)
        return Response(match)

    @detail_route(methods=['post'])
    def decline(self, request, pk=None, *args, **kwargs):
        match = self.get_object()
        match = match.respond(request.user.player.pk, accept=False)
        return Response(match)

    @detail_route()
    def images(self, request, pk=None, *args, **kwargs):
        # images = Image.objects.filter(used_in_round_details__match_round__match__pk=pk)
        images = []
        rounds = self.get_object().rounds
        if request.query_params.get('round'):
            rounds = rounds.filter(number=request.query_params['round'])
        for round_ in rounds.all():
            for details in round_.player_round_details.all():
                if details.image:
                    images.append(details.image)

        serializer = ImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)

class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

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

    def post(self, request, filename=None, format=None):
        file = request.data.get('file')
        file.name = random_string() + os.path.splitext(file.name)[1]
        owner = request.user.player if hasattr(request, 'user') and hasattr(request.user, 'player') else None
        image = Image.objects.create(file=file, owner=owner)
        serializer = ImageSerializer(image, context={'request': request})
        return Response(serializer.data)
