# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
import ctirs.api.v1.stix_files.urls
import ctirs.api.v1.package_id.urls
import ctirs.api.v1.stix_files_v2.urls
import ctirs.api.v1.gv.urls
import ctirs.api.v1.sns.urls

from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
from ctirs.api.v1.stix_files.views import stix_files

urlpatterns = [
    # stix_file
    _url(r'^stix_files$', stix_files),
    _url(r'^stix_files/', include(ctirs.api.v1.stix_files.urls)),
    # stix_file (package_id)
    _url(r'^stix_files_package_id/', include(ctirs.api.v1.package_id.urls)),
    # stix_file (v2)
    _url(r'^stix_files_v2/', include(ctirs.api.v1.stix_files_v2.urls)),
    # gv
    _url(r'^gv/', include(ctirs.api.v1.gv.urls)),
    # sns
    _url(r'^sns/', include(ctirs.api.v1.sns.urls)),
]
