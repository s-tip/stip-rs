try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.user.ajax.views as ajax

urlpatterns = [
    _url(r'^change_auth$', ajax.change_auth),
    _url(r'^change_active$', ajax.change_active),
    _url(r'^unset_mfa$', ajax.unset_mfa),
]
