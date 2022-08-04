try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import path as _url
import ctirs.configuration.community.ajax.views as ajax

urlpatterns = [
    # test_webhook
    _url(r'^test_webhook$', ajax.test_webhook),
]
