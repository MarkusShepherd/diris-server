# -*- coding: utf-8 -*-

'''URLs'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()  # schema_title='Diris Matches API'
router.register(r'matches', views.MatchViewSet, base_name='match')
router.register(r'players', views.PlayerViewSet, base_name='player')
router.register(r'images', views.ImageViewSet, base_name='image')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^upload/(?P<filename>[^/]+)/?$', views.ImageUploadView.as_view()),
    url(r'^matches/(?P<match_pk>[^/]+)/(?P<round_number>[^/]+)/image/(?P<filename>[^/]+)/?$',
        views.MatchImageView.as_view()),
    url(r'^matches/(?P<match_pk>[^/]+)/(?P<round_number>[^/]+)/vote/(?P<image_pk>[^/]+)/?$',
        views.MatchVoteView.as_view()),
]
