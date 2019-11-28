#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url,include
import ctirs.adapter.misp.detail.urls
import ctirs.adapter.misp.views as misp

urlpatterns = [
    #adapter/misp top
    url(r'^$', misp.top),
    #adapter/misp modify
    url(r'^modify$', misp.modify),
    #adapter/misp get
    url(r'^get$', misp.get),
    #adapter/misp detail
    url(r'^detail/', include(ctirs.adapter.misp.detail.urls)),
]
