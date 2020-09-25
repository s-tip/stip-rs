from django.conf.urls import include, url
from ctirs.login.views import login, login_totp
from ctirs.logout.views import logout
import ctirs.dashboard.views as dashboard
import ctirs.dashboard.urls
import ctirs.upload.urls
import ctirs.list.urls
import ctirs.poll.urls
import ctirs.adapter.urls
import ctirs.configuration.urls
import ctirs.profile.urls
import ctirs.api.urls
import django.views.i18n

urlpatterns = [
    url(r'^$', dashboard.top),
    url(r'^dashboard/', include(ctirs.dashboard.urls)),
    url(r'^upload/', include(ctirs.upload.urls)),
    url(r'^list/', include(ctirs.list.urls)),
    url(r'^poll/', include(ctirs.poll.urls)),
    url(r'^adapter/', include(ctirs.adapter.urls)),
    url(r'^configuration/', include(ctirs.configuration.urls)),
    url(r'^profile/', include(ctirs.profile.urls)),
    url(r'^login/$', login, name='login'),
    url(r'^login_totp/$', login_totp, name='login_totp'),
    url(r'^logout/$', logout),
    url(r'^api/', include(ctirs.api.urls)),
    url(r'^jsi18n/(?P<packages>\S+?)/$', django.views.i18n.javascript_catalog),
]
