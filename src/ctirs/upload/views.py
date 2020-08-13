import tempfile
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.core.stix.regist import regist
from ctirs.core.mongo.documents import Communities, Vias
from ctirs.error.views import error_page, error_page_no_view_permission, error_page_inactive
from ctirs.core.common import get_common_replace_dict


def get_upload_upload_community_id(request):
    return get_text_field_value(request, 'community_id', default_value=None)


def get_upload_upload_community_name(request):
    return get_text_field_value(request, 'community_name', default_value=None)


def get_upload_upload_package_name(request):
    return get_text_field_value(request, 'package_name', default_value=None)


# filefieldからitem_name指定の値を取得。未定義時はNone
# list形式で返却
def get_file_field_value(request, item_name):
    try:
        return request.FILES.getlist(item_name)
    except MultiValueDictKeyError:
        return None


# STIXファイル取得/指定無時はNone/リストで返却される
def get_sharing_stix(request):
    return get_file_field_value(request, 'stix')


@login_required
def top(request):
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        replace_dict = get_common_replace_dict(request)
        replace_dict['communities'] = Communities.objects.all()
        # レンダリング
        return render(request, 'upload.html', replace_dict)
    except Exception:
        # エラーページ
        return error_page(request)


# web/rest api共通ファイルupload処理
def upload_common(request, via):
    # 引数取得
    community_id = get_upload_upload_community_id(request)
    community_name = get_upload_upload_community_name(request)
    package_name = get_upload_upload_package_name(request)
    stix = get_sharing_stix(request)[0]

    # stixファイルを一時ファイルに出力
    stix_file_path = tempfile.mktemp(suffix='.xml')
    with open(stix_file_path, 'wb+') as fp:
        for chunk in stix:
            fp.write(chunk)
    # Communityドキュメントを取得する
    if community_id is not None:
        community = Communities.objects.get(id=community_id)
    elif community_name is not None:
        community = Communities.objects.get(name=community_name)
    else:
        raise Exception('Invalid community id or name.')
    # 登録処理
    regist(stix_file_path, community, via, package_name=package_name)
    return


@login_required
def upload(request):
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    # post以外はエラー
    if request.method != 'POST':
        # エラー画面
        raise Exception('Invalid HTTP Method')
    try:
        # uploaderIDを取得する
        uploader = int(request.user.id)
        # viaを取得
        via = Vias.get_via_file_upload(uploader=uploader)
        # upload処理
        upload_common(request, via)
        replace_dict = get_common_replace_dict(request)
        return render(request, 'success.html', replace_dict)
    except Exception:
        return error_page(request)
