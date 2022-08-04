from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.status.views as status
import ctirs.status.ajax.urls

urlpatterns = [
    _url(r'^$', status.top, name='status'),
    _url(r'^delete/$', status.delete),
    _url(r'^ajax/', include(ctirs.status.ajax.urls)),
]
