from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.taxii_client.detail.urls
import ctirs.configuration.taxii_client.views as taxii_client

urlpatterns = [
    # configuration/taxii_client top
    _url(r'^$', taxii_client.top),
    # configuration/taxii_client create
    _url(r'^create$', taxii_client.create),
    # configuration/taxii_client delete
    _url(r'^delete$', taxii_client.delete),
    # configuration/taxii_client detail
    _url(r'^detail/', include(ctirs.configuration.taxii_client.detail.urls)),
]
