import json
import tempfile
import datetime
import pytz
import requests
import traceback
import urllib.parse as urlparse
from urllib.parse import urlencode
from requests.auth import _basic_auth_str
from stix2 import parse
from stix2.v21.bundle import Bundle
from ctirs.core.mongo.documents_taxii21_objects import StixObject


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
    url = '%scollections/%s/objects/' % (
        taxii_client._api_root,
        taxii_client._collection)
    return url


def _get_json_response(taxii_client, protocol_version, next=None):
    url = _get_taxii_2x_objects_url(taxii_client)
    url_parts = list(urlparse.urlparse(url))
    query = {}

    if taxii_client._start is not None:
        query['added_after'] = taxii_client._start.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    if protocol_version == '2.0':
        headers = _get_taxii_20_get_request_header(taxii_client)
    elif protocol_version == '2.1':
        headers = None
        headers = _get_taxii_21_get_request_header(taxii_client)
        if next is not None:
            query['next'] = next

    url_parts[4] = urlencode(query)
    url = urlparse.urlunparse(url_parts)
    resp = requests.get(
        url,
        headers=headers,
        verify=False,
        proxies=taxii_client._proxies
    )
    if resp.status_code >= 300:
        raise Exception('Invalid http response (%s).' % (resp.status_code))
    return resp.json()


def _get_objects_21(taxii_client, protocol_version, objects, resp_json):
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
            protocol_version,
            next=resp_json['next'])
        return _get_objects_21(
            taxii_client,
            protocol_version,
            objects,
            next_resp_json)
    return objects


def poll_20(taxii_client, protocol_version='2.0'):
    try:
        count = 0
        js = _get_json_response(taxii_client, protocol_version)
        if 'objects' not in js:
            return 0

        _, stix_file_path = tempfile.mkstemp(suffix='.json')
        if protocol_version == '2.0':
            with open(stix_file_path, 'wb+') as fp:
                fp.write(json.dumps(js, indent=4).encode('utf-8'))
        elif protocol_version == '2.1':
            objects = _get_objects_21(taxii_client, protocol_version, [], js)
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

    try:
        resp = requests.post(
            url,
            headers=headers,
            data=content,
            verify=False,
            proxies=taxii_client._proxies
        )

        if resp.status_code != 202:
            raise Exception('Invalid http response: %s' % (resp.status_code))
        msg = 'An add object status response shows below.'
        msg += json.dumps(resp.json(), indent=4)
        return msg
    except Exception as e:
        traceback.print_exc()
        raise e
