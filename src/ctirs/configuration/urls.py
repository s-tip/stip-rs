from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.community.urls
import ctirs.configuration.user.urls
import ctirs.configuration.taxii_client.urls
import ctirs.configuration.taxii_server.urls
import ctirs.configuration.taxii2_client.urls
import ctirs.configuration.system.urls
import ctirs.configuration.mongo.urls
import ctirs.configuration.customizer.urls

urlpatterns = [
    _url(r'^community/', include(ctirs.configuration.community.urls)),
    _url(r'^user/', include(ctirs.configuration.user.urls)),
    _url(r'^taxii_client/', include(ctirs.configuration.taxii_client.urls)),
    _url(r'^taxii2_client/', include(ctirs.configuration.taxii2_client.urls)),
    _url(r'^taxii_server/', include(ctirs.configuration.taxii_server.urls)),
    _url(r'^system/', include(ctirs.configuration.system.urls)),
    _url(r'^mongo/', include(ctirs.configuration.mongo.urls)),
    _url(r'^customizer/', include(ctirs.configuration.customizer.urls)),
]
