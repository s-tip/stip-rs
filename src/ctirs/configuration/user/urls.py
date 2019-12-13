# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url, include
import ctirs.configuration.user.views as user
import ctirs.configuration.user.ajax.urls

urlpatterns = [
    # configuration/user top
    url(r'^$', user.top),
    # configuration/user create
    url(r'^create_user$', user.create),
    # configuration ajax
    url(r'^ajax/', include(ctirs.configuration.user.ajax.urls)),
]
