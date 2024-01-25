import traceback
from django.http import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
import ctirs.api as api_root
from ctirs.api.v1.decolators import api_key_auth
from ctirs.core.mongo.documents_stix import StixFiles
from ctirs.api.v1.gv.views import get_matched_packages


def common_error():
    msg = 'A system error has occurred. Please check the system log.'
    traceback.print_exc()
    return api_root.error(Exception(msg))


# /api/v1/stix_files_package_id/<package_id>
@csrf_exempt
@api_key_auth
def stix_files_package_id(request, package_id):
    try:
        if request.method == 'GET':
            return get_stix_file_package_id_document_info(request, package_id)
        elif request.method == 'DELETE':
            delete_stix_file_package_id_document_info(package_id)
            return api_root.get_delete_normal_status({'remove_package_id': package_id})
        else:
            return HttpResponseNotAllowed(['GET', 'DELETE'])
    except Exception:
        return common_error()


# GET /api/v1/stix_files_package_id/<package_id>
def get_stix_file_package_id_document_info(request, package_id):
    try:
        doc = StixFiles.objects.get(package_id=package_id)
        return api_root.get_rest_api_document_info(doc)
    except Exception:
        return api_root.error(Exception('The specified id not found.'))


# DELETE /api/v1/stix_files_package_id/<package_id>
def delete_stix_file_package_id_document_info(package_id):
    try:
        api_root.delete_stix_document(package_id=package_id)
    except Exception:
        return common_error()


# GET /api/v1/stix_files_package_id/<package_id>/stix
@api_key_auth
def stix_files_package_id_stix(request, package_id):
    try:
        doc = StixFiles.objects.get(package_id=package_id)
        return api_root.get_rest_api_document_content(doc)
    except Exception:
        return common_error()


# GET /api/v1/stix_files_package_id/<package_id>/related_packages
@api_key_auth
def stix_files_package_id_related_packages(request, package_id):
    try:
        ret = get_matched_packages(package_id)
        return JsonResponse(ret, safe=False)
    except Exception:
        return common_error()
