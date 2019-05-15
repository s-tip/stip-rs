# -*- coding: utf-8 -*-
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url,include
import ctirs.adapter.otx.detail.urls
import ctirs.adapter.otx.views as otx

urlpatterns = [

    #adapter/otx top
    url(r'^$', otx.top),
    #adapter/otx modify
    url(r'^modify$', otx.modify),
    #adapter/otx get
    url(r'^get$', otx.get),
    #adapter/otx detail
    url(r'^detail/', include(ctirs.adapter.otx.detail.urls)),
]
