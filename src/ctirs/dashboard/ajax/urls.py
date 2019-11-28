
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.dashboard.ajax.views as ajax

urlpatterns = [
    #get_stix_counts
    url(r'^get_stix_counts$', ajax.get_stix_counts),
]

