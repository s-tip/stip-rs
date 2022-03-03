
from django.conf.urls import url
import ctirs.api.v1.stix_files_v2.views as stix_files_v2

urlpatterns = [
    url(r'^search_bundle$', stix_files_v2.search_bundle),
    url(r'^create_note$', stix_files_v2.create_note),
    url(r'^create_opinion$', stix_files_v2.create_opinion),
    url(r'^revoke$', stix_files_v2.revoke),
    url(r'^modify$', stix_files_v2.modify),
    url(r'^(?P<observed_data_id>\S+)/sighting$', stix_files_v2.sighting),
    url(r'^(?P<object_ref>\S+)/language_contents$', stix_files_v2.language_contents),
    url(r'^object/(?P<object_id>\S+)$', stix_files_v2.object_main),
]
