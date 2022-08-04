try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.list.ajax.views as ajax

urlpatterns = [
    # list/ajax get_table_info
    _url(r'^get_table_info$', ajax.get_table_info),
    # list/publish get_table_info
    _url(r'^publish$', ajax.publish),
    # list/publish get_table_info
    _url(r'^misp_import$', ajax.misp_import),
]
