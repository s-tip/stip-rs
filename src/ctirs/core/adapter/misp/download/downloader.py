import io
import json
import requests
from stix.core.stix_package import STIXPackage
from ctirs.models.rs.models import System


class MISPDownloader(object):
    def __init__(self, url, api_key):
        self.url = url
        self.header = {}
        self.header['Content-Type'] = 'application/json'
        self.header['Authorization'] = api_key

    def _get_date_str(self, dt):
        return dt.strftime('%Y-%m-%d')

    def _get_events(self, from_dt, to_dt, published_only):
        payload = {}
        if from_dt is not None:
            payload['from'] = self._get_date_str(from_dt)
        if to_dt is not None:
            payload['to'] = self._get_date_str(to_dt)
        if published_only:
            payload['published'] = True
        resp_text = self._post_misp(self.header, payload)
        if resp_text is None:
            return None
        resp = json.loads(resp_text)
        events = []
        for event in resp['response']:
            events.append(event['Event']['uuid'])
        return events

    def _get_event(self, uuid, version):
        payload = {}
        payload['uuid'] = uuid
        payload['returnFormat'] = version
        header = self.header.copy()
        if version == 'stix':
            header['Accept'] = 'application/xml'
        else:
            header['Accept'] = 'application/json'
        resp_text = self._post_misp(header, payload)
        if version == 'stix':
            with io.StringIO(resp_text) as fp:
                package = STIXPackage.from_xml(fp)
                return package
        else:
            return json.loads(resp_text)

    def _post_misp(self, header, payload):
        proxies = System.get_request_proxies()
        resp = requests.post(
            self.url,
            data=json.dumps(payload),
            headers=header,
            verify=False,
            proxies=proxies)

        if resp.status_code == 404:
            print('No events')
            return None

        if resp.status_code != 200:
            print('http_response_status is ' + str(resp.status_code))
            print('message :' + str(resp.text))
            print('Exit.')
            return None
        return resp.text

    def get(self, from_dt=None, to_dt=None, published_only=False, stix_version='stix2'):
        events = self._get_events(from_dt, to_dt, published_only)
        if events is None or len(events) == 0:
            return None
        stix_files = []
        for event in events:
            stix_file = self._get_event(event, stix_version)
            if stix_file:
                stix_files.append(stix_file)
        return stix_files
