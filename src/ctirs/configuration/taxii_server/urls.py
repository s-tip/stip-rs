#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import include,url
import ctirs.configuration.taxii_server.detail.urls
import ctirs.configuration.taxii_server.views as taxii_server

urlpatterns = [
    #configuration/taxii_server top
    url(r'^$', taxii_server.top),
    #configuration/taxii_server reboot
    url(r'^reboot$', taxii_server.reboot),
    #configuration/taxii_server create
    url(r'^create$', taxii_server.create),
    #configuration/taxii_server delete
    url(r'^delete$', taxii_server.delete),
    #configuration/taxii_server detail
    url(r'^detail/', include(ctirs.configuration.taxii_server.detail.urls)),
]
