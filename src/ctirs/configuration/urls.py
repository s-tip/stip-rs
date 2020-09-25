from django.conf.urls import url, include
import ctirs.configuration.community.urls
import ctirs.configuration.user.urls
import ctirs.configuration.taxii_client.urls
import ctirs.configuration.taxii_server.urls
import ctirs.configuration.taxii2_client.urls
import ctirs.configuration.system.urls
import ctirs.configuration.mongo.urls

urlpatterns = [
    url(r'^community/', include(ctirs.configuration.community.urls)),
    url(r'^user/', include(ctirs.configuration.user.urls)),
    url(r'^taxii_client/', include(ctirs.configuration.taxii_client.urls)),
    url(r'^taxii2_client/', include(ctirs.configuration.taxii2_client.urls)),
    url(r'^taxii_server/', include(ctirs.configuration.taxii_server.urls)),
    url(r'^system/', include(ctirs.configuration.system.urls)),
    url(r'^mongo/', include(ctirs.configuration.mongo.urls)),
]
