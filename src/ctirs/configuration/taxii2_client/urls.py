from django.conf.urls import include, url
import ctirs.configuration.taxii2_client.detail.urls
import ctirs.configuration.taxii2_client.ajax.urls
import ctirs.configuration.taxii2_client.views as taxii2_client

urlpatterns = [
    url(r'^$', taxii2_client.top),
    url(r'^create$', taxii2_client.create),
    url(r'^delete$', taxii2_client.delete),
    url(r'^detail/', include(ctirs.configuration.taxii2_client.detail.urls)),
    url(r'^ajax/', include(ctirs.configuration.taxii2_client.ajax.urls)),
]
