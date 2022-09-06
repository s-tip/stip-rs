try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.taxii_server.detail.views as detail

urlpatterns = [
    # configuration/taxii_server/modify
    _url(r'^(?P<taxii_id>\S+)/modify$', detail.modify),
    # configuration/taxii_server/detail top
    _url(r'^(?P<taxii_id>\S+)$', detail.top),
]
