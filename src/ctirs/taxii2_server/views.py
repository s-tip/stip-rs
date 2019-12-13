import datetime
import pytz
import json
import tempfile
import traceback
from django.views.decorators.csrf import csrf_exempt
from ctirs.api import JsonResponse
from django.http.response import HttpResponse
from ctirs.core.mongo.documents import Vias, Communities
from ctirs.core.mongo.documents_stix import StixFiles
# from opentaxii.taxii.http import HTTP_AUTHORIZATION

RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON = 'application/taxii+json; version=2.0'
RESPONSE_COMMON_CONTENT_TYPE_STIX_JSON = 'application/stix+json; version=2.0'
RESPONSE_CONTENT_TYPE_STIX_JSON = 'application/vnd.oasis.stix+json; version=2.0'
RESPONSE_CONTENT_TYPE_TAXII_JSON = 'application/vnd.oasis.taxii+json; version=2.0'

HTTP_ACCEPT_CONTENT_TYPE = 'application/vnd.oasis.taxii+json'
HTTP_ACCEPT_VERSION = 'version=2.0'

REQUEST_CONTENT_TYPE_STIX_JSON = 'application/vnd.oasis.stix+json; version=2.0'
COLLECTION_MEDIA_TYPE = 'application/vnd.oasis.stix+json; version=2.0'

TEST_TXS_HOST_PORT = 'https://10.0.3.100:10001'
PLUGFEST_TXS_HOST_PORT = 'https://133.162.143.58:10001'
# TXS_HOST_PORT = PLUGFEST_TXS_HOST_PORT
TXS_HOST_PORT = TEST_TXS_HOST_PORT

READ_COLLECTION = 'read_collection'
WRITE_COLLECTION = 'write_collection'
READ_WRITE_COLLECTION = 'read_write_collection'
# oasis:stip_kago
HTTP_AUTHORIZATION_VALUE = 'Basic b2FzaXM6c3RpcF9rYWdv'
MAX_CONTENT_LENGTH = 10000000

API_ROOT_1 = 'api1'

# TXSが登録するコミュニティの名前
_taxii2_community_name = 'taxii2'
# TXSが登録するユーザー名
_taxii_publisher = 'admin'

try:
    _community = Communities.objects.get(name=_taxii2_community_name)
except BaseException:
    _community = None
_via = Vias.get_via_taxii_publish(_taxii_publisher)


def get_no_accept_json_data(message, error_id='To be determined', error_code='To be determined'):
    return {
        'title': 'Incorrect Taxii Version',
        'description': 'An incorrent Taxii version was used in the post',
        'error_id': error_id,
        'error_code': error_code,
        'http_status': '406',
        'external_details': message,
        'details': {
            'version': '1.0',
        }
    }


# HTTP_ACCEPT チェック
def check_http_accept(request, expect_content_type=HTTP_ACCEPT_CONTENT_TYPE, expect_version=HTTP_ACCEPT_VERSION):
    # debug_print('>>>request.META[HTTP_ACCEPT]:' + str(request.META['HTTP_ACCEPT']))
    # , で複数の HTTP_ACCEPT が存在する場合に備え分割
    http_accept_list = request.META['HTTP_ACCEPT'].split(',')
    # debug_print('>>>http_accept_list:' + str(http_accept_list))
    is_invalid = True
    # 一つ一つ吟味
    for http_accept in http_accept_list:
        # debug_print('>>>http_accept:' + str(http_accept))
        # ; で分割
        ll = http_accept.split(';')
        # 長さが 2 以下は無視
        if len(ll) < 2:
            # debug_print('>>>http_accept is too short. skip.')
            continue
        # debug_print('>>>ll:' + str(ll))
        # 最初の要素が正しい ContentType である (空白をトリミングして評価)
        if ll[0].strip(' ') != expect_content_type:
            # debug_print('>>>Unexpected ContentValue. skip.')
            continue
        # 2番目の要素が正しい version である (空白をトリミングして評価)
        if ll[1].strip(' ') != expect_version:
            # debug_print('>>>Unexpected Version. skip.')
            continue
        # debug_print('>>>OK')
        is_invalid = False
        break
    return is_invalid


# HTTP_AUTHORIZATION チェック
def check_common_authorization(request):
    # credential check
    if 'HTTP_AUTHORIZATION' not in request.META:
        debug_print('>>> no HTTP_AUTHORIZATION')
        r = HttpResponse(content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)
        r['WWW-Authenticate'] = 'Basic realm="taxii", type=1, title="Login to \"apps\"", Basic realm="simple"'
        r.status_code = 401
        return r

    if request.META['HTTP_AUTHORIZATION'] != HTTP_AUTHORIZATION_VALUE:
        debug_print('>>> invalid HTTP_AUTHORIZATION')
        debug_print(HTTP_AUTHORIZATION_VALUE)
        debug_print(request.META['HTTP_AUTHORIZATION'])
        r = HttpResponse(content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)
        r['WWW-Authenticate'] = 'Basic realm="taxii", type=1, title="Login to \"apps\"", Basic realm="simple"'
        r.status_code = 401
        return r
    return None


def debug_print(msg):
    print(msg)

# /taxii/
@csrf_exempt
def top_taxii(request):
    debug_print('>>>top_taxii enter')
    # method check
    debug_print('>>>HTTP method:' + str(request.method))
    if request.method != 'GET':
        data = get_no_accept_json_data('Invalid HTTP method')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)
        r.status_code = 406
        return r

    # Accept check
    debug_print('>>>request.META.has_key(HTTP_ACCEPT):' + str('HTTP_ACCEPT' in request.META))
    if 'HTTP_ACCEPT' not in request.META:
        print('>>>no HTTP_ACCEPT')
        data = get_no_accept_json_data('No Accept')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)
        r.status_code = 406
        return r

    if check_http_accept(request):
        debug_print('>>>Invalid Accept')
        data = get_no_accept_json_data('Invalid Accept')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)
        r.status_code = 406
        return r

    # Authenticate check
    r = check_common_authorization(request)
    if r is not None:
        return r

    data = {
        'title': 'TAXII Server Under Test',
        'description': 'This is a TAXII Server under test',
        'contact': 'Please contact x-xxx-xxx-xxxx',
        'default': '%s/%s/' % (TXS_HOST_PORT, API_ROOT_1),
        'api_roots': [
            '%s/%s/' % (TXS_HOST_PORT, API_ROOT_1)
        ]
    }
    return JsonResponse(data, safe=False, content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)

# /api1/
@csrf_exempt
def top(request):
    debug_print('>>>top enter')
    # method check
    debug_print('>>>HTTP method:' + str(request.method))
    if request.method != 'GET':
        data = get_no_accept_json_data('Invalid HTTP method')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)
        r.status_code = 406
        return r

    # Accept check
    debug_print('>>>request.META.has_key(HTTP_ACCEPT):' + str('HTTP_ACCEPT' in request.META))
    if 'HTTP_ACCEPT' not in request.META:
        print('>>>no HTTP_ACCEPT')
        data = get_no_accept_json_data('No Accept')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)
        r.status_code = 406
        return r

    if check_http_accept(request):
        debug_print('>>>Invalid Accept')
        data = get_no_accept_json_data('Invalid Accept')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)
        r.status_code = 406
        return r

    # Authenticate check
    r = check_common_authorization(request)
    if r is not None:
        return r

    data = {
        'title': 'Sharing Group 1',
        'description': 'This sharing group shares intelligence.',
        'versions': ['taxii-2.0'],
        'max_content_length': MAX_CONTENT_LENGTH
    }
    return JsonResponse(data, safe=False, content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)


# /collections/
@csrf_exempt
def collections_root(request):
    debug_print('>>>collections enter')
    # method check
    if request.method != 'GET':
        debug_print('>>>Invalid HTTP method:' + str(request.method))
        data = get_no_accept_json_data('Invalid HTTP method')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
        r.status_code = 406
        return r

    # Authenticate check
    r = check_common_authorization(request)
    if r is not None:
        debug_print('>>>Invalid Authentication.')
        return r

    # Accept check
    if 'HTTP_ACCEPT' not in request.META:
        debug_print('>>>No HTTP_ACCEPT.')
        data = get_no_accept_json_data('No Accept')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
        r.status_code = 406
        return r

    if check_http_accept(request):
        debug_print('>>>HTTP_ACCEPT Invalid:' + str(request.META['HTTP_ACCEPT']))
        data = get_no_accept_json_data('Invalid Accept')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
        r.status_code = 406
        return r

    collections = []
    data = {
        'id': READ_COLLECTION,
        'title': 'Test Read Collection',
        'description': 'This is Test Read Collection',
        'can_read': True,
        'can_write': False,
        'media_types': [
            COLLECTION_MEDIA_TYPE
        ]
    }
    collections.append(data)
    data = {
        'id': WRITE_COLLECTION,
        'title': 'Test Write Collection',
        'description': 'This is Test Write Collection',
        'can_read': False,
        'can_write': True,
        'media_types': [
            COLLECTION_MEDIA_TYPE
        ]
    }
    collections.append(data)
    data = {
        'id': READ_WRITE_COLLECTION,
        'title': 'Test Read Write Collection',
        'description': 'This is Test Read Write Collection',
        'can_read': True,
        'can_write': True,
        'media_types': [
            COLLECTION_MEDIA_TYPE
        ]
    }
    collections.append(data)
    r = {}
    r['collections'] = collections

    return JsonResponse(r, safe=False, content_type=RESPONSE_CONTENT_TYPE_TAXII_JSON)


@csrf_exempt
# /collections/_id
def collections(request, id_):
    debug_print('>>>collections enter')
    debug_print('>>>id_ :' + str(id_))
    # method check
    if request.method != 'GET':
        debug_print('>>>Invalid HTTP method:' + str(request.method))
        data = get_no_accept_json_data('Invalid HTTP method')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
        r.status_code = 406
        return r

    # Authenticate check
    r = check_common_authorization(request)
    if r is not None:
        debug_print('>>>Invalid Authentication.')
        return r

    # Accept check
    if 'HTTP_ACCEPT' not in request.META:
        debug_print('>>>No HTTP_ACCEPT.')
        data = get_no_accept_json_data('No Accept')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
        r.status_code = 406
        return r

    if check_http_accept(request):
        debug_print('>>>HTTP_ACCEPT Invalid:' + str(request.META['HTTP_ACCEPT']))
        data = get_no_accept_json_data('Invalid Accept')
        r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
        r.status_code = 406
        return r

    if id_ == READ_COLLECTION:
        data = {
            'id': id_,
            'title': 'Test Read Collection',
            'description': 'This is Test Read Collection',
            'can_read': True,
            'can_write': False,
            'media_types': [
                COLLECTION_MEDIA_TYPE
            ]
        }
    elif id_ == WRITE_COLLECTION:
        data = {
            'id': id_,
            'title': 'Test Write Collection',
            'description': 'This is Test Write Collection',
            'can_read': False,
            'can_write': True,
            'media_types': [
                COLLECTION_MEDIA_TYPE
            ]
        }
    elif id_ == READ_WRITE_COLLECTION:
        data = {
            'id': id_,
            'title': 'Test Read Write Collection',
            'description': 'This is Test Read Write Collection',
            'can_read': True,
            'can_write': True,
            'media_types': [
                COLLECTION_MEDIA_TYPE
            ]
        }
    else:
        # unmatched collection id
        debug_print('>>>unmatched collection id:' + str(id_))
        data = {
            'title': 'Incorrect Collection Get',
            'description': 'An incorrect URL for a collection was accessed',
            'error_id': 'To be determined',
            'error_code': 'To be determined',
            'http_status': '404',
            'external_details': 'To be determined',
            "details": {
                "collection": request.path,
            }
        }
        j = JsonResponse(data, safe=False, content_type=RESPONSE_COMMON_CONTENT_TYPE_TAXII_JSON)
        j.status_code = 404
        return j

    return JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_TAXII_JSON)


@csrf_exempt
def collections_objects(request, id_):
    debug_print('>>>collections_objects enter')
    debug_print('>>>id_ :' + str(id_))
    # Authenticate check
    r = check_common_authorization(request)
    if r is not None:
        debug_print('>>>Invalid Authentication.')
        return r

    if id_ == READ_COLLECTION:
        # Read Collection
        debug_print('>>>Read Collection.')
        if request.method != 'GET':
            # ReadCollcetion 指定時に GET 以外はNG
            debug_print('>>>Invalid HTTP Method:' + str(request.method))
            data = get_no_accept_json_data('Invalid HTTP method')
            r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
            r.status_code = 406
            return r
        # Accept check
        if 'HTTP_ACCEPT' not in request.META:
            debug_print('>>>No HTTP_ACCEPT.')
            data = get_no_accept_json_data('No Accept')
            r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
            r.status_code = 406
            return r

        if check_http_accept(request):
            debug_print('>>>HTTP_ACCEPT Invalid:' + str(request.META['HTTP_ACCEPT']))
            data = get_no_accept_json_data('Invalid Accept')
            r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
            r.status_code = 406
            return r
        return get_read_collection_content()
    elif id_ == WRITE_COLLECTION:
        # Write Collection
        debug_print('>>>Write Collection.')
        if request.method != 'POST':
            # WirteCollcetion 指定時に POST 以外はNG
            debug_print('>>>Invalid HTTP Method:' + str(request.method))
            data = get_no_accept_json_data('Invalid HTTP method')
            r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
            r.status_code = 406
            return r

        # max-content-length check
        if int(request.META['CONTENT_LENGTH']) > MAX_CONTENT_LENGTH:
            debug_print('>>>Too much content size:' + str(request.META['CONTENT_LENGTH']))
            data = get_no_accept_json_data('Too much content size')
            r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
            r.status_code = 406
            return r

        # Accept check
        if 'HTTP_ACCEPT' not in request.META:
            debug_print('>>>No HTTP_ACCEPT.')
            data = get_no_accept_json_data('No Accept')
            r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
            r.status_code = 406
            return r

        if check_http_accept(request):
            debug_print('>>>HTTP_ACCEPT Invalid:' + str(request.META['HTTP_ACCEPT']))
            data = get_no_accept_json_data('Invalid Accept')
            r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
            r.status_code = 406
            return r
        data = post_write_collection(request.body)
        r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_TAXII_JSON)
        r.status_code = 202
        return r
    elif id_ == READ_WRITE_COLLECTION:
        # ReadWrite Collection
        debug_print('>>>ReadWrite Collection.')
        if request.method == 'GET':
            return get_read_collection_content()
        elif request.method == 'POST':
            # max-content-length check
            if int(request.META['CONTENT_LENGTH']) > MAX_CONTENT_LENGTH:
                debug_print('>>>Too much content size:' + str(request.META['CONTENT_LENGTH']))
                data = get_no_accept_json_data('Too much content size')
                r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
                r.status_code = 406
                return r
            data = post_write_collection(request.body)
            r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_TAXII_JSON)
            r.status_code = 202
            return r
        else:
            debug_print('>>>Invalid HTTP Method:' + str(request.method))
            data = get_no_accept_json_data('Invalid HTTP method')
            r = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
            r.status_code = 406
            return r
    else:
        # unmatched collection id
        debug_print('>>>Unmatched Collection:' + str(id_))
        data = {
            'title': 'Incorrect Collection Get',
            'description': 'An incorrect URL for a collection was accessed',
            'error_id': 'To be determined',
            'error_code': 'To be determined',
            'http_status': '404',
            'external_details': 'To be determined',
            "details": {
                "collection": id_,
            }
        }
        j = JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)
        j.status_code = 404
        return j

    return JsonResponse(data, safe=False, content_type=RESPONSE_CONTENT_TYPE_STIX_JSON)


def get_read_collection_content():
    debug_print('>>>enter get_read_collection_content')
    j = []
    for stix_file in StixFiles.objects(input_community=_community):
        debug_print('>>>stix_file id: ' + str(stix_file.id))
        content = stix_file.content.read()
        j.append(json.loads(content))
    return JsonResponse(j, safe=False, content_type=RESPONSE_COMMON_CONTENT_TYPE_STIX_JSON)


# content の中身を RS に登録
def post_write_collection(content):
    debug_print('>>>enter post_write_collection')
    debug_print('>>>--- content start')
    debug_print(str(content))
    debug_print('>>>--- content end')

    # stixファイルを一時ファイルに出力
    _, stix_file_path = tempfile.mkstemp(suffix='.json')
    with open(stix_file_path, 'wb+') as fp:
        fp.write(content)
    print('>>>stix_file_path: ' + str(stix_file_path))

    # RSに登録
    try:
        from ctirs.core.stix.regist import regist
        if _community is not None:
            regist(stix_file_path, _community, _via)
        print('>>>regist success:')
        print('>>>regist _community: ' + str(_community))
        print('>>>regist _via: ' + str(_via))
    except Exception as e:
        traceback.print_exc()
        raise e

    # stix解析し、返却値を作成する
    j = json.loads(content)

    r = {}
    r['id'] = j['id']
    r['status'] = 'complete'
    r['request_timestamp'] = datetime.datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    total_count = 0
    failure_count = 0
    success_count = 0
    pending_count = 0
    successes = []
    for object_ in j['objects']:
        total_count += 1
        success_count += 1
        successes.append(object_['id'])
    r['total_count'] = total_count
    r['success_count'] = success_count
    r['failure_count'] = failure_count
    r['pending_count'] = pending_count
    r['successes'] = successes
    return r
