from django.conf.urls import url
import ctirs.configuration.taxii2_client.ajax.views as ajax

urlpatterns = [
    url(r'^get_discovery$', ajax.get_discovery),
    url(r'^get_collections$', ajax.get_collections),
]
