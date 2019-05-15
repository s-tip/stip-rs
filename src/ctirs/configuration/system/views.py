# -*- coding: utf-8 -*-
from django.shortcuts import render
from ctirs.core.common import get_text_field_value, get_common_replace_dict
from ctirs.error.views import error_page,error_page_no_view_permission, error_page_free_format, error_page_inactive
from ctirs.models.rs.models import System
from django.contrib.auth.decorators import login_required
from ctirs.core.mongo.documents_stix import StixFiles

def get_configuration_system_communirty_root_dir(request):
    return get_text_field_value(request,'community_root_dir',default_value='')
def get_configuration_system_suffix_list_file_path(request):
    return get_text_field_value(request,'suffix_list_file_path',default_value='')
def get_configuration_system_http_proxy(request):
    return get_text_field_value(request,'http_proxy',default_value='')
def get_configuration_system_https_proxy(request):
    return get_text_field_value(request,'https_proxy',default_value='')

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
        return render(request,'system.html',get_success_replace_dict(request))
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
        community_root_dir = get_configuration_system_communirty_root_dir(request)
        suffix_list_file_path = get_configuration_system_suffix_list_file_path(request)
        http_proxy = get_configuration_system_http_proxy(request)
        https_proxy = get_configuration_system_https_proxy(request)
        #Config更新
        System.objects.modify(community_root_dir,suffix_list_file_path,http_proxy,https_proxy)
        #レンダリング
        replace_dict = get_success_replace_dict(request)
        replace_dict['info_msg'] = 'Modify Success!!'
        return render(request,'system.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def rebuild_cache(request):
    if request.method != 'GET':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        #レンダリング
        StixFiles.rebuild_cache()
        replace_dict = get_success_replace_dict(request)
        replace_dict['info_msg'] = 'Rebuild Success!!'
        return render(request,'system.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

def get_success_replace_dict(request):
    replace_dict = get_common_replace_dict(request)
    try:
        replace_dict['system'] = System.objects.get()
    except:
        replace_dict['system'] = None
    return replace_dict
