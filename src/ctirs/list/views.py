import os
import traceback
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from ctirs.error.views import error_page_inactive, error_page_no_view_permission, error_page_free_format, error_page
from ctirs.core.common import get_common_replace_dict, get_text_field_value
from ctirs.core.mongo.documents_stix import StixFiles


def get_list_delete_id(request):
    return get_text_field_value(request, 'id', default_value=None)


def get_list_download_id(request):
    return get_text_field_value(request, 'id', default_value=None)


def get_list_download_version(request):
    return get_text_field_value(request, 'version', default_value=None)


@login_required
def top(request):
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    replace_dict = get_common_replace_dict(request)
    return render(request, 'list.html', replace_dict)


@login_required
def delete(request):
    if request.method != 'GET':
        return error_page_free_format(request, 'Invalid HTTP Method.')
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # 削除対象 ID が ,区切り文字列で渡る
    ids = get_list_delete_id(request).split(',')
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        for id_ in ids:
            # mongoから該当レコード削除
            origin_path = StixFiles.delete_by_id(id_)
            # ファイル削除
            if os.path.exists(origin_path):
                os.remove(origin_path)
        return top(request)
    except Exception:
        return error_page(request)
    return top(request)


@login_required
def download(request):
    if request.method != 'GET':
        return error_page_free_format(request, 'Invalid HTTP Method.')
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    id_ = get_list_download_id(request)
    version = get_list_download_version(request)

    # 該当レコード検索
    doc = StixFiles.objects.get(id=id_)
    # 格納バージョンと指定バーションが一致
    if version == doc.version:
        # そのままダウンロード
        # response作成
        response = HttpResponse(doc.content.read())
    else:
        try:
            # 変換する
            if doc.version == '2.0':
                # 2.0 -> 1.2
                dest = doc.get_slide_1_x()
            else:
                # 1.2 -> 2.0
                dest = doc.get_elevate_2_x()
        except Exception as e:
            traceback.print_exc()
            return error_page_free_format(request, 'Can\'t Convert because of stix2library. ' + str(e.message))

        response = HttpResponse(dest)

    if version.startswith('1.'):
        # download version が 1.x
        response['Content-Type'] = 'application/xml'
        response['Content-Disposition'] = 'attachment; filename=%s.xml' % (id_)
    else:
        # download version が 2.x
        response['Content-Type'] = 'application/json'
        response['Content-Disposition'] = 'attachment; filename=%s.json' % (id_)

    return response
