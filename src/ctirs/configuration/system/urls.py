try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.system.views as system

urlpatterns = [
    # configuration/system top
    _url(r'^$', system.top),
    # configuration/system modify
    _url(r'^modify$', system.modify),
    # configuration/system rebuild_cache
    _url(r'^rebuild_cache$', system.rebuild_cache),
]
