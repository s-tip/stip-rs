import os
import json
from django.http.response import HttpResponse
from ctirs.core.mongo.documents_stix import StixFiles
from stip.common.rest_api_auth import auth_by_api_key


def authentication(request):
    username = _get_api_user(request)
    api_key = _get_api_api_key(request)
    if ((username is None) or (api_key is None)):
        return None
    return auth_by_api_key(username, api_key)


def _get_api_user(request):
    try:
        return request.META['HTTP_USERNAME']
    except KeyError:
        return None


def _get_api_api_key(request):
    try:
        return request.META['HTTP_APIKEY']
    except KeyError:
        return None


class JsonResponse(HttpResponse):
    """
    An HTTP response class that consumes data to be serialized to JSON.

    :param data: Data to be dumped into json. By default only ``dict`` objects
      are allowed to be passed due to a security flaw before EcmaScript 5. See
      the ``safe`` parameter for more information.
    :param encoder: Should be an json encoder class. Defaults to
      ``django.core.serializers.json.DjangoJSONEncoder``.
    :param safe: Controls if only ``dict`` objects may be serialized. Defaults
      to ``True``.
    """

#    def __init__(self, data, encoder=DjangoJSONEncoder, safe=True, **kwargs):
    def __init__(self, data, encoder=None, safe=True, **kwargs):
        if safe and not isinstance(data, dict):
            raise TypeError('In order to allow non-dict objects to be '
                            'serialized set the safe parameter to False')
        kwargs.setdefault('content_type', 'application/json')
        data = json.dumps(data, cls=encoder)
        super(JsonResponse, self).__init__(content=data, **kwargs)


def error(e=None):
    d = {}
    d['return_code'] = '1'
    d['userMessage'] = 'A system error has occurred. Please check the system log.'
    return JsonResponse(d, status=500, safe=False)


def get_normal_response_json():
    d = {}
    d['return_code'] = '0'
    d['userMessage'] = 'Success'
    return d


def get_put_normal_status():
    d = get_normal_response_json()
    return JsonResponse(d, status=201, safe=False)


def get_delete_normal_status(data_dict=None):
    return JsonResponse(data_dict, status=200, safe=False)


def is_exist_file_option(request):
    try:
        if request.GET['file'] == '1':
            return True
    except KeyError:
        pass
    return False


def get_rest_api_document_info(doc):
    return JsonResponse(doc.get_rest_api_document_info(), safe=False)


def get_rest_api_document_content(doc):
    return JsonResponse(doc.get_rest_api_document_content(), safe=False)


def delete_stix_document(id_=None, package_id=None):
    if id_:
        origin_path = StixFiles.delete_by_id(id_)
    elif package_id:
        origin_path = StixFiles.delete_by_package_id(package_id)
    else:
        return
    # ファイル削除
    if os.path.exists(origin_path):
        os.remove(origin_path)
    return
