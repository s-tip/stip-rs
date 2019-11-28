
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
import ctirs.api.v1.urls
from django.conf.urls import url,include

urlpatterns = [
    #v1
    url(r'^v1/', include(ctirs.api.v1.urls)),
]
