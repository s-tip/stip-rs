import datetime
import pytz
from mongoengine import DoesNotExist
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.models.rs.models import STIPUser
from ctirs.error.views import error_page, error_page_no_view_permission, error_page_free_format, error_page_inactive
from ctirs.core.mongo.documents import MispAdapter, Communities
from ctirs.core.adapter.misp.download.control import MispAdapterDownloadControl

misp = MispAdapterDownloadControl()


def get_adapter_misp_modify_url(request):
    return get_text_field_value(request, 'url', default_value='')


def get_adapter_misp_modify_apikey(request):
    return get_text_field_value(request, 'apikey', default_value='')


def get_adapter_misp_modify_identity(request):
    return get_text_field_value(request, 'identity', default_value='')


def get_adapter_misp_modify_stix_id_prefix(request):
    return get_text_field_value(request, 'stix_id_prefix', default_value='')


def get_adapter_misp_modify_community_id(request):
    return get_text_field_value(request, 'community_id', default_value=None)


def get_adapter_misp_modify_uploader_id(request):
    return get_text_field_value(request, 'uploader_id', default_value=None)


def get_adapter_misp_get_start_date(request):
    return get_text_field_value(request, 'start_date', default_value=None)


def get_adapter_misp_get_end_date(request):
    return get_text_field_value(request, 'end_date', default_value=None)


def get_adapter_misp_get_published_only(request):
    return (get_text_field_value(request, 'published_only', default_value='"false') == 'published_only')


def get_adapter_misp_get_stix_version(request):
    return get_text_field_value(request, 'stix_version', default_value='1.2')


# replace辞書取得
def get_replace_dict():
    replace_dict = {}
    replace_dict['communities'] = Communities.objects.all()
    replace_dict['users'] = STIPUser.objects.all()
    return get_misp_dict(replace_dict)


# misp辞書取得
def get_misp_dict(replace_dict):
    replace_dict['misp'] = MispAdapter.get()
    # communityが削除されている場合はNoneを格納する
    try:
        if replace_dict['misp'].community is None:
            replace_dict['misp'].community = None
    except DoesNotExist:
        replace_dict['misp'].community = None
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
        return render(request, 'misp.html', replace_dict)
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
        url = get_adapter_misp_modify_url(request)
        apikey = get_adapter_misp_modify_apikey(request)
        stix_id_prefix = get_adapter_misp_modify_stix_id_prefix(request)
        identity = get_adapter_misp_modify_identity(request)
        community_id = get_adapter_misp_modify_community_id(request)
        uploader_id = int(get_adapter_misp_modify_uploader_id(request))
        published_only = get_adapter_misp_get_published_only(request)
        stix_version = get_adapter_misp_get_stix_version(request)
        # 設定更新
        # url は sheme と fqdn 名までなので END_POINT を追加する
        MispAdapter.modify_settings(url, apikey, stix_id_prefix, identity, community_id, uploader_id, published_only, stix_version)
        # レンダリング
        replace_dict = get_replace_dict()
        replace_dict['info_msg_modify'] = 'Modify Success!!'
        return render(request, 'misp.html', replace_dict)
    except Exception:
        # エラーページ
        return error_page(request)


def get(request):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    try:
        start_str = get_adapter_misp_get_start_date(request)
        end_str = get_adapter_misp_get_end_date(request)
        try:
            start_date = _get_datetime_from_str(start_str)
        except BaseException:
            # parse不能時は指定なしと同義
            start_date = None
        try:
            end_date = _get_datetime_from_str(end_str)
        except BaseException:
            # parse不能時は指定なしと同義
            end_date = None
        count = misp.get_misp_stix(from_dt=start_date, to_dt=end_date, identity=MispAdapter.get().identity)
        # レンダリング
        replace_dict = get_replace_dict()
        replace_dict['info_msg_get'] = 'Get by Misp Adapter successfully!! (Get %d stix files.)' % (count)
        return render(request, 'misp.html', replace_dict)
    except Exception:
        # エラーページ
        return error_page(request)


# 時間文字列はYYYY/MM/DD datetimeに変換
def _get_datetime_from_str(s):
    return datetime.datetime.strptime(s, '%Y/%m/%d').replace(tzinfo=pytz.utc)
