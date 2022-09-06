from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.taxii2_client.detail.urls
import ctirs.configuration.taxii2_client.ajax.urls
import ctirs.configuration.taxii2_client.views as taxii2_client

urlpatterns = [
    _url(r'^$', taxii2_client.top),
    _url(r'^create$', taxii2_client.create),
    _url(r'^delete$', taxii2_client.delete),
    _url(r'^detail/', include(ctirs.configuration.taxii2_client.detail.urls)),
    _url(r'^ajax/', include(ctirs.configuration.taxii2_client.ajax.urls)),
]
