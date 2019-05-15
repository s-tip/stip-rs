# -*- coding: utf-8 -*-
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.configuration.system.views as system

urlpatterns = [
    #configuration/system top
    url(r'^$', system.top),
    #configuration/system modify
    url(r'^modify$', system.modify),
    #configuration/system rebuild_cache
    url(r'^rebuild_cache$', system.rebuild_cache),
]
