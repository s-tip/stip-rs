from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.list.views as list_
import ctirs.list.ajax.urls

urlpatterns = [
    # list top
    _url(r'^$', list_.top, name='list'),
    # list delete
    _url(r'^delete$', list_.delete),
    # list download
    _url(r'^download$', list_.download),
    # list/ajax
    _url(r'^ajax/', include(ctirs.list.ajax.urls)),
]
