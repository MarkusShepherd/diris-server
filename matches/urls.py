from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from matches import views

urlpatterns = [
    url(r'^matches/$', views.match_list),
    url(r'^matches/(?P<pk>[0-9]+)/$', views.match_detail),
]

urlpatterns = format_suffix_patterns(urlpatterns)