from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
from ctirs.login.views import login, login_totp
from ctirs.logout.views import logout
import ctirs.dashboard.views as dashboard
import ctirs.dashboard.urls
import ctirs.upload.urls
import ctirs.list.urls
import ctirs.status.urls
import ctirs.poll.urls
import ctirs.adapter.urls
import ctirs.configuration.urls
import ctirs.profile.urls
import ctirs.api.urls
from django.views.i18n import JavaScriptCatalog

urlpatterns = [
    _url(r'^$', dashboard.top),
    _url(r'^dashboard/', include(ctirs.dashboard.urls)),
    _url(r'^upload/', include(ctirs.upload.urls)),
    _url(r'^list/', include(ctirs.list.urls)),
    _url(r'^status/', include(ctirs.status.urls)),
    _url(r'^poll/', include(ctirs.poll.urls)),
    _url(r'^adapter/', include(ctirs.adapter.urls)),
    _url(r'^configuration/', include(ctirs.configuration.urls)),
    _url(r'^profile/', include(ctirs.profile.urls)),
    _url(r'^login/$', login, name='login'),
    _url(r'^login_totp/$', login_totp, name='login_totp'),
    _url(r'^logout/$', logout),
    _url(r'^api/', include(ctirs.api.urls)),
    _url(r'^jsi18n/(?P<packages>\S+?)/$', JavaScriptCatalog.as_view()),
]
