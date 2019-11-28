# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url, include
import ctirs.adapter.isight.detail.urls
import ctirs.adapter.isight.views as isight

urlpatterns = [
    # adapter/isight top
    url(r'^$', isight.top),
    # adapter/isight modify
    url(r'^modify$', isight.modify),
    # adapter/isight get
    url(r'^get$', isight.get),
    # adapter/isght detail
    url(r'^detail/', include(ctirs.adapter.isight.detail.urls)),
]
