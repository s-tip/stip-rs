import pytz
import datetime
from mongoengine.errors import DoesNotExist
from django.http import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
import ctirs.api as api_root
from ctirs.core.mongo.documents import Communities, Vias
from ctirs.core.mongo.documents_stix import StixFiles
from ctirs.core.common import get_text_field_value
from ctirs.upload.views import upload_common


def get_api_get_stix_files_community(request):
    return get_text_field_value(request, 'community', default_value=None)


def get_api_get_stix_files_start(request):
    return get_text_field_value(request, 'start', default_value=None)


def get_api_get_stix_files_end(request):
    return get_text_field_value(request, 'end', default_value=None)

# /api/v1/stix_files
# GET/POSTの受付
@csrf_exempt
def stix_files(request):
    try:
        if request.method == 'GET':
            # stix_file一覧取得
            return get_stix_files(request)
        elif request.method == 'POST':
            # stix_file追加
            return upload_stix_file(request)
        else:
            return HttpResponseNotAllowed(['GET', 'POST'])
    except Exception as e:
        return api_root.error(e)

# 引数の日時文字列からdatetimeオブジェクトを作成


def get_datetime_from_argument(s):
    return datetime.datetime.strptime(s, '%Y%m%d%H%M%S').replace(tzinfo=pytz.utc)

# stix_file一覧取得
# GET /api/v1/stix_files


def get_stix_files(request):
    # apikey認証
    ctirs_auth_user = api_root.authentication(request)
    if ctirs_auth_user is None:
        return api_root.error(Exception('You have no permission for this operation.'))

    l = []
    query = {}
    # community filter
    community = get_api_get_stix_files_community(request)
    if community is not None:
        try:
            query['input_community'] = Communities.objects.get(name=community)
        except DoesNotExist:
            return api_root.error(Exception('The specified community not found.'))

    # start filter
    # YYYYMMDDHHMMSS形式
    start = get_api_get_stix_files_start(request)
    if start is not None:
        try:
            d = get_datetime_from_argument(start)
            query['created__gt'] = d
        except Exception as _:
            return api_root.error(Exception('Time string format invalid.'))

    # end filter
    # YYYYMMDDHHMMSS形式
    end = get_api_get_stix_files_end(request)
    if end is not None:
        try:
            d = get_datetime_from_argument(end)
            query['created__lt'] = d
        except Exception as _:
            return api_root.error(Exception('Time string format invalid.'))

    # 検索
    for stix_files in StixFiles.objects.filter(**query):
        try:
            l.append(stix_files.get_rest_api_document_info())
        except DoesNotExist:
            pass
    return JsonResponse(l, safe=False)

# STIXファイル追加
# POST /api/v1/stix_files


def upload_stix_file(request):
    # apikey認証
    ctirs_auth_user = api_root.authentication(request)
    if ctirs_auth_user is None:
        return api_root.error(Exception('You have no permission for this operation.'))
    try:
        # viaを取得
        via = Vias.get_via_rest_api_upload(uploader=ctirs_auth_user.id)
        upload_common(request, via)
        return api_root.get_put_normal_status()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_root.error(e)


# STIXファイル情報取得/削除
# /api/v1/stix_files/<id_>
@csrf_exempt
def stix_files_id(request, id_):
    # apikey認証
    ctirs_auth_user = api_root.authentication(request)
    if ctirs_auth_user is None:
        return api_root.error(Exception('You have no permission for this operation.'))
    try:
        if request.method == 'GET':
            # STIX ファイル情報取得
            return get_stix_file_document_info(request, id_)
        elif request.method == 'DELETE':
            # STIX ファイル情報削除
            delete_stix_file_document_info(id_)
            return api_root.get_delete_normal_status()
        else:
            return HttpResponseNotAllowed(['GET', 'DELETE'])
    except Exception as e:
        return api_root.error(e)

# STIX ファイル情報取得
# GET /api/v1/stix_files/<id_>


def get_stix_file_document_info(request, id_):
    try:
        doc = StixFiles.objects.get(id=id_)
        return api_root.get_rest_api_document_info(doc)
    except Exception as _:
        return api_root.error(Exception('The specified id not found.'))

# STIX ファイル情報削除
# DELETE /api/v1/stix_files/<id_>


def delete_stix_file_document_info(id_):
    try:
        api_root.delete_stix_document(id_=id_)
    except Exception as e:
        return api_root.error(e)

# STIX取得
# GET /api/v1/stix_files/<id>/stix


def stix_files_id_stix(request, id_):
    # apikey認証
    ctirs_auth_user = api_root.authentication(request)
    if ctirs_auth_user is None:
        return api_root.error(Exception('You have no permission for this operation.'))
    try:
        doc = StixFiles.objects.get(id=id_)
        return api_root.get_rest_api_document_content(doc)
    except DoesNotExist:
        return api_root.error(Exception('The specified id not found.'))
