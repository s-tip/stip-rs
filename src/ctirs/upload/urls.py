# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import include, url
import ctirs.upload.views as upload

urlpatterns = [
    # upload top
    url(r'^$', upload.top),
    # upload post
    url(r'^post/$', upload.upload),
]
