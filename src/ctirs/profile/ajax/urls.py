#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.profile.ajax.views as ajax

urlpatterns = [
    #profile change_api_key
    url(r'^change_api_key', ajax.change_api_key),
]
