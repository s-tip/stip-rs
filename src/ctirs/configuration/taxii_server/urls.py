from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.taxii_server.detail.urls
import ctirs.configuration.taxii_server.views as taxii_server

urlpatterns = [
    # configuration/taxii_server top
    _url(r'^$', taxii_server.top),
    # configuration/taxii_server reboot
    _url(r'^reboot$', taxii_server.reboot),
    # configuration/taxii_server create
    _url(r'^create$', taxii_server.create),
    # configuration/taxii_server delete
    _url(r'^delete$', taxii_server.delete),
    # configuration/taxii_server detail
    _url(r'^detail/', include(ctirs.configuration.taxii_server.detail.urls)),
]
