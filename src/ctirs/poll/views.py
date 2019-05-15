# -*- coding: utf-8 -*-
import pytz
import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ctirs.core.common import get_text_field_value, get_common_replace_dict
from ctirs.error.views import error_page, error_page_inactive
from ctirs.core.mongo.documents import TaxiiClients
from ctirs.core.taxii.taxii import Client

def get_start_start(request):
    return get_text_field_value(request,'poll_start',default_value=None)

def get_start_end(request):
    return get_text_field_value(request,'poll_end',default_value=None)

@login_required
def top(request):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    try:
        replace_dict = get_common_replace_dict(request)
        replace_dict['taxii_clients'] = TaxiiClients.objects.all()
        #レンダリング
        return render(request,'poll.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def detail(request,id_):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    try:
        replace_dict = get_common_replace_dict(request)
        replace_dict['taxii'] = TaxiiClients.objects.get(id=id_)
        #レンダリング
        return render(request,'poll_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

#formの日時フォーマット文字列からdatetime型に変換して返却
def get_datetime_from_string(str_):
    if str_ is None:
        return None
    return datetime.datetime.strptime(str_,'%Y/%m/%d %H:%M:%S').replace(tzinfo=pytz.utc)

@login_required
def start(request,id_):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    start = get_datetime_from_string(get_start_start(request))
    end = get_datetime_from_string(get_start_end(request))
    try:
        cl = Client(taxii_id = id_)
        cl.set_start_time(start)
        cl.set_end_time(end)
        count = cl.poll()
        replace_dict = get_common_replace_dict(request)
        replace_dict['taxii'] = TaxiiClients.objects.get(id=id_)
        replace_dict['info_msg'] =  'Poll end successfully!! (Get %d stix files.)' % (count)
        #レンダリング
        return render(request,'poll_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)
