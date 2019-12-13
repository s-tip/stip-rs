# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.adapter.misp.detail.views as detail

urlpatterns = [
    # adapter/misp/detail resume
    url(r'^resume/(?P<job_id>\S+)$', detail.resume),
    # adapter/misp/detail pause
    url(r'^pause/(?P<job_id>\S+)$', detail.pause),
    # adapter/misp/detail remove
    url(r'^remove/(?P<job_id>\S+)$', detail.remove),
    # adapter/misp/detail create
    url(r'^create$', detail.create),
    # adapter/misp/detail interval
    url(r'^interval$', detail.interval),
    # adapter/misp/detail top
    url(r'^$', detail.top),
]
