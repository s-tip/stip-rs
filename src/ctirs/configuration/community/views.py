# -*- coding: utf-8 -*-
#import os
from django.shortcuts import render, redirect
from ctirs.core.common import get_text_field_value, get_common_replace_dict
from ctirs.error.views import error_page,error_page_no_view_permission, error_page_free_format, error_page_inactive
from django.contrib.auth.decorators import login_required
from ctirs.core.mongo.documents import Communities,Webhooks

def get_configuration_community_create_community_name(request):
    return get_text_field_value(request,'name',default_value='')
def get_configuration_community_delete_community_id(request):
    return get_text_field_value(request,'community_id',default_value='')

def get_configuration_community_modify_community_id(request):
    return get_text_field_value(request,'community_id',default_value=None)
def get_configuration_community_modify_community_name(request):
    return get_text_field_value(request,'community_name',default_value=None)

def get_configuration_community_add_webhook_community_id(request):
    return get_text_field_value(request,'community_id',default_value=None)
def get_configuration_community_add_webhook_url(request):
    return get_text_field_value(request,'url',default_value=None)

def get_configuration_community_delete_webhook_community_id(request):
    return get_text_field_value(request,'community_id',default_value=None)
def get_configuration_community_delete_webhook_webhook_id(request):
    return get_text_field_value(request,'webhook_id',default_value=None)

@login_required
def top(request):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        replace_dict = get_common_replace_dict(request)
        replace_dict['communities'] = Communities.objects.all()
        #レンダリング
        return render(request,'community.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def create(request):
    if request.method != 'POST':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        name = get_configuration_community_create_community_name(request)
        if(name == None or len(name) == 0):
            return error_page_free_format(request,'No Community Name.')
        
        #community初期化処理
        try:
            Communities.init_community(name)
        except Exception as e:
            return error_page_free_format(request,e.message)

        #結果返却
        replace_dict = get_common_replace_dict(request)
        replace_dict['communities'] = Communities.objects.all()
        replace_dict['info_msg'] = 'Create Success!!'
        #レンダリング
        return render(request,'community.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def delete(request):
    if request.method != 'GET':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        community_id = get_configuration_community_delete_community_id(request)
        if(community_id == None or len(community_id) == 0):
            return error_page_free_format(request,'No Community ID.')
        u = Communities.objects.get(id = community_id)
        u.delete()
        replace_dict = get_common_replace_dict(request)
        replace_dict['communities'] = Communities.objects.all()
        replace_dict['info_msg'] = 'Delete Success!!'
        #レンダリング
        return render(request,'community.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def detail(request,mongo_id):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        replace_dict = get_common_replace_dict(request)
        replace_dict['community'] = Communities.objects.get(id=mongo_id)
        #レンダリング
        return render(request,'community_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def modify(request):
    #POST以外はエラー
    if request.method != 'POST':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    #community_id取得
    community_id = get_configuration_community_modify_community_id(request)
    #community_name取得
    community_name = get_configuration_community_modify_community_name(request)
    if ((community_id is None) or (community_name is None)):
        return error_page_free_format(request,'invalid arguments.')
    try:
        c = Communities.objects.get(id=community_id)
        c.name = community_name
        c.save()
        #communityトップページ返却
        return redirect('/configuration/community/')
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def add_webhook(request):
    #POST以外はエラー
    if request.method != 'GET':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    #community_id取得
    community_id = get_configuration_community_add_webhook_community_id(request)
    #url取得
    url = get_configuration_community_add_webhook_url(request)
    if ((community_id is None) or (url is None)):
        return error_page_free_format(request,'invalid arguments.')
    try:
        #webhook作成
        webhook = Webhooks()
        webhook.url = url
        webhook.save()
        #communityに追加
        c = Communities.objects.get(id=community_id)
        c.webhooks.append(webhook)
        c.save()
        replace_dict = get_common_replace_dict(request)
        replace_dict['community'] = c
        #レンダリング
        return render(request,'community_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def delete_webhook(request):
    #POST以外はエラー
    if request.method != 'GET':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    #community_id取得
    community_id = get_configuration_community_delete_webhook_community_id(request)
    #webhook_id取得
    webhook_id = get_configuration_community_delete_webhook_webhook_id(request)
    if ((community_id is None) or (webhook_id is None)):
        return error_page_free_format(request,'invalid arguments.')
    try:
        #Webhookドキュメント取得
        w = Webhooks.objects.get(id=webhook_id)
        #communityドキュメント取得
        c = Communities.objects.get(id=community_id)
        #webhooksリストからwebhookを削除
        c.webhooks.remove(w)
        c.save()
        replace_dict = get_common_replace_dict(request)
        replace_dict['community'] = c
        #レンダリング
        return render(request,'community_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)
