import pytz
import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from django.http import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from stip.common import get_text_field_value
import ctirs.api as api_root
from ctirs.api.v1.decolators import api_key_auth
from ctirs.core.mongo.documents import Communities, Vias
from ctirs.core.mongo.documents_stix import StixFiles
from ctirs.upload.views import upload_common


def get_api_get_stix_files_community(request):
    return get_text_field_value(request, 'community', default_value=None)


def get_api_get_stix_files_start(request):
    return get_text_field_value(request, 'start', default_value=None)


def get_api_get_stix_files_end(request):
    return get_text_field_value(request, 'end', default_value=None)

# /api/v1/stix_files
@csrf_exempt
@api_key_auth
def stix_files(request):
    try:
        if request.method == 'GET':
            return get_stix_files(request)
        elif request.method == 'POST':
            return upload_stix_file(request)
        else:
            return HttpResponseNotAllowed(['GET', 'POST'])
    except Exception as e:
        return api_root.error(e)


def get_datetime_from_argument(s):
    return datetime.datetime.strptime(s, '%Y%m%d%H%M%S').replace(tzinfo=pytz.utc)


# GET /api/v1/stix_files
def get_stix_files(request):
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
    start = get_api_get_stix_files_start(request)
    if start is not None:
        try:
            d = get_datetime_from_argument(start)
            query['created__gt'] = d
        except Exception:
            return api_root.error(Exception('Time string format invalid.'))

    # end filter
    end = get_api_get_stix_files_end(request)
    if end is not None:
        try:
            d = get_datetime_from_argument(end)
            query['created__lt'] = d
        except Exception:
            return api_root.error(Exception('Time string format invalid.'))

    for stix_files in StixFiles.objects.filter(**query):
        try:
            l.append(stix_files.get_rest_api_document_info())
        except DoesNotExist:
            pass
    return JsonResponse(l, safe=False)


# POST /api/v1/stix_files
def upload_stix_file(request):
    ctirs_auth_user = api_root.authentication(request)
    if ctirs_auth_user is None:
        return api_root.error(Exception('You have no permission for this operation.'))
    try:
        via = Vias.get_via_rest_api_upload(uploader=ctirs_auth_user.id)
        upload_common(request, via)
        return api_root.get_put_normal_status()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_root.error(e)


# /api/v1/stix_files/<id_>
@csrf_exempt
@api_key_auth
def stix_files_id(request, id_):
    try:
        if request.method == 'GET':
            return get_stix_file_document_info(request, id_)
        elif request.method == 'DELETE':
            delete_stix_file_document_info(id_)
            return api_root.get_delete_normal_status()
        else:
            return HttpResponseNotAllowed(['GET', 'DELETE'])
    except Exception as e:
        return api_root.error(e)


# GET /api/v1/stix_files/<id_>
def get_stix_file_document_info(request, id_):
    try:
        doc = StixFiles.objects.get(id=id_)
        return api_root.get_rest_api_document_info(doc)
    except Exception:
        return api_root.error(Exception('The specified id not found.'))


# DELETE /api/v1/stix_files/<id_>
def delete_stix_file_document_info(id_):
    try:
        api_root.delete_stix_document(id_=id_)
    except Exception as e:
        return api_root.error(e)


# GET /api/v1/stix_files/<id>/stix
@api_key_auth
def stix_files_id_stix(request, id_):
    try:
        doc = StixFiles.objects.get(id=id_)
        return api_root.get_rest_api_document_content(doc)
    except DoesNotExist:
        return api_root.error(Exception('The specified id not found.'))
    except ValidationError:
        return api_root.error(Exception('The specified id is invalid.'))
