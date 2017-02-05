from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.views import serve

from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.authtoken.views import obtain_auth_token

import session_csrf
session_csrf.monkeypatch()

from django.contrib import admin
admin.autodiscover()

urlpatterns = (
    # Examples:
    # url(r'^$', 'diris.views.home', name='home'),
    url(r'^', include('matches.urls')),
    # url(r'^blog/', include('blog.urls')),
    url(r'^_ah/', include('djangae.urls')),

    # Note that by default this is also locked down with login:admin in app.yaml
    url(r'^admin/', include(admin.site.urls)),

    url(r'^csp/', include('cspreports.urls')),

    # url(r'^auth/', include('django.contrib.auth.urls')),
    # url(r'^gauth/', include('djangae.contrib.gauth.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # url(r'^api-token-auth/', obtain_auth_token),
    url(r'^api-jwt-auth/', obtain_jwt_token),
)

if settings.DEBUG:
    urlpatterns += tuple(static(settings.STATIC_URL, view=serve, show_indexes=True))
