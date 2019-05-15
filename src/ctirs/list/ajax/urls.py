# -*- coding: utf-8 -*-
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.list.ajax.views as ajax

urlpatterns = [
    #list/ajax get_table_info
    url(r'^get_table_info$', ajax.get_table_info),
    #list/publish get_table_info
    url(r'^publish$', ajax.publish),
    #list/publish get_table_info
    url(r'^misp_import$', ajax.misp_import),
]
