import datetime
import pytz
from mongoengine import DoesNotExist
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.models.rs.models import STIPUser
from ctirs.error.views import error_page, error_page_no_view_permission, error_page_free_format, error_page_inactive
from ctirs.core.mongo.documents import OtxAdapter, Communities
from ctirs.core.adapter.otx.otx import OtxAdapterControl

otx = OtxAdapterControl()


def get_adapter_otx_modify_apikey(request):
    return get_text_field_value(request, 'apikey', default_value='')


def get_adapter_otx_modify_community_id(request):
    return get_text_field_value(request, 'community_id', default_value=None)


def get_adapter_otx_modify_uploader_id(request):
    return get_text_field_value(request, 'uploader_id', default_value=None)


def get_adapter_otx_get_start(request):
    return get_text_field_value(request, 'start', default_value=None)


# replace辞書取得
def get_replace_dict():
    replace_dict = {}
    replace_dict['communities'] = Communities.objects.all()
    replace_dict['users'] = STIPUser.objects.all()
    return get_otx_dict(replace_dict)


# otx辞書取得
def get_otx_dict(replace_dict):
    replace_dict['otx'] = OtxAdapter.get()
    # communityが削除されている場合はNoneを格納する
    try:
        if replace_dict['otx'].community is None:
            replace_dict['otx'].community = None
    except DoesNotExist:
        replace_dict['otx'].community = None
    return replace_dict


@login_required
def top(request):
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        # レンダリング
        replace_dict = get_replace_dict()
        return render(request, 'otx.html', replace_dict)
    except Exception:
        # エラーページ
        return error_page(request)


@login_required
def modify(request):
    if request.method != 'POST':
        return error_page_free_format(request, 'invalid method')
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    try:
        apikey = get_adapter_otx_modify_apikey(request)
        community_id = get_adapter_otx_modify_community_id(request)
        uploader_id = int(get_adapter_otx_modify_uploader_id(request))
        # 設定更新
        OtxAdapter.modify_settings(apikey, community_id, uploader_id)
        # レンダリング
        replace_dict = get_replace_dict()
        replace_dict['info_msg_modify'] = 'Modify Success!!'
        return render(request, 'otx.html', replace_dict)
    except Exception:
        # エラーページ
        return error_page(request)


@login_required
def get(request):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    try:
        start_str = get_adapter_otx_get_start(request)
        try:
            start = datetime.datetime.strptime(start_str, '%Y/%m/%d %H:%M:%S').replace(tzinfo=pytz.utc).isoformat()
        except BaseException:
            # parse不能時は指定なしと同義
            start = None
        count = otx.get_otx_stix(start)
        # レンダリング
        replace_dict = get_replace_dict()
        replace_dict['info_msg_get'] = 'Get by OTX Adapter successfully!! (Get %d stix files.)' % (count)
        return render(request, 'otx.html', replace_dict)
    except Exception:
        # エラーページ
        return error_page(request)
