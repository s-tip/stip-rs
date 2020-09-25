
# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url, include
import ctirs.profile.views as profile
import ctirs.profile.ajax.urls

urlpatterns = [
    # profile top
    url(r'^$', profile.top),
    # profile change_password
    url(r'^change_password$', profile.change_password, name='password_modified'),
    # profile change_screen_name
    url(r'^change_screen_name$', profile.change_screen_name),
    # profile ajax
    url(r'^ajax/', include(ctirs.profile.ajax.urls)),
]
