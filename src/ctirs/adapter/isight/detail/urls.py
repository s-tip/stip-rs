#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.adapter.isight.detail.views as detail

urlpatterns = [
    #adapter/isight/detail resume
    url(r'^resume/(?P<job_id>\S+)$', detail.resume),
    #adapter/isight/detail pause
    url(r'^pause/(?P<job_id>\S+)$', detail.pause),
    #adapter/isight/detail remove
    url(r'^remove/(?P<job_id>\S+)$', detail.remove),
    #adapter/isight/detail create
    url(r'^create$', detail.create),
    #adapter/isight/detail interval
    url(r'^interval$', detail.interval),
    #adapter/isight/detail top
    url(r'^$', detail.top),
]
