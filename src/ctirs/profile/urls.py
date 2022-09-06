from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.profile.views as profile
import ctirs.profile.ajax.urls

urlpatterns = [
    # profile top
    _url(r'^$', profile.top),
    # profile change_password
    _url(r'^change_password$', profile.change_password, name='password_modified'),
    # profile change_screen_name
    _url(r'^change_screen_name$', profile.change_screen_name),
    # profile ajax
    _url(r'^ajax/', include(ctirs.profile.ajax.urls)),
]
