try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.status.ajax.views as ajax

urlpatterns = [
    _url(r'^check/', ajax.check),
]
