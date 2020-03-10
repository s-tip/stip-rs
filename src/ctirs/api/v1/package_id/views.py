from django.http import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
import ctirs.api as api_root
from ctirs.core.mongo.documents_stix import StixFiles
from ctirs.api.v1.gv.views import get_matched_packages

# STIXファイル情報取得/削除
# /api/v1/stix_files_package_id/<package_id>
@csrf_exempt
def stix_files_package_id(request, package_id):
    # apikey認証
    ctirs_auth_user = api_root.authentication(request)
    if ctirs_auth_user is None:
        return api_root.error(Exception('You have no permission for this operation.'))
    try:
        if request.method == 'GET':
            # STIX ファイル情報取得
            return get_stix_file_package_id_document_info(request, package_id)
        elif request.method == 'DELETE':
            # STIX ファイル情報削除
            delete_stix_file_package_id_document_info(package_id)
            return api_root.get_delete_normal_status()
        else:
            return HttpResponseNotAllowed(['GET', 'DELETE'])
    except Exception as e:
        return api_root.error(e)


# STIX ファイル情報取得
# GET /api/v1/stix_files_package_id/<package_id>
def get_stix_file_package_id_document_info(request, package_id):
    try:
        doc = StixFiles.objects.get(package_id=package_id)
        return api_root.get_rest_api_document_info(doc)
    except Exception as _:
        return api_root.error(Exception('The specified id not found.'))


# STIX ファイル情報削除
# DELETE /api/v1/stix_files_package_id/<package_id>
def delete_stix_file_package_id_document_info(package_id):
    try:
        api_root.delete_stix_related_document(package_id=package_id)
    except Exception as e:
        return api_root.error(e)


# STIX ファイル取得
# GET /api/v1/stix_files_package_id/<package_id>/stix
def stix_files_package_id_stix(request, package_id):
    # apikey認証
    ctirs_auth_user = api_root.authentication(request)
    if ctirs_auth_user is None:
        return api_root.error(Exception('You have no permission for this operation.'))
    try:
        doc = StixFiles.objects.get(package_id=package_id)
        return api_root.get_rest_api_document_content(doc)
    except Exception as e:
        return api_root.error(e)


# 関連 CTI 取得
# GET /api/v1/stix_files_package_id/<package_id>/related_packages
def stix_files_package_id_related_packages(request, package_id):
    # apikey認証
    ctirs_auth_user = api_root.authentication(request)
    if ctirs_auth_user is None:
        return api_root.error(Exception('You have no permission for this operation.'))
    try:
        ret = get_matched_packages(package_id)
        return JsonResponse(ret, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_root.error(e)
