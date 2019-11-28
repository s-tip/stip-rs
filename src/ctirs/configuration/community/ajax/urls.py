
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.configuration.community.ajax.views as ajax

urlpatterns = [
    #test_webhook
    url(r'^test_webhook$', ajax.test_webhook),
]

