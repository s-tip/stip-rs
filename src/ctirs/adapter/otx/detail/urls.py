# -*- coding: utf-8 -*-
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.adapter.otx.detail.views as detail

urlpatterns = [
    #adapter/otx/detail resume
    url(r'^resume/(?P<job_id>\S+)$', detail.resume),
    #adapter/otx/detail pause
    url(r'^pause/(?P<job_id>\S+)$', detail.pause),
    #adapter/otx/detail remove
    url(r'^remove/(?P<job_id>\S+)$', detail.remove),
    #adapter/otx/detail create
    url(r'^create$', detail.create),
    #adapter/otx/detail interval
    url(r'^interval$', detail.interval),
    #adapter/otx/detail top
    url(r'^$', detail.top),
]