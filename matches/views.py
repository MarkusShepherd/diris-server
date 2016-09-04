from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework import viewsets
from matches.models import Match, Player, Image, PlayerRoundDetails
from matches.serializers import MatchSerializer, PlayerSerializer, ImageSerializer

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

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
        images = Image.objects.filter(used_in_round_details__round__match__pk=pk)
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
