# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url, include
import ctirs.adapter.otx.urls
import ctirs.adapter.isight.urls
import ctirs.adapter.misp.urls

urlpatterns = [
    # adapter/otx
    url(r'^otx/', include(ctirs.adapter.otx.urls)),
    # adapter/isight
    url(r'^isight/', include(ctirs.adapter.isight.urls)),
    # adapter/misp
    url(r'^misp/', include(ctirs.adapter.misp.urls)),
]
