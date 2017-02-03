from __future__ import absolute_import, print_function, unicode_literals

import os

from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from rest_framework import views, viewsets, permissions
# from djangae.contrib.improve_queryset_consistency import improve_queryset_consistency
# from djangae.contrib.consistency import improve_queryset_consistency

from matches.models import Match, Player, Image, PlayerRoundDetails
from matches.serializers import MatchSerializer, PlayerSerializer, ImageSerializer, RoundSerializer

from .utils import random_string

class MatchViewSet(viewsets.ModelViewSet):
    # queryset = improve_queryset_consistency(Match.objects.all())
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    # permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    # def get_queryset(self):
    #     return Match.objects.all()

    @detail_route(methods=['post'])
    def accept(self, request, pk, *args, **kwargs):
        match = self.get_object()
        # match = self.get_queryset().get(pk=pk)
        match = match.respond(request.user.player.pk, accept=True)
        return Response(match)

    @detail_route(methods=['post'])
    def decline(self, request, pk, *args, **kwargs):
        match = self.get_object()
        # match = self.get_queryset().get(pk=pk)
        match = match.respond(request.user.player.pk, accept=False)
        return Response(match)

    @detail_route()
    def images(self, request, pk=None, *args, **kwargs):
        # images = Image.objects.filter(used_in_round_details__match_round__match__pk=pk)
        images = []
        match = self.get_object()
        # match = self.get_queryset().get(pk=pk)
        rounds = match.rounds
        if request.query_params.get('round'):
            rounds = rounds.filter(number=request.query_params['round'])
        for round_ in rounds.all():
            for details in round_.player_round_details.all():
                if details.image:
                    images.append(details.image)

        serializer = ImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)

class MatchApiView(views.APIView):
    parser_classes = (FileUploadParser,)

    def post(self, request, match_pk, round_number, filename):
        try:
            player = request.user.player
        except Exception:
            # print(request.query_params.get('player'))
            player = Player.objects.get(pk=request.query_params.get('player'))

        match = Match.objects.get(pk=match_pk)
        round_ = match.rounds.get(number=round_number)
        details = round_.player_round_details.get(player=player)

        file = request.data.get('file')
        file.name = random_string() + os.path.splitext(file.name)[1]
        image = Image.objects.create(file=file, owner=player)

        details.submit_image(image, story=request.query_params.get('story'))

        serializer = RoundSerializer(round_, context={'request': request})
        return Response(serializer.data)

class PlayerViewSet(viewsets.ModelViewSet):
    # queryset = improve_queryset_consistency(Player.objects.all())
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    # def get_queryset(self):
    #     return Player.objects.all()

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
    # queryset = improve_queryset_consistency(Image.objects.all())
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    # def get_queryset(self):
    #     return Image.objects.all()

class ImageUploadView(views.APIView):
    parser_classes = (FileUploadParser,)

    def put(self, request, filename):
        file = request.data.get('file')
        file.name = random_string() + os.path.splitext(file.name)[1]
        owner = request.user.player if hasattr(request, 'user') and hasattr(request.user, 'player') else None
        image = Image.objects.create(file=file, owner=owner)
        serializer = ImageSerializer(image, context={'request': request})
        return Response(serializer.data)
