try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.mongo.views as mongo

urlpatterns = [
    # configuration/mongo top
    _url(r'^$', mongo.top),
    # configuration/mongo modify
    _url(r'^modify$', mongo.modify),
]
