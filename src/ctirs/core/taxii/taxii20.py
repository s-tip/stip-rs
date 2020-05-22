import json
import tempfile
import datetime
import pytz
import requests
import traceback
from requests.auth import _basic_auth_str


TAXII_2_ACCEPT = 'application/vnd.oasis.taxii+json; version=2.0'
TAXII_2_PUBLICATION_CONTENT_TYPE = TAXII_2_ACCEPT


def _get_taxii_20_authorization(taxii_client):
    return _basic_auth_str(taxii_client._username, taxii_client._password)


def _get_taxii_20_post_request_header(taxii_client):
    return {
        'Accept': TAXII_2_ACCEPT,
        'Authorization': _get_taxii_20_authorization(taxii_client),
        'Content-Type': TAXII_2_PUBLICATION_CONTENT_TYPE,
    }


def _get_taxii_20_get_request_header(taxii_client):
    return {
        'Accept': TAXII_2_ACCEPT,
        'Authorization': _get_taxii_20_authorization(taxii_client),
    }


def _get_taxii20_base_url(taxii_client):
    # Basic TXS Get
    url = '%s:%d%s/' % (taxii_client._address, taxii_client._port, taxii_client._path)
    headers = {
        "Accept": "application/vnd.oasis.taxii+json; version=2.0",
    }
    try:
        resp = requests.get(
            url,
            headers=headers,
            auth=(taxii_client._username, taxii_client._password),
            verify=False,
            proxies=taxii_client._proxies
        )
    except Exception as e:
        traceback.print_exc()
        raise e

    j = resp.json()

    base_url = None
    if ('default' in j):
        base_url = j['default']
    else:
        base_url = url
    return base_url


def _get_taxii20_objects_url(taxii_client):
    base_url = _get_taxii20_base_url(taxii_client)
    if base_url is None:
        return None
    if base_url[-1] != '/':
        base_url = base_url + '/'
    url = base_url + 'collections/' + taxii_client._collection_name + '/objects/'
    return url


def poll_20(taxii_client):
    url = _get_taxii20_objects_url(taxii_client)
    if url is None:
        return 0
    headers = {
        'Accept': 'application/vnd.oasis.stix+json; version=2.0',
    }

    resp = requests.get(
        url,
        headers=headers,
        auth=(taxii_client._username, taxii_client._password),
        verify=False,
        proxies=taxii_client._proxies
    )

    count = 0
    stixes = []
    js = resp.json()
    if isinstance(js, list):
        stixes = js
    else:
        stixes = [js]
    for j in stixes:
        _, stix_file_path = tempfile.mkstemp(suffix='.json')
        with open(stix_file_path, 'wb+') as fp:
            fp.write(json.dumps(j, indent=4))
        try:
            from ctirs.core.stix.regist import regist
            if taxii_client._community is not None:
                regist(stix_file_path, taxii_client._community, taxii_client._via)
            count += 1
        except BaseException:
            traceback.print_exc()

    last_requested = datetime.datetime.now(pytz.utc)
    taxii_client._taxii.last_requested = last_requested
    taxii_client._taxii.save()
    return count


def push_20(taxii_client, stix_file_doc):
    if stix_file_doc.version != '2.0':
        content = stix_file_doc.get_elevate_20()
    else:
        with open(stix_file_doc.origin_path, 'r', encoding='utf-8') as fp:
            content = fp.read()

    url = _get_taxii20_objects_url()
    headers = {
        "Accept": "application/vnd.oasis.taxii+json; version=2.0",
        "Content-Type": "application/vnd.oasis.stix+json; version=2.0"
    }
    resp = requests.post(
        url,
        headers=headers,
        auth=(taxii_client._username, taxii_client._password),
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
