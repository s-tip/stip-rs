# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url, include
import ctirs.dashboard.views as dashboard
import ctirs.dashboard.ajax.urls

urlpatterns = [
    # dashboard top
    url(r'^$', dashboard.top),
    # dashboard ajax
    url(r'^ajax/', include(ctirs.dashboard.ajax.urls)),
]
