import os
import json
import tempfile
import datetime
import pytz
import requests
import traceback
import libtaxii.clients as clients
import urllib.parse as urlparse
from urllib.parse import urlencode
from requests.auth import _basic_auth_str
from stix2 import parse
from stix2.v21.bundle import Bundle
from ctirs.core.mongo.documents_taxii21_objects import StixObject
from logging import getLogger

logger = getLogger('txs2_audit')


TAXII_20_ACCEPT = 'application/vnd.oasis.stix+json; version=2.0'
TAXII_21_ACCEPT = 'application/taxii+json; version=2.1'
TAXII_20_PUBLICATION_CONTENT_TYPE = 'application/vnd.oasis.stix+json; version=2.0'
TAXII_21_PUBLICATION_CONTENT_TYPE = TAXII_21_ACCEPT


def _get_taxii_2x_authorization(taxii_client):
    return _basic_auth_str(taxii_client._username, taxii_client._password)


def _get_taxii_20_post_request_header(taxii_client):
    return {
        'Accept': TAXII_20_ACCEPT,
        'Authorization': _get_taxii_2x_authorization(taxii_client),
        'Content-Type': TAXII_20_PUBLICATION_CONTENT_TYPE,
    }


def _get_taxii_20_get_request_header(taxii_client):
    return {
        'Accept': TAXII_20_ACCEPT,
        'Authorization': _get_taxii_2x_authorization(taxii_client),
    }


def _get_taxii_21_get_request_header(taxii_client):
    return {
        'Accept': TAXII_21_ACCEPT,
        'Authorization': _get_taxii_2x_authorization(taxii_client),
    }


def _get_taxii_21_post_request_header(taxii_client):
    return {
        'Accept': TAXII_21_ACCEPT,
        'Authorization': _get_taxii_2x_authorization(taxii_client),
        'Content-Type': TAXII_21_PUBLICATION_CONTENT_TYPE,
    }


def _get_taxii_2x_objects_url(taxii_client):
    if taxii_client._port == 443:
        url = 'https://%s%s%scollections/objects/' % (
            taxii_client._domain,
            taxii_client._api_root,
            taxii_client._collection)
    else:
        url = 'https://%s:%d%scollections/%s/objects/' % (
            taxii_client._domain,
            taxii_client._port,
            taxii_client._api_root,
            taxii_client._collection)
    return url


def _get_taxii_2x_manifest_url(taxii_client):
    if taxii_client._port == 443:
        url = 'https://%s%scollections/%s/manifest/' % (
            taxii_client._domain,
            taxii_client._api_root,
            taxii_client._collection)
    else:
        url = 'https://%s:%d%scollections/%s/manifest/' % (
            taxii_client._domain,
            taxii_client._port,
            taxii_client._api_root,
            taxii_client._collection)
    return url


def _get_taxii_2x_versions_url(taxii_client, object_id):
    if taxii_client._port == 443:
        url = 'https://%s%scollections/%s/objects/%s/versions/' % (
            taxii_client._domain,
            taxii_client._api_root,
            taxii_client._collection,
            object_id)
    else:
        url = 'https://%s:%d%scollections/%s/objects/%s/versions/' % (
            taxii_client._domain,
            taxii_client._port,
            taxii_client._api_root,
            taxii_client._collection,
            object_id)
    return url


def _get_taxii_2x_object_url(taxii_client, object_id):
    if taxii_client._port == 443:
        url = 'https://%s%scollections/%s/objects/%s/' % (
            taxii_client._domain,
            taxii_client._api_root,
            taxii_client._collection,
            object_id)
    else:
        url = 'https://%s:%d%scollections/%s/objects/%s/' % (
            taxii_client._domain,
            taxii_client._port,
            taxii_client._api_root,
            taxii_client._collection,
            object_id)
    return url


def _get_query(taxii_client, next=None, filtering_params=None):
    query = {}

    if taxii_client._start is not None:
        query['added_after'] = taxii_client._start.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    if taxii_client._protocol_version == '2.1':
        if next is not None:
            query['next'] = next

    if filtering_params is not None:
        if 'next' not in query:
            if 'next' in filtering_params:
                query['next'] = filtering_params['next']
        if 'limit' in filtering_params:
            query['limit'] = filtering_params['limit']
        if 'match' in filtering_params:
            match = filtering_params['match']
            if 'id' in match:
                query['match[id]'] = match['id']
            if 'type' in match:
                query['match[type]'] = match['type']
            if 'spec_version' in match:
                query['match[spec_version]'] = match['spec_version']
            if 'version' in match:
                query['match[version]'] = match['version']
    return query


def _get_json_response(taxii_client, method='objects', next=None, object_id=None, filtering_params=None):
    if method == 'objects':
        url = _get_taxii_2x_objects_url(taxii_client)
    elif method == 'manifest':
        url = _get_taxii_2x_manifest_url(taxii_client)
    elif method == 'versions':
        url = _get_taxii_2x_versions_url(taxii_client, object_id)
    elif method == 'get_object':
        url = _get_taxii_2x_object_url(taxii_client, object_id)
    else:
        raise Exception('Method invalid')
    query = _get_query(taxii_client, next=next, filtering_params=filtering_params)
    return get_request(taxii_client, url, query)


def _delete_json_response(taxii_client, object_id=None, filtering_params=None):
    url = _get_taxii_2x_object_url(taxii_client, object_id)
    query = _get_query(taxii_client, filtering_params)
    return delete_request(taxii_client, url, query)


def get_request(taxii_client, url, query):
    if taxii_client._protocol_version == '2.0':
        headers = _get_taxii_20_get_request_header(taxii_client)
    elif taxii_client._protocol_version == '2.1':
        headers = _get_taxii_21_get_request_header(taxii_client)

    resp = _request_to_txs20(taxii_client, headers, url, http_method='GET', query=query, content=None)
    return resp.json()


def delete_request(taxii_client, url, query):
    if taxii_client._protocol_version == '2.0':
        headers = _get_taxii_20_get_request_header(taxii_client)
    elif taxii_client._protocol_version == '2.1':
        headers = _get_taxii_21_get_request_header(taxii_client)

    resp = _request_to_txs20(taxii_client, headers, url, http_method='DELETE', query=query, content=None)
    return resp.json()


def _get_objects_21(taxii_client, objects, resp_json, filtering_params=None):
    if resp_json is None:
        return objects
    if 'objects' not in resp_json:
        return objects
    if len(resp_json['objects']) == 0:
        return objects
    for o_dict in resp_json['objects']:
        try:
            o_ = parse(o_dict, version='2.1', allow_custom=True)
            if not StixObject.objects.filter(
                object_id=o_dict['id'],
                modified=o_dict['modified']):
                objects.append(o_)
            else:
                print('Skipped! _id:%s/modified:%s has already existed.' % (o_.id, o_dict['modified']))
        except Exception:
            pass

    if 'more' not in resp_json:
        return objects
    if resp_json['more'] and 'next' in resp_json:
        next_resp_json = _get_json_response(
            taxii_client,
            method='objects',
            next=resp_json['next'],
            object_id=None,
            filtering_params=filtering_params)
        return _get_objects_21(
            taxii_client,
            objects,
            next_resp_json,
            filtering_params)
    return objects


def manifest(taxii_client, filtering_params=None):
    try:
        js = _get_json_response(
            taxii_client, method='manifest', next=None, object_id=None,
            filtering_params=filtering_params)
        if 'http_status' in js:
            raise Exception(json.dumps(js, indent=4))
        if 'objects' not in js:
            return []
        return js['objects']
    except BaseException as e:
        traceback.print_exc()
        raise e


def versions(taxii_client, object_id, filtering_params=None):
    try:
        js = _get_json_response(
            taxii_client, method='versions', next=None, object_id=object_id,
            filtering_params=filtering_params)
        if 'http_status' in js:
            raise Exception(json.dumps(js, indent=4))
        if 'versions' not in js:
            return []
        return js['versions']
    except BaseException as e:
        traceback.print_exc()
        raise e


def get_object(taxii_client, object_id, filtering_params=None):
    try:
        js = _get_json_response(
            taxii_client, method='get_object', next=None, object_id=object_id,
            filtering_params=filtering_params)
        if 'http_status' in js:
            raise Exception(json.dumps(js, indent=4))
        if 'objects' not in js:
            return []
        return js['objects']
    except BaseException as e:
        traceback.print_exc()
        raise e


def delete_object(taxii_client, object_id, filtering_params=None):
    try:
        js = _delete_json_response(taxii_client, object_id=object_id, filtering_params=filtering_params)
        if 'http_status' in js:
            raise Exception(json.dumps(js, indent=4))
        return
    except BaseException as e:
        traceback.print_exc()
        raise e


def poll_20(taxii_client, filtering_params=None):
    try:
        protocol_version = taxii_client._protocol_version
        count = 0
        fd = None
        js = _get_json_response(
            taxii_client, method='objects', next=None, object_id=None,
            filtering_params=filtering_params)
        if 'http_status' in js:
            raise Exception(json.dumps(js, indent=4))
        if 'objects' not in js:
            return 0

        fd, stix_file_path = tempfile.mkstemp(suffix='.json')
        if protocol_version == '2.0':
            with open(stix_file_path, 'wb+') as fp:
                fp.write(json.dumps(js, indent=4).encode('utf-8'))
        elif protocol_version == '2.1':
            objects = _get_objects_21(
                taxii_client, [],
                js, filtering_params=filtering_params)
            if len(objects) == 0:
                return 0
            bundle = Bundle(objects)
            with open(stix_file_path, 'wb+') as fp:
                fp.write(bundle.serialize(pretty=True).encode('utf-8'))
        from ctirs.core.stix.regist import regist
        if taxii_client._community is not None:
            regist(stix_file_path, taxii_client._community, taxii_client._via)
        count += 1
        last_requested = datetime.datetime.now(pytz.utc)
        taxii_client._taxii.last_requested = last_requested
        taxii_client._taxii.save()
        return count
    except BaseException as e:
        traceback.print_exc()
        raise e
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except Exception:
                pass


def push_20(taxii_client, stix_file_doc, protocol_version='2.0'):
    url = _get_taxii_2x_objects_url(taxii_client)

    if protocol_version == '2.0':
        headers = _get_taxii_20_post_request_header(taxii_client)
        if stix_file_doc.version.startswith('2.'):
            with open(stix_file_doc.origin_path, 'r', encoding='utf-8') as fp:
                content = fp.read().encode('utf-8')
        else:
            content = stix_file_doc.get_elevate_20().encode('utf-8')
    elif protocol_version == '2.1':
        headers = _get_taxii_21_post_request_header(taxii_client)
        if stix_file_doc.version == '2.1':
            with open(stix_file_doc.origin_path, 'r', encoding='utf-8') as fp:
                content = fp.read().encode('utf-8')
        else:
            content = stix_file_doc.get_elevate_21().encode('utf-8')
        org_stix = json.loads(content)
        push_stix = {}
        push_stix['objects'] = org_stix['objects']
        content = json.dumps(push_stix, indent=4)

    resp = _request_to_txs20(taxii_client, headers, url, http_method='POST', query={}, content=content)
    if resp.status_code != 202:
        raise Exception('Invalid http response: %s' % (resp.status_code))
    msg = 'An add object status response shows below.'
    msg += json.dumps(resp.json(), indent=4)
    return msg
 

def _request_to_txs20(taxii_client, headers, url, http_method='GET', query={}, content=None):
    resp = None
    cert_file = None
    key_file = None
    cert_fd = None
    key_fd = None
    if taxii_client._auth_type == clients.HttpClient.AUTH_CERT_BASIC:
        del(headers['Authorization'])
        cert_fd, cert_file = tempfile.mkstemp()
        with open(cert_file, 'w', encoding='utf-8') as fp:
            fp.write(taxii_client._cert_file)
        key_fd, key_file = tempfile.mkstemp()
        with open(key_file, 'w', encoding='utf-8') as fp:
            fp.write(taxii_client._key_file)
        cert = (cert_file, key_file)
    else:
        cert = None

    logger.info('-----start-----')
    logger.info('url: %s' % (url))
    logger.info('method: %s' % (http_method))
    logger.info('headers: \n%s' % (json.dumps(headers, indent=4)))
    logger.info('query: \n%s' % (json.dumps(query, indent=4)))
    logger.info('content: \n%s' % (content))
    try:
        url_parts = list(urlparse.urlparse(url))
        url_parts[4] = urlencode(query)
        url = urlparse.urlunparse(url_parts)
        if http_method == 'GET':
            resp = requests.get(
                url,
                headers=headers,
                verify=False,
                cert=cert,
                proxies=taxii_client._proxies
            )
        elif http_method == 'POST':
            resp = requests.post(
                url,
                headers=headers,
                data=content,
                verify=False,
                cert=cert,
                proxies=taxii_client._proxies
            )
        elif http_method == 'DELETE':
            resp = requests.delete(
                url,
                headers=headers,
                data=content,
                verify=False,
                cert=cert,
                proxies=taxii_client._proxies
            )
    finally:
        logger.info('response status: %s' % (resp.status_code))
        try:
            logger.info('response json: \n%s' % (json.dumps(resp.json(), indent=4)))
        except Exception:
            logger.info('response body (not json format): \n%s' % (resp.text))
        logger.info('-----end-----')
        if cert_fd is not None:
            try:
                os.close(cert_fd)
            except Exception:
                pass
        if key_fd is not None:
            try:
                os.close(key_fd)
            except Exception:
                pass
        if cert_file is not None:
            try:
                os.remove(cert_file)
            except Exception:
                pass
        if key_file is not None:
            try:
                os.remove(key_file)
            except Exception:
                pass
    return resp
