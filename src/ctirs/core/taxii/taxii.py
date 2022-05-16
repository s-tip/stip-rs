import pytz
import traceback
import libtaxii.clients as clients
from urllib.parse import urlparse
from ctirs.core.mongo.documents import Vias, ScheduleJobs
from ctirs.core.schedule.schedule import CtirsScheduler
from ctirs.models.rs.models import System
from ctirs.core.taxii.taxii20 import poll_20, push_20, manifest, versions, get_request, get_object
from ctirs.core.taxii.taxii11 import poll_11, push_11


class Client(object):
    def __init__(self, community=None, taxii_client=None, taxii2_client=None):
        if taxii2_client:
            taxii = taxii2_client
        elif taxii_client:
            taxii = taxii_client

        self._name = taxii.name
        self._protocol_version = taxii.protocol_version
        self._username = taxii.login_id
        self._password = taxii.login_password
        self._jobs = taxii.jobs
        self._interval_job = taxii.interval_schedule_job
        self._can_read = taxii.can_read
        self._can_write = taxii.can_write
        if taxii.is_use_cert:
            self._auth_type = clients.HttpClient.AUTH_CERT_BASIC
            self._key_file = taxii.key_file
            self._cert_file = taxii.cert_file
        else:
            self._auth_type = clients.HttpClient.AUTH_BASIC
        if taxii2_client:
            self._domain = taxii.domain
            self._port = taxii.port
            self._api_root = taxii.api_root
            self._collection = taxii.collection
            self._via = Vias.get_via_taxii_poll(taxii2_client=taxii, uploader=taxii.uploader)
        else:
            self._address = taxii.address
            self._port = taxii.port
            self._path = taxii.path
            self._collection_name = taxii.collection
            self._via = Vias.get_via_taxii_poll(taxii_client=taxii, uploader=taxii.uploader)
            self._client = clients.HttpClient()

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
        self._taxii = taxii
        self._start = None
        self._end = None
        self._schedule = CtirsScheduler()

    def request_get_taxii_server(self, url):
        return get_request(self, url, {})

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
        try:
            self.poll()
        except BaseException:
            traceback.print_exc()

    def poll(self, filtering_params=None):
        if not self._can_read:
            print('This collection is not for polling/consuming.: %s ' % (self._name))
            return 0
        if self._protocol_version == '2.0':
            return poll_20(self, filtering_params=filtering_params)
        elif self._protocol_version == '2.1':
            return poll_20(self, filtering_params=filtering_params)
        else:
            return poll_11(self)

    def manifest(self, filtering_params=None):
        if not self._can_read:
            print('This collection is not for retriving manifest.: %s ' % (self._name))
            return []
        if self._protocol_version == '2.0':
            return manifest(self, filtering_params=filtering_params)
        elif self._protocol_version == '2.1':
            return manifest(self, filtering_params=filtering_params)
        else:
            print('For TAXII 2.0, 2.1 only.: %s ' % (self._name))
            return []

    def versions(self, object_id, filtering_params=None):
        if not self._can_read:
            print('This collection is not for retriving versions.: %s ' % (self._name))
            return []
        if self._protocol_version == '2.0':
            return versions(self, object_id, filtering_params=filtering_params)
        elif self._protocol_version == '2.1':
            return versions(self, object_id, filtering_params=filtering_params)
        else:
            print('For TAXII 2.0, 2.1 only.: %s ' % (self._name))
            return []

    def get_object(self, object_id, filtering_params=None):
        if not self._can_read:
            print('This collection is not for retriving versions.: %s ' % (self._name))
            return []
        if self._protocol_version == '2.0':
            return get_object(self, object_id, filtering_params=filtering_params)
        elif self._protocol_version == '2.1':
            return get_object(self, object_id, filtering_params=filtering_params)
        else:
            print('For TAXII 2.0, 2.1 only.: %s ' % (self._name))
            return []

    def push(self, stix_file_doc):
        if not self._can_write:
            msg = 'This collection is not for inbox/publishing: %s ' % (self._name)
            print(msg)
            return msg
        if self._protocol_version == '2.0':
            return push_20(self, stix_file_doc, protocol_version='2.0')
        elif self._protocol_version == '2.1':
            return push_20(self, stix_file_doc, protocol_version='2.1')
        else:
            return push_11(self, stix_file_doc)
