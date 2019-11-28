#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import include,url
import ctirs.configuration.taxii_client.detail.urls
import ctirs.configuration.taxii_client.views as taxii_client

urlpatterns = [
    #configuration/taxii_client top
    url(r'^$', taxii_client.top),
    #configuration/taxii_client create
    url(r'^create$', taxii_client.create),
    #configuration/taxii_client delete
    url(r'^delete$', taxii_client.delete),
    #configuration/taxii_client detail
    url(r'^detail/', include(ctirs.configuration.taxii_client.detail.urls)),
]
