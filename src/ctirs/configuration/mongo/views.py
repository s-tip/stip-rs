# -*- coding: utf-8 -*-
from django.shortcuts import render
from ctirs.core.common import get_text_field_value, get_common_replace_dict
from ctirs.error.views import error_page,error_page_no_view_permission, error_page_free_format, error_page_inactive
from django.contrib.auth.decorators import login_required
from ctirs.models.rs.models import MongoConfig

def get_configuration_mongo_host(request):
    return get_text_field_value(request,'host',default_value='')
def get_configuration_mongo_port(request):
    return int(get_text_field_value(request,'port',default_value=''))
def get_configuration_mongo_db(request):
    return get_text_field_value(request,'db',default_value='')

@login_required
def top(request):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        #レンダリング
        return render(request,'mongo.html',get_success_replace_dict(request))
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def modify(request):
    if request.method != 'POST':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        host = get_configuration_mongo_host(request)
        port = get_configuration_mongo_port(request)
        db = get_configuration_mongo_db(request)
        #Config更新
        MongoConfig.objects.modify(host,port,db)
        #レンダリング
        replace_dict = get_success_replace_dict(request)
        replace_dict['info_msg'] = 'Modify Success!!'
        return render(request,'mongo.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

def get_success_replace_dict(request):
    replace_dict = get_common_replace_dict(request)
    replace_dict['mongo'] = MongoConfig.objects.get()
    return replace_dict
