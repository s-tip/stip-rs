try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.api.v1.stix_files_v2.views as stix_files_v2

urlpatterns = [
    _url(r'^search_bundle$', stix_files_v2.search_bundle),
    _url(r'^create_note$', stix_files_v2.create_note),
    _url(r'^create_opinion$', stix_files_v2.create_opinion),
    _url(r'^revoke$', stix_files_v2.revoke),
    _url(r'^modify$', stix_files_v2.modify),
    _url(r'^(?P<observed_data_id>\S+)/sighting$', stix_files_v2.sighting),
    _url(r'^(?P<object_ref>\S+)/language_contents$', stix_files_v2.language_contents),
    _url(r'^object/(?P<object_id>\S+)/latest$', stix_files_v2.get_latest_object),
    _url(r'^object/(?P<object_id>\S+)/(?P<version>\S+)$', stix_files_v2.get_stix2_content),
    _url(r'^object/(?P<object_id>\S+)$', stix_files_v2.object_main),
]
