from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.user.views as user
import ctirs.configuration.user.ajax.urls

urlpatterns = [
    # configuration/user top
    _url(r'^$', user.top),
    # configuration/user create
    _url(r'^create_user$', user.create),
    # configuration/user change_password_top
    _url(r'^change_password_top$', user.change_password_top),
    # configuration/user change_password
    _url(r'^change_password$', user.change_password),
    # configuration ajax
    _url(r'^ajax/', include(ctirs.configuration.user.ajax.urls)),
]
