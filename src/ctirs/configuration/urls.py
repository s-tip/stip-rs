# -*- coding: utf-8 -*-
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url, include
import ctirs.configuration.community.urls
import ctirs.configuration.user.urls
import ctirs.configuration.taxii_client.urls
import ctirs.configuration.taxii_server.urls
import ctirs.configuration.system.urls
import ctirs.configuration.mongo.urls

urlpatterns = [
    #configuration/Community
    url(r'^community/', include(ctirs.configuration.community.urls)),
    #configuration/User
    url(r'^user/', include(ctirs.configuration.user.urls)),
    #configuration/Taxii Client
    url(r'^taxii_client/', include(ctirs.configuration.taxii_client.urls)),
    #configuration/Taxii Server
    url(r'^taxii_server/', include(ctirs.configuration.taxii_server.urls)),
    #configuration/system
    url(r'^system/', include(ctirs.configuration.system.urls)),
    #configuration/mongo
    url(r'^mongo/', include(ctirs.configuration.mongo.urls)),
]
