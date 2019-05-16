# -*- coding: utf-8 -*-
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url,include
import ctirs.configuration.community.views as community
import ctirs.configuration.community.ajax.urls

urlpatterns = [
    #configuration/community top
    url(r'^$', community.top),
    #configuration/community create
    url(r'^create/$', community.create),
    #configuration/community delete
    url(r'^delete/$', community.delete),
    #configuration/community detail
    url(r'^detail/(?P<mongo_id>\S+)$', community.detail),
    #configuration/community modify
    url(r'^modify/$', community.modify),
    #configuration/community add_webhook
    url(r'^add_webhook$', community.add_webhook),
    #configuration/community delete_webhook
    url(r'^delete_webhook$', community.delete_webhook),
    #configuration/community ajax
    url(r'^ajax/', include(ctirs.configuration.community.ajax.urls)),
]
