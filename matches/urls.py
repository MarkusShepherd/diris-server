from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from matches import views

match_list = views.MatchViewSet.as_view({
	'get': 'list',
	'post': 'create',
})
match_detail = views.MatchViewSet.as_view({
	'get': 'retrieve',
	'put': 'update',
	'patch': 'partial_update',
	'delete': 'destroy',
})

urlpatterns = [
	url(r'^$', views.api_root),
    url(r'^matches/$', match_list, name='match-list'),
    url(r'^matches/(?P<pk>[0-9]+)/$', match_detail, name='match-detail'),
]

urlpatterns = format_suffix_patterns(urlpatterns)