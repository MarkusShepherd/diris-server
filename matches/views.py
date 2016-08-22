from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import generics
from matches.models import Match
from matches.serializers import MatchSerializer

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'matches': reverse('match-list', request=request, format=format),
    })

class MatchList(generics.ListCreateAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

class MatchDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
