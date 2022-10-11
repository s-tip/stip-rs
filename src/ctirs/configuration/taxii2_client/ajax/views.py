from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from ctirs.api import JsonResponse
from ctirs.core.mongo.documents import Taxii2Clients
import ctirs.configuration.taxii2_client.views as tc2
import uuid


COLLECTION_SUFFIX = 'collections/'


def _get_taxii_discovery_url(protocol_version, domain, port):
    if protocol_version == '2.1':
        end_point = '/taxii2/'
    else:
        end_point = '/taxii/'
    if port == 443:
        return 'https://%s%s' % (domain, end_point)
    else:
        return 'https://%s:%d%s' % (domain, port, end_point)


def _get_collections_url(domain, port, api_root):
    if api_root.startswith('/'):
        end_point = api_root
    else:
        end_point = '/%s' % (api_root)
    if not end_point.endswith('/'):
        end_point = '%s/' % (end_point)
    if port == 443:
        return 'https://%s%s%s' % (domain, end_point, COLLECTION_SUFFIX)
    else:
        return 'https://%s:%d%s%s' % (domain, port, end_point, COLLECTION_SUFFIX)


def _get_collection_url(domain, port, api_root, collection):
    base = _get_collections_url(domain, port, api_root)
    return '%s%s/' % (base, collection)


def _get_taxii2_client_create_ca(request):
    return 'ca' in request.GET


def _taxii_request(request, end_point):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        tc = None
        setting_name = tc2.get_taxii2_client_create_display_name(request)
        domain = tc2.get_taxii2_client_create_domain(request)
        if not domain:
            resp = {'status': 'NG',
                    'message': 'No TAXII Server Domain'}
            return JsonResponse(resp)
        port = tc2.get_taxii2_client_create_port(request)
        login_id = tc2.get_taxii2_client_create_login_id(request)
        login_password = tc2.get_taxii2_client_create_login_password(request)
        ca = _get_taxii2_client_create_ca(request)
        certificate = tc2.get_taxii2_client_create_certificate(request)
        private_key = tc2.get_taxii2_client_create_private_key(request)
        protocol_version = tc2.get_taxii2_client_create_protocol_version(request)

        if setting_name:
            try:
                tc_work = Taxii2Clients.objects.get(name=setting_name)
                if len(login_password) == 0:
                    login_password = tc_work.login_password
                if len(certificate) == 0:
                    certificate = tc_work.cert_file
                if len(private_key) == 0:
                    private_key = tc_work.key_file
                setting_name = str(uuid.uuid4())
            except Taxii2Clients.DoesNotExist:
                pass
        setting_name = str(uuid.uuid4())

        tc = Taxii2Clients.create(
            name=setting_name,
            login_id=login_id,
            login_password=login_password,
            ca=ca,
            cert_file=certificate,
            key_file=private_key,
            protocol_version=protocol_version,
        )
        from ctirs.core.taxii.taxii import Client
        cl = Client(community=None, taxii2_client=tc)
        if end_point == 'discovery':
            url = _get_taxii_discovery_url(protocol_version, domain, port)
        elif end_point == 'collections':
            api_root = tc2.get_taxii2_client_create_api_root(request)
            url = _get_collections_url(domain, port, api_root)
        elif end_point == 'collection':
            api_root = tc2.get_taxii2_client_create_api_root(request)
            collection = tc2.get_taxii2_client_create_collection(request)
            url = _get_collection_url(domain, port, api_root, collection)
        else:
            raise Exception('Invalid end_point')
        txs_resp = cl.request_get_taxii_server(url)
        resp = {'status': 'OK',
                'data': txs_resp}
        return JsonResponse(resp)
    except Exception as e:
        resp = {'status': 'NG',
                'message': str(e)}
    finally:
        if tc is not None:
            tc.delete()
    return JsonResponse(resp)


@login_required
def get_discovery(request):
    return _taxii_request(request, end_point='discovery')


@login_required
def get_collections(request):
    return _taxii_request(request, end_point='collections')


@login_required
def get_collection(request):
    return _taxii_request(request, end_point='collection')
