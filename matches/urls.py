from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from matches import views


# Create a router and register our viewsets with it.
router = DefaultRouter() # schema_title='Diris Matches API'
router.register(r'matches', views.MatchViewSet)
router.register(r'players', views.PlayerViewSet)
router.register(r'images', views.ImageViewSet)

urlpatterns = [
	url(r'^', include(router.urls)),
	url(r'^upload/(?P<filename>[^/]+)$', views.ImageUploadView.as_view()),
]
