from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from matches import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'matches', views.MatchViewSet)

urlpatterns = [
	url(r'^', include(router.urls)),
]
