
# URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.api.v1.sns.views as sns

urlpatterns = [
    # feeds取得
    url(r'feeds$', sns.feeds),
    # tags取得
    url(r'feeds/tags$', sns.tags),
    # attaches(添付ファイル取得)
    url(r'attaches$', sns.attaches),
    # related_packages(comment,like,unlike取得)
    url(r'related_packages$', sns.related_packages),
    # content(original STIX 取得)
    url(r'content$', sns.content),
    # comments(comments 取得)
    url(r'comments$', sns.comments),
    # likers(likers 取得)
    url(r'likers$', sns.likers),
    # share_misp
    url(r'share_misp$', sns.share_misp),
    # query取得
    url(r'query$', sns.query),
]
