# from rest_framework.decorators import detail_route
# from rest_framework.response import Response
from rest_framework import viewsets
from matches.models import Match, Player, Image
from matches.serializers import MatchSerializer, PlayerSerializer, ImageSerializer

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    # @detail_route(renderer_classes=[renderers.StaticHTMLRenderer])
    # def highlight(self, request, *args, **kwargs):
    #     snippet = self.get_object()
    #     return Response(snippet.highlighted)

    # def perform_create(self, serializer):
    #     serializer.save(owner=self.request.user)
