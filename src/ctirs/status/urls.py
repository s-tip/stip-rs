from django.conf.urls import url, include
import ctirs.status.views as status
import ctirs.status.ajax.urls

urlpatterns = [
    url(r'^$', status.top, name='status'),
    url(r'^delete/$', status.delete),
    url(r'^ajax/', include(ctirs.status.ajax.urls)),
]
