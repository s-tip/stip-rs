import json
import tempfile
import datetime
import pytz
import requests
import traceback
from requests.auth import _basic_auth_str


TAXII_20_ACCEPT = 'application/vnd.oasis.taxii+json; version=2.0'
TAXII_20_PUBLICATION_CONTENT_TYPE = 'application/vnd.oasis.stix+json; version=2.0'


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


def _get_taxii_2x_objects_url(taxii_client):
    url = '%scollections/%s/objects/' % (
        taxii_client._api_root,
        taxii_client._collection)
    return url


def poll_20(taxii_client, protocol_version='2.0'):
    url = _get_taxii_2x_objects_url(taxii_client)
    if taxii_client._start is not None:
        url += ('?added_after=%s' % (taxii_client._start.strftime('%Y-%m-%dT%H:%M:%S.000Z')))
    if protocol_version == '2.0':
        headers = _get_taxii_20_get_request_header(taxii_client)
    else:
        headers = None
    try:
        count = 0
        resp = requests.get(
            url,
            headers=headers,
            verify=False,
            proxies=taxii_client._proxies
        )
        if resp.status_code >= 300:
            raise Exception('Invalid http response (%s).' % (resp.status_code))

        js = resp.json()
        if protocol_version == '2.0':
            if 'objects' not in js:
                return 0
        _, stix_file_path = tempfile.mkstemp(suffix='.json')
        if protocol_version == '2.0':
            with open(stix_file_path, 'wb+') as fp:
                fp.write(json.dumps(js, indent=4).encode('utf-8'))
        elif protocol_version == '2.1':
            ### bundle を作る
            with open(stix_file_path, 'wb+') as fp:
                fp.write(json.dumps(js, indent=4).encode('utf-8'))
        from ctirs.core.stix.regist import regist
        if taxii_client._community is not None:
            regist(stix_file_path, taxii_client._community, taxii_client._via)
        count += 1
    except BaseException:
        traceback.print_exc()
    finally:
        last_requested = datetime.datetime.now(pytz.utc)
        taxii_client._taxii.last_requested = last_requested
        taxii_client._taxii.save()
        return count


def push_20(taxii_client, stix_file_doc, protocol_version='2.0'):
    if stix_file_doc.version != '2.0':
        content = stix_file_doc.get_elevate_20()
    else:
        with open(stix_file_doc.origin_path, 'r', encoding='utf-8') as fp:
            content = fp.read()

    url = _get_taxii_2x_objects_url(taxii_client)
    headers = _get_taxii_20_post_request_header(taxii_client)

    resp = requests.post(
        url,
        headers=headers,
        data=content,
        verify=False,
        proxies=taxii_client._proxies
    )

    if resp.status_code != 202:
        raise Exception('Invalid http response: %s' % (resp.status_code))

    try:
        j = resp.json()
        if j['status'] != 'complete':
            return
        if j['failure_count'] != 0:
            return
        if j['pending_count'] != 0:
            return
    except Exception as e:
        traceback.print_exc()
        raise e
