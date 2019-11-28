#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.taxii2_server.views as taxii

urlpatterns = [
    #taxii2 top
    url(r'^collections/(?P<id_>\S+)/objects/$', taxii.collections_objects),
    url(r'^collections/(?P<id_>\S+)/$', taxii.collections),
    url(r'^collections/$', taxii.collections_root),
    url(r'^$', taxii.top),
]
