#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.configuration.taxii_server.detail.views as detail

urlpatterns = [
    #configuration/taxii_server/modify
    url(r'^(?P<taxii_id>\S+)/modify$', detail.modify),
    #configuration/taxii_server/detail top
    url(r'^(?P<taxii_id>\S+)$', detail.top),
]
