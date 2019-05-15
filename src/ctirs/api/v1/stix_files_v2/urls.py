# -*- coding: utf-8 -*-

#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.api.v1.stix_files_v2.views as stix_files_v2

urlpatterns =[
    #STIX V2.x sighting 格納
    url(r'^(?P<observed_data_id>\S+)/sighting$', stix_files_v2.sighting),
    #STIX V2.x language_content 作成
    url(r'^(?P<object_ref>\S+)/language_contents$', stix_files_v2.language_contents),
    #STIX V2.x objects 単位で取得
    url(r'^object/(?P<object_id>\S+)$', stix_files_v2.get_object_main),
]