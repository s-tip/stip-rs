from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.adapter.otx.urls
import ctirs.adapter.isight.urls
import ctirs.adapter.misp.urls

urlpatterns = [
    # adapter/otx
    _url(r'^otx/', include(ctirs.adapter.otx.urls)),
    # adapter/isight
    _url(r'^isight/', include(ctirs.adapter.isight.urls)),
    # adapter/misp
    _url(r'^misp/', include(ctirs.adapter.misp.urls)),
]
