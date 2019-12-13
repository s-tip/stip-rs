# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.configuration.taxii_client.detail.views as detail

urlpatterns = [
    # configuration/taxii_client/detail resume
    url(r'^(?P<taxii_id>\S+)/resume/(?P<job_id>\S+)$', detail.resume),
    # configuration/taxii_client/detail pause
    url(r'^(?P<taxii_id>\S+)/pause/(?P<job_id>\S+)$', detail.pause),
    # configuration/taxii_client/detail remove
    url(r'^(?P<taxii_id>\S+)/remove/(?P<job_id>\S+)$', detail.remove),
    # configuration/taxii_client/detail create
    url(r'^(?P<taxii_id>\S+)/create$', detail.create),
    # configuration/taxii_client/detail interval
    url(r'^(?P<taxii_id>\S+)/interval$', detail.interval),
    # configuration/taxii_client/detail top
    url(r'^(?P<taxii_id>\S+)$', detail.top),
]
