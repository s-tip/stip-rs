import os
import datetime
import pytz
import tempfile
import traceback
import requests
import json
import libtaxii
import libtaxii.clients as clients
import libtaxii.messages_11 as tm11
import libtaxii.constants as const
from requests.auth import _basic_auth_str
from urllib.parse import urlparse
from ctirs.core.mongo.documents import TaxiiClients, Vias, ScheduleJobs
from ctirs.core.schedule.schedule import CtirsScheduler
from ctirs.models.rs.models import System


class Client(object):
    TAXII_2_ACCEPT = 'application/vnd.oasis.taxii+json; version=2.0'
    TAXII_2_PUBLICATION_CONTENT_TYPE = TAXII_2_ACCEPT

    def __init__(self, taxii_name=None, taxii_id=None, community=None, taxii_client=None):
        taxii = None
        if taxii_client is not None:
            taxii = taxii_client
        elif taxii_name is not None:
            taxii = TaxiiClients.objects.get(name=taxii_name)
        elif taxii_id is not None:
            taxii = TaxiiClients.objects.get(id=taxii_id)

        self._address = taxii.address
        self._port = taxii.port
        self._path = taxii.path
        self._collection_name = taxii.collection
        self._jobs = taxii.jobs
        self._interval_job = taxii.interval_schedule_job
        self._protocol_version = taxii.protocol_version

        self._client = clients.HttpClient()
        if taxii.is_use_cert:
            self._auth_type = clients.HttpClient.AUTH_CERT_BASIC
            self._key_file = taxii.key_file
            self._cert_file = taxii.cert_file
        else:
            self._auth_type = clients.HttpClient.AUTH_BASIC
        self._username = taxii.login_id
        self._password = taxii.login_password
        self._ssl = taxii.ssl
        self._client.set_use_https(self._ssl)
        self._client.set_auth_type(self._auth_type)

        self._proxies = System.get_request_proxies()
        if self._proxies is not None:
            p = urlparse(self._address)
            if p.scheme == 'https':
                self._client.set_proxy(self._proxies['https'])
            else:
                self._client.set_proxy(self._proxies['http'])

        try:
            self._community = taxii.community
        except BaseException:
            self._community = None
        self._via = Vias.get_via_taxii_poll(taxii, uploader=taxii.uploader)
        self._taxii = taxii
        self._start = None
        self._end = None
        self._schedule = CtirsScheduler()

    def _get_taxii_20_authorization(self):
        return _basic_auth_str(self._username, self._password)

    def get_taxii_20_get_request_header(self):
        return {
            'Accept': self.TAXII_2_ACCEPT,
            'Authorization': self._get_taxii_20_authorization(),
        }

    # TAXII 2.0 用 POST request Header
    def get_taxii_20_post_request_header(self):
        return {
            'Accept': self.TAXII_2_ACCEPT,
            'Authorization': self._get_taxii_20_authorization(),
            'Content-Type': self.TAXII_2_PUBLICATION_CONTENT_TYPE,
        }
        
    def set_start_time(self, start):
        self._start = start

    def set_end_time(self, end):
        self._end = end

    def add_job(self, schedule_job):
        self._schedule.add_job(schedule_job, self.poll_job)
        self._schedule.start_job(schedule_job)

    def resume_job(self, job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        index = -1
        if self._interval_job == schedule_job:
            if schedule_job.status == ScheduleJobs.STATUS_IN_OPERATION:
                return
        if schedule_job in self._jobs:
            index = self._jobs.index(schedule_job)
            if schedule_job.status == ScheduleJobs.STATUS_IN_OPERATION:
                return
        else:
            raise Exception('invalid job_id')
        self._schedule.resume_job(schedule_job)
        if index > -1:
            self._jobs[index] = schedule_job

    def pause_job(self, job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        index = -1
        if self._interval_job == schedule_job:
            if schedule_job.status == ScheduleJobs.STATUS_STOP:
                return
        if schedule_job in self._jobs:
            index = self._jobs.index(schedule_job)
            if schedule_job.status == ScheduleJobs.STATUS_STOP:
                return
        else:
            raise Exception('invalid job_id')
        self._schedule.pause_job(schedule_job)
        if index > -1:
            self._jobs[index] = schedule_job

    def remove_job(self, job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        self._schedule.remove_job(schedule_job)
        schedule_job.remove()

    def remove_interval_job(self):
        if self._interval_job is None:
            return
        schedule_job = ScheduleJobs.objects.get(id=self._interval_job.id)
        self._schedule.remove_job(schedule_job)
        schedule_job.remove()
        self._interval_job = None

    def poll_job(self):
        if self._taxii.last_requested is not None:
            self.set_start_time(self._taxii.last_requested.replace(tzinfo=pytz.utc))
        self.poll()

    def poll(self):
        if self._protocol_version == '2.0':
            return self.poll_20()
        else:
            return self.poll_11()

    def _get_auth_credentials_dict(self):
        auth_credentials_dict = {}
        auth_credentials_dict['username'] = self._username
        auth_credentials_dict['password'] = self._password
        if self._auth_type == clients.HttpClient.AUTH_CERT_BASIC:
            _, cert_file = tempfile.mkstemp()
            with open(cert_file, 'w', encoding='utf-8') as fp:
                fp.write(self._cert_file)
            _, key_file = tempfile.mkstemp()
            with open(key_file, 'w', encoding='utf-8') as fp:
                fp.write(self._key_file)
            auth_credentials_dict['cert_file'] = cert_file
            auth_credentials_dict['key_file'] = key_file
        return auth_credentials_dict

    def poll_11(self):
        auth_credentials_dict = self._get_auth_credentials_dict()
        self._client.set_auth_credentials(auth_credentials_dict)
        try:
            poll_parameters = tm11.PollParameters()
            poll_request = tm11.PollRequest(
                message_id=tm11.generate_message_id(),
                collection_name=self._collection_name,
                exclusive_begin_timestamp_label=self._start,
                inclusive_end_timestamp_label=self._end,
                poll_parameters=poll_parameters,
            )
            last_requested = datetime.datetime.now(pytz.utc)

            http_resp = self._client.call_taxii_service2(
                self._address,
                self._path,
                const.VID_TAXII_XML_11,
                poll_request.to_xml(),
                port=self._port)

            taxii_message = libtaxii.get_message_from_http_response(http_resp, poll_request.message_id)

            try:
                if taxii_message.content_blocks is None:
                    return 0
            except AttributeError:
                return 0

            count = 0
            for cb in taxii_message.content_blocks:
                _, stix_file_path = tempfile.mkstemp(suffix='.xml')
                with open(stix_file_path, 'wb+') as fp:
                    fp.write(cb.content)
                try:
                    from ctirs.core.stix.regist import regist
                    if self._community is not None:
                        regist(stix_file_path, self._community, self._via)
                    count += 1
                except BaseException:
                    traceback.print_exc()

            self._taxii.last_requested = last_requested
            self._taxii.save()

            return count
        finally:
            if 'cert_file' in auth_credentials_dict:
                try:
                    os.remove(auth_credentials_dict['cert_file'])
                except Exception:
                    pass
            if 'key_file' in auth_credentials_dict:
                try:
                    os.remove(auth_credentials_dict['key_file'])
                except Exception:
                    pass

    def get_taxii20_base_url(self):
        url = '%s:%d%s/' % (self._address, self._port, self._path)
        headers = {
            "Accept": "application/vnd.oasis.taxii+json; version=2.0",
        }
        try:
            resp = requests.get(
                url,
                headers=headers,
                auth=(self._username, self._password),
                verify=False,
                proxies=self._proxies
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

    def get_taxii20_objects_url(self):
        base_url = self.get_taxii20_base_url()
        if base_url is None:
            return None
        if base_url[-1] != '/':
            base_url = base_url + '/'
        url = base_url + 'collections/' + self._collection_name + '/objects/'
        return url

    def poll_20(self):
        url = self.get_taxii20_objects_url()
        if url is None:
            return 0
        headers = {
            'Accept': 'application/vnd.oasis.stix+json; version=2.0',
        }

        resp = requests.get(
            url,
            headers=headers,
            auth=(self._username, self._password),
            verify=False,
            proxies=self._proxies
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
                if self._community is not None:
                    regist(stix_file_path, self._community, self._via)
                count += 1
            except BaseException:
                traceback.print_exc()

        last_requested = datetime.datetime.now(pytz.utc)
        self._taxii.last_requested = last_requested
        self._taxii.save()
        return count

    def push(self, stix_file_doc):
        if self._protocol_version == '2.0':
            self.push_20(stix_file_doc)
        else:
            self.push_11(stix_file_doc)

    def push_11(self, stix_file_doc):
        if stix_file_doc.version.startswith('2.'):
            try:
                content = stix_file_doc.get_slide_12()
            except Exception as e:
                traceback.print_exc()
                raise e
        else:
            with open(stix_file_doc.origin_path, 'r', encoding='utf-8') as fp:
                content = fp.read()

        auth_credentials_dict = self._get_auth_credentials_dict()
        self._client.set_auth_credentials(auth_credentials_dict)

        try:
            subscription_information = tm11.SubscriptionInformation(
                collection_name=self._collection_name,
                subscription_id='subscripiton_id')
            cb = tm11.ContentBlock(const.CB_STIX_XML_11, content)
            im = tm11.InboxMessage(
                message_id=tm11.generate_message_id(),
                destination_collection_names=[self._collection_name],
                subscription_information=subscription_information,
                content_blocks=[cb])

            http_resp = self._client.call_taxii_service2(
                self._address,
                self._path,
                const.VID_TAXII_XML_11,
                im.to_xml(),
                port=self._port)
            taxii_message = libtaxii.get_message_from_http_response(http_resp, im.message_id)
            if taxii_message.status_type != 'SUCCESS':
                raise Exception('taxii_message.status_type is not SUCCESS')
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            if 'cert_file' in auth_credentials_dict:
                try:
                    os.remove(auth_credentials_dict['cert_file'])
                except Exception:
                    pass
            if 'key_file' in auth_credentials_dict:
                try:
                    os.remove(auth_credentials_dict['key_file'])
                except Exception:
                    pass

    def push_20(self, stix_file_doc):
        if stix_file_doc.version != '2.0':
            content = stix_file_doc.get_elevate_20()
        else:
            with open(stix_file_doc.origin_path, 'r', encoding='utf-8') as fp:
                content = fp.read()

        url = self.get_taxii20_objects_url()
        headers = {
            "Accept": "application/vnd.oasis.taxii+json; version=2.0",
            "Content-Type": "application/vnd.oasis.stix+json; version=2.0"
        }
        resp = requests.post(
            url,
            headers=headers,
            auth=(self._username, self._password),
            data=content,
            verify=False,
            proxies=self._proxies
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
