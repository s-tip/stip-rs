# -*- coding: utf-8 -*-
import datetime
import pytz
import calendar
from mongoengine import DoesNotExist
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ctirs.models.rs.models import STIPUser
from ctirs.core.common import get_text_field_value
from ctirs.error.views import error_page,error_page_no_view_permission, error_page_free_format, error_page_inactive
from ctirs.core.mongo.documents import isightAdapter,Communities
from ctirs.core.adapter.isight.isight import iSightAdapterControl

isight = iSightAdapterControl()

def get_adapter_isight_modify_public_key(request):
    return get_text_field_value(request,'public_key',default_value='')

def get_adapter_isight_modify_private_key(request):
    return get_text_field_value(request,'private_key',default_value='')

def get_adapter_isight_modify_community_id(request):
    return get_text_field_value(request,'community_id',default_value=None)

def get_adapter_isight_modify_uploader_id(request):
    return get_text_field_value(request,'uploader_id',default_value=None)

def get_adapter_isight_get_start_time(request):
    return get_text_field_value(request,'start_time',default_value=None)

def get_adapter_isight_get_end_time(request):
    return get_text_field_value(request,'end_time',default_value=None)

#replace辞書取得
def get_replace_dict():
    replace_dict = {}
    replace_dict['communities'] = Communities.objects.all()
    replace_dict['users'] = STIPUser.objects.all()
    return get_isight_dict(replace_dict)

#isight辞書取得
def get_isight_dict(replace_dict):
    replace_dict['isight'] = isightAdapter.get()
    #communityが削除されている場合はNoneを格納する
    try:
        if replace_dict['isight'].community is None:
            replace_dict['isight'].community = None
    except DoesNotExist:
            replace_dict['isight'].community = None
    return replace_dict

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
        replace_dict = get_replace_dict()
        return render(request,'isight.html',replace_dict)
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
    try:
        public_key = get_adapter_isight_modify_public_key(request)
        private_key = get_adapter_isight_modify_private_key(request)
        community_id = get_adapter_isight_modify_community_id(request)
        uploader_id = int(get_adapter_isight_modify_uploader_id(request))
        #設定更新
        isightAdapter.modify_settings(public_key,private_key,community_id,uploader_id)
        #レンダリング
        replace_dict = get_replace_dict()
        replace_dict['info_msg_modify'] = 'Modify Success!!'
        return render(request,'isight.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

def get(request):
    if request.method != 'GET':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    try:
        start_str = get_adapter_isight_get_start_time(request)
        end_str = get_adapter_isight_get_end_time(request)
        try:
            start_time = _get_epoch_time(start_str)
        except:
            #parse不能時は指定なしと同義
            start_time = None
        try:
            end_time = _get_epoch_time(end_str)
        except:
            #parse不能時は指定なしと同義
            end_time = None
        count = isight.get_isight_stix(start_time=start_time,end_time=end_time)
        #レンダリング
        replace_dict = get_replace_dict()
        replace_dict['info_msg_get'] =  'Get by iSight Partners Adapter successfully!! (Get %d stix files.)' % (count)
        return render(request,'isight.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

#時間文字列はYYYY/MM/DD HH:MM:SSをepoch_timeに変換
def _get_epoch_time(s):
    dt = datetime.datetime.strptime(s,'%Y/%m/%d %H:%M:%S').replace(tzinfo=pytz.utc)
    return calendar.timegm(dt.timetuple())
