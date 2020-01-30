# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url, include
import ctirs.configuration.user.views as user
import ctirs.configuration.user.ajax.urls

urlpatterns = [
    # configuration/user top
    url(r'^$', user.top),
    # configuration/user create
    url(r'^create_user$', user.create),
    # configuration/user change_password_top
    url(r'^change_password_top$', user.change_password_top),
    # configuration/user change_password
    url(r'^change_password$', user.change_password),
    # configuration ajax
    url(r'^ajax/', include(ctirs.configuration.user.ajax.urls)),
]
