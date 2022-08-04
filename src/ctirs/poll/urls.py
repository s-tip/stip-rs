try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.poll.views as poll

urlpatterns = [
    # poll top
    _url(r'^$', poll.top),
    # poll detail
    _url(r'^(?P<id_>\S+)/start$', poll.start),
    _url(r'^(?P<taxii_id>\S+)/objects/(?P<object_id>\S+)/versions/$', poll.versions),
    _url(r'^(?P<taxii_id>\S+)/objects/(?P<object_id>\S+)/versions/(?P<version>\S+)/', poll.version),
    _url(r'^register_object/$', poll.register_object),
    # poll detail
    _url(r'^(?P<id_>\S+)$', poll.detail),
]
