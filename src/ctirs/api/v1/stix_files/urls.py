try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.api.v1.stix_files.views as stix_files

urlpatterns = [
    # STIX 取得
    _url(r'^(?P<id_>\S+)/stix$', stix_files.stix_files_id_stix),
    # STIX ファイル情報取得/削除
    _url(r'^(?P<id_>\S+)$', stix_files.stix_files_id),
]
