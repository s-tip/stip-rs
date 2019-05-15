# -*- coding: utf-8 -*-
import mongoengine
from subprocess import Popen
from django.shortcuts import render
from ctirs.core.common import get_text_field_value, get_common_replace_dict
from ctirs.error.views import error_page,error_page_no_view_permission, error_page_inactive
from django.contrib.auth.decorators import login_required
from ctirs.core.mongo.documents import TaxiiServers

def get_taxii_server_create_setting_name(request):
    return get_text_field_value(request,'setting_name',default_value='')

def get_taxii_server_create_collection_name(request):
    return get_text_field_value(request,'colleciton_name',default_value='')

def get_taxii_server_delete_id(request):
    return get_text_field_value(request,'id',default_value='')

@login_required
def top(request):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        replace_dict = get_taxii_server_common_replace_dict(request)
        #レンダリング
        return render(request,'taxii_server.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def reboot(request):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        #サービス再起動
        restart_taxii_server()
        replace_dict = get_taxii_server_common_replace_dict(request)
        replace_dict['reboot_info_msg'] = 'Reboot Success!!'
        #レンダリング
        return render(request,'taxii_server.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)
    
def restart_taxii_server():    
    #サービス再起動
    p = Popen(['supervisorctl','restart','stip-taxii-server'])
    p.wait()
    return

@login_required
def create(request):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        setting_name = get_taxii_server_create_setting_name(request)
        collection_name = get_taxii_server_create_collection_name(request)
        replace_dict = get_taxii_server_common_replace_dict(request)
        try:
            TaxiiServers.create(setting_name,collection_name)
            replace_dict['create_info_msg'] = 'Create Success!!'
        except mongoengine.NotUniqueError:
            replace_dict['create_error_msg'] = 'Duplicate Value (Setting Name or Collection Name)'
        #レンダリング
        return render(request,'taxii_server.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def delete(request):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        id_ = get_taxii_server_delete_id(request)
        replace_dict = get_taxii_server_common_replace_dict(request)
        ts = TaxiiServers.objects.get(id=id_)
        ts.delete()
        replace_dict['create_info_msg'] = 'Delete Success!!'
        #レンダリング
        return render(request,'taxii_server.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)
    
def get_taxii_server_common_replace_dict(request):
    replace_dict = get_common_replace_dict(request)
    replace_dict['taxii_servers'] = TaxiiServers.objects.all()
    return replace_dict
