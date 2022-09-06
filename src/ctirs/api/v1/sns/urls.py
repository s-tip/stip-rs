try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.api.v1.sns.views as sns

urlpatterns = [
    # feeds取得
    _url(r'feeds$', sns.feeds),
    # tags取得
    _url(r'feeds/tags$', sns.tags),
    # attaches(添付ファイル取得)
    _url(r'attaches$', sns.attaches),
    # related_packages(comment,like,unlike取得)
    _url(r'related_packages$', sns.related_packages),
    # content(original STIX 取得)
    _url(r'content$', sns.content),
    # comments(comments 取得)
    _url(r'comments$', sns.comments),
    # likers(likers 取得)
    _url(r'likers$', sns.likers),
    # share_misp
    _url(r'share_misp$', sns.share_misp),
    # query取得
    _url(r'query$', sns.query),
]
