from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.adapter.otx.detail.urls
import ctirs.adapter.otx.views as otx

urlpatterns = [
    # adapter/otx top
    _url(r'^$', otx.top),
    # adapter/otx modify
    _url(r'^modify$', otx.modify),
    # adapter/otx get
    _url(r'^get$', otx.get),
    # adapter/otx detail
    _url(r'^detail/', include(ctirs.adapter.otx.detail.urls)),
]
