# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.poll.views as poll

urlpatterns = [
    # poll top
    url(r'^$', poll.top),
    # poll detail
    url(r'^(?P<id_>\S+)/start$', poll.start),
    url(r'^(?P<taxii_id>\S+)/objects/(?P<object_id>\S+)/versions/$', poll.versions),
    # poll detail
    url(r'^(?P<id_>\S+)$', poll.detail),
]
