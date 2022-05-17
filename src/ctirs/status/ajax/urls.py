from django.conf.urls import url
import ctirs.status.ajax.views as ajax

urlpatterns = [
    url(r'^check/', ajax.check),
]
