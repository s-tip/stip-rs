try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.customizer.views as customizer

urlpatterns = [
    _url(r'^set_configuration/$', customizer.set_customizer_configuration, name='set_customizer_configuration'),
    _url(r'^get_configuration/$', customizer.get_customizer_configuration, name='get_customizer_configuration'),
    _url(r'^$', customizer.stix_customizer, name='stix_customizer'),
]
