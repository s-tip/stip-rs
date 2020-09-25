from django.conf.urls import url
import ctirs.configuration.user.ajax.views as ajax

urlpatterns = [
    url(r'^change_auth$', ajax.change_auth),
    url(r'^change_active$', ajax.change_active),
    url(r'^unset_mfa$', ajax.unset_mfa),
]
