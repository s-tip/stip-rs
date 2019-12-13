# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.configuration.mongo.views as mongo

urlpatterns = [
    # configuration/mongo top
    url(r'^$', mongo.top),
    # configuration/mongo modify
    url(r'^modify$', mongo.modify),
]
