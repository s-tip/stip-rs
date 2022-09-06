try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.taxii2_client.ajax.views as ajax

urlpatterns = [
    _url(r'^get_discovery$', ajax.get_discovery),
    _url(r'^get_collections$', ajax.get_collections),
    _url(r'^get_collection$', ajax.get_collection),
]
