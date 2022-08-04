import ctirs.api.v1.urls
from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url

urlpatterns = [
    # v1
    _url(r'^v1/', include(ctirs.api.v1.urls)),
]
