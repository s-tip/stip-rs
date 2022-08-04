try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.profile.ajax.views as ajax

urlpatterns = [
    # profile change_api_key
    _url(r'^change_api_key', ajax.change_api_key),
]
