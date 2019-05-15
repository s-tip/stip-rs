# -*- coding: utf-8 -*-
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url,include
import ctirs.list.views as list_
import ctirs.list.ajax.urls

urlpatterns = [
    #list top
    url(r'^$', list_.top),
    #list delete
    url(r'^delete$', list_.delete),
    #list download
    url(r'^download$', list_.download),
    #list/ajax
    url(r'^ajax/', include(ctirs.list.ajax.urls)),
]
