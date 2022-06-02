from django.conf.urls import url
import ctirs.configuration.customizer.views as customizer

urlpatterns = [
    url(r'^set_configuration/$', customizer.set_customizer_configuration, name='set_customizer_configuration'),
    url(r'^get_configuration/$', customizer.get_customizer_configuration, name='get_customizer_configuration'),
    url(r'^$', customizer.stix_customizer, name='stix_customizer'),
]
