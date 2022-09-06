try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.upload.views as upload

urlpatterns = [
    # upload top
    _url(r'^$', upload.top),
    # upload post
    _url(r'^post/$', upload.upload),
]
