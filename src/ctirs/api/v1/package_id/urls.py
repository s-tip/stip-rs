# -*- coding: utf-8 -*-

# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.api.v1.package_id.views as package_id

urlpatterns = [
    # STIX 取得
    url(r'^(?P<package_id>\S+)/stix$', package_id.stix_files_package_id_stix),
    # 関連 STIX 取得
    url(r'^(?P<package_id>\S+)/related_packages$', package_id.stix_files_package_id_related_packages),
    # STIXファイル情報取得/削除　
    url(r'^(?P<package_id>\S+)$', package_id.stix_files_package_id),

]