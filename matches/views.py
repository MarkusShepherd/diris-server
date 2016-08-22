# from rest_framework.decorators import detail_route
# from rest_framework.response import Response
from rest_framework import viewsets
from matches.models import Match
from matches.serializers import MatchSerializer

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    # @detail_route(renderer_classes=[renderers.StaticHTMLRenderer])
    # def highlight(self, request, *args, **kwargs):
    #     snippet = self.get_object()
    #     return Response(snippet.highlighted)

    # def perform_create(self, serializer):
    #     serializer.save(owner=self.request.user)
