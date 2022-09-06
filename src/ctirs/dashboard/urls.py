from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.dashboard.views as dashboard
import ctirs.dashboard.ajax.urls

urlpatterns = [
    # dashboard top
    _url(r'^$', dashboard.top, name='dashboard'),
    # dashboard ajax
    _url(r'^ajax/', include(ctirs.dashboard.ajax.urls)),
]
