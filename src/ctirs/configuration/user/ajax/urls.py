#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.configuration.user.ajax.views as ajax

urlpatterns = [
    #configuration change_auth
    url(r'^change_auth$', ajax.change_auth),
]
