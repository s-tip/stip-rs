from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import path as _url
import ctirs.configuration.community.views as community
import ctirs.configuration.community.ajax.urls

urlpatterns = [
    # configuration/community top
    _url(r'^$', community.top),
    # configuration/community create
    _url(r'^create/$', community.create),
    # configuration/community delete
    _url(r'^delete/$', community.delete),
    # configuration/community detail
    _url(r'^detail/(?P<mongo_id>\S+)$', community.detail),
    # configuration/community modify
    _url(r'^modify/$', community.modify),
    # configuration/community add_webhook
    _url(r'^add_webhook$', community.add_webhook),
    # configuration/community delete_webhook
    _url(r'^delete_webhook$', community.delete_webhook),
    # configuration/community ajax
    _url(r'^ajax/', include(ctirs.configuration.community.ajax.urls)),
]
