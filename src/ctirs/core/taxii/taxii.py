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
from urllib.parse import urlparse
#from xml.dom.minidom import parseString
from ctirs.core.mongo.documents import TaxiiClients, Vias, ScheduleJobs
from ctirs.core.schedule.schedule import CtirsScheduler
from ctirs.models.rs.models import System


class Client(object):
    _SUBSCRIPTION_ID = 'CTI Repository System.'
    TAXII_2_ACCEPT = 'application/vnd.oasis.taxii+json; version=2.0'
    PLUG_FEST_AUTH_STRING = 'Basic dGVzDoxMjPCow=='
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

        # taxii client設定
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

        # proxy 設定があれば設定する
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
        # _scheduleのstartはschedule単位
        # modify/resume/pauseはjob単位

        # TAXII Protocol 1.1 なら Authentication 設定を行う
        if self._protocol_version == '1.1':
            self.set_taxii_11_authentication()

    # TAXII Protocol 1.1 の Authentication 設定を行う
    def set_taxii_11_authentication(self):
        try:
            # auth
            cert_file = None
            key_file = None

            # SSL使用設定
            self._client.set_use_https(self._ssl)
            # 認証タイプ
            self._client.set_auth_type(self._auth_type)
            # BASIC認証情報
            auth_credentials_dict = {}
            auth_credentials_dict['username'] = self._username
            auth_credentials_dict['password'] = self._password
            # 証明書認証の場合は情報追加
            if self._auth_type == clients.HttpClient.AUTH_CERT_BASIC:
                # certificate/private_keyの一時ファイルを作成
                _, cert_file = tempfile.mkstemp()
                with open(cert_file, 'w') as fp:
                    fp.write(self._cert_file)
                _, key_file = tempfile.mkstemp()
                with open(key_file, 'w') as fp:
                    fp.write(self._key_file)
                auth_credentials_dict['cert_file'] = cert_file
                auth_credentials_dict['key_file'] = key_file
            # 認証情報設定
            self._client.set_auth_credentials(auth_credentials_dict)

        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            # 一時ファイルを削除
            if cert_file is not None:
                os.remove(cert_file)
            if key_file is not None:
                os.remove(key_file)

    # TAXII 2.0 用 GET request Header

    def get_taxii_20_get_request_header(self):
        return {
            'Accept': self.TAXII_2_ACCEPT,
            'Authorization': self.PLUG_FEST_AUTH_STRING,
        }

    # TAXII 2.0 用 POST request Header
    def get_taxii_20_post_request_header(self):
        return {
            'Accept': self.TAXII_2_ACCEPT,
            'Authorization': self.PLUG_FEST_AUTH_STRING,
            'Content-Type': self.TAXII_2_PUBLICATION_CONTENT_TYPE,
        }

    # set start time
    def set_start_time(self, start):
        self._start = start

    # set end time
    def set_end_time(self, end):
        self._end = end

    # add job
    def add_job(self, schedule_job):
        self._schedule.add_job(schedule_job, self.poll_job)
        self._schedule.start_job(schedule_job)

    # resume job
    def resume_job(self, job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        # interval job と一緒の場合
        if self._interval_job == schedule_job:
            if schedule_job.status == ScheduleJobs.STATUS_STOP:
                pass
            else:
                print('already working.')
            return
        # schedule_jobと一緒(cron_jobリストにふくまれている)
        if schedule_job in self._jobs:
            if schedule_job.status == ScheduleJobs.STATUS_STOP:
                pass
            else:
                print('already working.')
                return
        else:
            raise Exception('invalid job_id')
        self._schedule.resume_job(schedule_job)

    # stop job
    def pause_job(self, job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        # interval job と一緒の場合
        if self._interval_job == schedule_job:
            if schedule_job.status == ScheduleJobs.STATUS_IN_OPERATION:
                pass
            else:
                print('not yet start.')
            return
        if schedule_job in self._jobs:
            if schedule_job.status == ScheduleJobs.STATUS_IN_OPERATION:
                pass
            else:
                print('not yet start.')
                return
        else:
            raise Exception('invalid job_id')
            return
        self._schedule.pause_job(schedule_job)

    # remove_job job
    def remove_job(self, job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        # スケジューラからjob削除
        self._schedule.remove_job(schedule_job)
        # mongoのジョブ情報削除
        schedule_job.remove()

    # remove_job job(interval)
    def remove_interval_job(self):
        if self._interval_job is None:
            # まだ設定されていない
            return
        schedule_job = ScheduleJobs.objects.get(id=self._interval_job.id)
        # スケジューラからjob削除
        self._schedule.remove_job(schedule_job)
        # ScheduleJobs と ScheduleIntervalJobs を削除
        schedule_job.remove()
        self._interval_job = None

    # poll for job
    def poll_job(self):
        if self._taxii.last_requested is not None:
            self.set_start_time(self._taxii.last_requested.replace(tzinfo=pytz.utc))
            self.poll()

    # poll entry
    def poll(self):
        if self._protocol_version == '2.0':
            return self.poll_20()
        else:
            return self.poll_11()

    # poll(version 1.1) entry
    def poll_11(self):
        # request xml作成
        poll_parameters = tm11.PollParameters()
        poll_request = tm11.PollRequest(
            message_id=tm11.generate_message_id(),
            collection_name=self._collection_name,
            exclusive_begin_timestamp_label=self._start,
            inclusive_end_timestamp_label=self._end,
            poll_parameters=poll_parameters,
        )
        last_requested = datetime.datetime.now(pytz.utc)

        #from xml.dom.minidom import parseString
        #print( parseString(poll_request.to_xml()).toprettyxml(encoding='utf-8'))

        # request
        http_resp = self._client.call_taxii_service2(
            self._address,
            self._path,
            const.VID_TAXII_XML_11,
            poll_request.to_xml(),
            port=self._port)

        # taxii_message抽出
        taxii_message = libtaxii.get_message_from_http_response(http_resp, poll_request.message_id)

        # content_blocks が None or 存在しない場合は登録ししない
        try:
            if taxii_message.content_blocks is None:
                return 0
        except AttributeError:
            return 0

        # content_blocksごとに登録処理
        count = 0
        for cb in taxii_message.content_blocks:
            # stixファイルを一時ファイルに出力
            _, stix_file_path = tempfile.mkstemp(suffix='.xml')
            with open(stix_file_path, 'wb+') as fp:
                # cb.contentがstixの中身
                fp.write(cb.content)
            # 登録
            try:
                from ctirs.core.stix.regist import regist
                if self._community is not None:
                    regist(stix_file_path, self._community, self._via)
                count += 1
            except BaseException:
                # taxiiの場合は途中で失敗しても処理を継続する
                traceback.print_exc()

        # last_requested更新
        self._taxii.last_requested = last_requested
        self._taxii.save()

        return count

    def debug_print(self, msg):
        print(msg)

    # poll, push 共通 base_url 取得
    def get_taxii20_base_url(self):
        self.debug_print('>>> get_taxii20_base_url enter')

        # Basic TXS Get
        url = '%s:%d%s/' % (self._address, self._port, self._path)
        headers = {
            "Accept": "application/vnd.oasis.taxii+json; version=2.0",
        }
        self.debug_print('get_taxii20_base_url: URL: %s' % (url))
        self.debug_print('get_taxii20_base_url: _username: %s' % (self._username))
        self.debug_print('get_taxii20_base_url: _password: %s' % (self._password))
        self.debug_print('get_taxii20_base_url: request headers:%s' % (json.dumps(headers, indent=4)))
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
        self.debug_print('get_taxii20_base_url: response status_code:%s' % (resp.status_code))

        self.debug_print(resp.text)
        j = resp.json()
        self.debug_print('----')
        self.debug_print(json.dumps(j, indent=4))
        self.debug_print('----')

        base_url = None
        if ('default' in j):
            base_url = j['default']
        else:
            # default がない場合は url を使う
            base_url = url
        self.debug_print('get_taxii20_base_url: base_url:%s' % (base_url))
        return base_url

    # poll, push 共通 objects_url 取得
    def get_taxii20_objects_url(self):
        # base_url 取得
        base_url = self.get_taxii20_base_url()
        if base_url is None:
            self.debug_print('>>> get_taxii20_objects_url: No base_url')
            return None
        if base_url[-1] != '/':
            base_url = base_url + '/'
        url = base_url + 'collections/' + self._collection_name + '/objects/'
        return url

    # poll(version 2.0) entry

    def poll_20(self):
        self.debug_print('>>> poll_20:enter')

        url = self.get_taxii20_objects_url()
        if url is None:
            self.debug_print('>>> poll_20: No base_url')
            return 0
        headers = {
            'Accept': 'application/vnd.oasis.stix+json; version=2.0',
        }
        self.debug_print('poll_20: URL: %s' % (url))
        self.debug_print('poll_20: request headers:%s' % (json.dumps(headers, indent=4)))

        resp = requests.get(
            url,
            headers=headers,
            auth=(self._username, self._password),
            verify=False,
            proxies=self._proxies
        )
        self.debug_print('poll_20: response status_code:%s' % (resp.status_code))
        #self.debug_print('poll_20: response headers')
        # for k,v in resp.headers.iteritems():
        #    self.debug_print('%s: %s' % (k,v))
        # self.debug_print('----')
        #self.debug_print('poll_20: request resp.json():%s' % (json.dumps(resp.json(),indent=4)))

        # stix のリストで返却される
        count = 0
        stixes = []
        js = resp.json()
        # list で返却される場合と単体の場合がある
        if isinstance(js, list):
            stixes = js
        else:
            stixes = [js]
        for j in stixes:
            # 1つずつ file に保存して regist する
            # stixファイルを一時ファイルに出力
            _, stix_file_path = tempfile.mkstemp(suffix='.json')
            with open(stix_file_path, 'wb+') as fp:
                fp.write(json.dumps(j, indent=4))
            # 登録
            try:
                from ctirs.core.stix.regist import regist
                if self._community is not None:
                    regist(stix_file_path, self._community, self._via)
                count += 1
            except BaseException:
                # taxiiの場合は途中で失敗しても処理を継続する
                traceback.print_exc()
                pass

        last_requested = datetime.datetime.now(pytz.utc)
        self._taxii.last_requested = last_requested
        self._taxii.save()
        return count

    # push entry
    def push(self, stix_file_doc):
        self.debug_print('>>> push: enter')
        if self._protocol_version == '2.0':
            self.push_20(stix_file_doc)
        else:
            self.push_11(stix_file_doc)

    # push(version 1.1) entry
    def push_11(self, stix_file_doc):
        self.debug_print('>>> push_11: enter')
        # stix_file_doc の versionが 2.0 ならスライド
        if stix_file_doc.version == '2.0':
            try:
                content = stix_file_doc.get_slide_1_x()
            except Exception as e:
                traceback.print_exc()
                raise e

        else:
            with open(stix_file_doc.origin_path, 'r') as fp:
                content = fp.read()

        # Subscription Information xml作成
        subscription_information = tm11.SubscriptionInformation(
            collection_name=self._collection_name,
            subscription_id='subscripiton_id')
        cb = tm11.ContentBlock(const.CB_STIX_XML_11, content)
        im = tm11.InboxMessage(
            message_id=tm11.generate_message_id(),
            destination_collection_names=[self._collection_name],
            subscription_information=subscription_information,
            content_blocks=[cb])
        try:
            # push
            self._address = '10.0.3.100'
            #self.debug_print('>>> push_11: self._address:%s' %(self._address))
            #self.debug_print('>>> push_11: self._path:%s' %(self._path))
            #self.debug_print('>>> push_11: self._port:%d' %(self._port))
            #self.debug_print('>>> push_11: self._collection_name:%s' %(self._collection_name))
            #self.debug_print('>>> push_11: verify_server:%s' %(str(self._client.verify_server)))
            #self.debug_print('>>> push_11: use_https:%s' %(str(self._client.use_https)))
            http_resp = self._client.call_taxii_service2(
                self._address,
                self._path,
                const.VID_TAXII_XML_11,
                im.to_xml(),
                port=self._port)
            taxii_message = libtaxii.get_message_from_http_response(http_resp, im.message_id)
            if taxii_message.status_type != 'SUCCESS':
                self.debug_print('taxii_message.status_type is not SUCCESS')
                self.debug_print(taxii_message.to_xml(pretty_print=True))
                raise Exception('taxii_message.status_type is not SUCCESS')
        except Exception as e:
            traceback.print_exc()
            self.debug_print(e)
            raise e

    # push(version 2.0) entry
    def push_20(self, stix_file_doc):
        self.debug_print('>>> push_20: enter')
        # stix_file_doc の versionが 2.0以外 ならelevate
        if stix_file_doc.version != '2.0':
            content = stix_file_doc.get_elevate_2_x()
        else:
            with open(stix_file_doc.origin_path, 'r') as fp:
                content = fp.read()

        '''
        #Data1/Write Collection
        url = '%s:%d%s' % (self._address,self._port,self._path)
        #print '>>>push_20'
        print '>>>push_20:url : %s' % (url)

        #TEST_DATA_1_ID = '91a7b528-80eb-42ed-a74d-bd5a2116'
        #TEST_DATA_1_VERIFICATION_URL = 'https://10.1.1.10/api1/collections/91a7b528-80eb-42ed-a74d-bd5a2116/'
        #TEST_DATA_1_PUBLICATION_URL = 'https://10.1.1.10/api1/collections/91a7b528-80eb-42ed-a74d-bd5a2116/objects'
        verification_url = url + 'collections/' + self._collection_name +'/'
        #print '>>>push_20:verification_url : %s' % (verification_url)
        #verification_url = url + 'collections/' + '91a7b528-80eb-42ed-a74d-bd5a2116' +'/'
        publication_url = verification_url + 'objects/'
        print '>>>push_20:publication_url : %s' % (publication_url)
        #TEST_DATA_1_TITLE = 'Write Collection 1'
        #TEST_DATA_1_DESCRIPTION = 'This is Write collection 1'
        #TEST_DATA_1_CAN_READ = False
        #TEST_DATA_1_CAN_WRITE = True
        #TEST_DATA_1_MEDIA_TYPES = [ "application/vnd.oasis.stix+json; version=2.0" ]

        #Data2/Read Collection
        #TEST_DATA_2_ID = '91a7b528-80eb-42ed-a74d-bd526120'
        #TEST_DATA_2_VERIFICATION_URL = 'https://10.1.1.10/api1/collections/91a7b528-80eb-42ed-a74d-bd526120/'
        #TEST_DATA_2_PUBLICATION_URL = 'https://10.1.1.10/api1/collections/91a7b528-80eb-42ed-a74d-bd526120/objects'
        #TEST_DATA_2_TITLE = 'Read Collection 1'
        #TEST_DATA_2_DESCRIPTION = 'This is read collection 1'
        #TEST_DATA_2_CAN_READ = True
        #TEST_DATA_2_CAN_WRITE = False
        #TEST_DATA_2_MEDIA_TYPES = [ "application/vnd.oasis.stix+json; version=2.0" ]

        #Data3/Read_Write Collection
        #TEST_DATA_3_ID = '91a7b528-80eb-42ed-a74d-bd5a2118'
        #TEST_DATA_3_VERIFICATION_URL = 'https://10.1.1.10/api1/collections/91a7b528-80eb-42ed-a74d-bd5a2118/'
        #TEST_DATA_3_PUBLICATION_URL = 'https://10.1.1.10/api1/collections/91a7b528-80eb-42ed-a74d-bd5a2118/objects'
        #TEST_DATA_3_TITLE = 'Read-Write Collection 1'
        #TEST_DATA_3_DESCRIPTION = 'This is read-write collection 1'
        #TEST_DATA_3_CAN_READ = True
        #TEST_DATA_3_CAN_WRITE = True
        #TEST_DATA_3_MEDIA_TYPES = [ "application/vnd.oasis.stix+json; version=2.0" ]
        '''

        '''
        #Verify Collection Information
        headers = {
             "Accept": "application/vnd.oasis.taxii+json; version=2.0",
        }
        print 'taxii_push_20: verification:request headers:%s' % (json.dumps(headers,indent=4))
        print 'taxii_push_20: verification:request url:%s' % (verification_url)
        #print 'taxii_push_20: verification:request headers:%s' % (json.dumps(self.get_taxii_20_get_request_header(),indent=4))
        resp = requests.post(
            verification_url,
            #headers = self.get_taxii_20_get_request_header(),
            headers = headers,
            auth = (self._username,self._password),
            verify = False
            proxies = self._proxies
        )
        print resp
        print resp.status_code
        print resp.headers

        #if resp.status_code != 200 and resp.status_code != 202:
        if resp.status_code != 200:
            #error
            print 'taxii_push_20: verification:response_code:%d. Exit.' % (resp.status_code)
            return
        '''

        '''
        try:
            #check response parameter
            j = resp.json()
            #if j['id'] != TEST_DATA_1_ID:
            if j['id'] != self._collection_name:
                print 'taxii_push_20: verification: Invalid ID(%s). Exit.' % (j['id'])
                return
            if j['title'] != TEST_DATA_1_TITLE:
                print 'taxii_push_20: verification: Invalid title(%s). Exit.' % (j['title'])
                return
            if j['description'] != TEST_DATA_1_DESCRIPTION:
                print 'taxii_push_20: verification: Invalid description(%s). Exit.' % (j['description'])
                return
            if j['can_read'] != TEST_DATA_1_CAN_READ:
                print 'taxii_push_20: verification: Invalid can_read(%s). Exit.' % (str(j['can_read']))
                return
            if j['can_write'] != TEST_DATA_1_CAN_WRITE:
                print 'taxii_push_20: verification: Invalid can_write(%s). Exit.' % (str(j['can_write']))
                return
            if j['media_types'] != TEST_DATA_1_MEDIA_TYPES:
                print 'taxii_push_20: verification: Invalid media_types(%s). Exit.' % (str(j['media_types']))
                return
        except:
            traceback.print_exc()
            return
        '''

        '''
        INDICATOR_DATA = {
            "type": "bundle",
            "id": "bundle--5d0092c5-5f74-4287-9642-33f4c354e56d",
            "spec_version": "2.0",
            "objects": [
                {
                  "type": "identity",
                  "name": "ACME Corp, Inc.",
                  "identity_class": "organization",
                  "id": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff"
                },
                {
                  "type": "indicator",
                  "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                  "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                  "created": "2016-04-06T20:03:48.000Z",
                  "modified": "2016-04-06T20:03:48.000Z",
                  "labels": [
                      "Malicious IP"
                      ],
                  "name": "Bad IP1",
                  "description": "This indicator should be monitored for malicious activity",
                  "pattern": "[ ipv4-addr:value: = '198.51.100.1' ]",
                  "valid_from": "2016-01-01T00:00:00Z"
                  }
            ]
        }
        '''

        # Publication
        # print 'taxii_push_20: publication:request headers:%s' % (json.dumps(self.get_taxii_20_post_request_header(),indent=4))
        url = self.get_taxii20_objects_url()
        self.debug_print('taxii_push_20: url:%s' % (url))
        headers = {
            "Accept": "application/vnd.oasis.taxii+json; version=2.0",
            "Content-Type": "application/vnd.oasis.stix+json; version=2.0"
        }
        self.debug_print('taxii_push_20: publication:request headers:%s' % (json.dumps(headers, indent=4)))
        resp = requests.post(
            url,
            headers=headers,
            auth=(self._username, self._password),
            data=content,
            verify=False,
            proxies=self._proxies
        )
        self.debug_print('taxii_push_20: resp.status_code: %s' % (resp.status_code))

        if resp.status_code != 202:
            # error
            self.debug_print('taxii_push_20: publication: response_code:%d. Exit.' % (resp.status_code))
            raise Exception('Invalid http response: %s' % (resp.status_code))

        try:
            # check response parameter
            j = resp.json()
            # self.debug_print(json.dumps(j,indent=4))
            if j['status'] != 'complete':
                self.debug_print('taxii_push_20: publication: Invalid status(%s). Exit.' % (j['status']))
                return
            if j['failure_count'] != 0:
                self.debug_print('taxii_push_20: publication: Invalid failure_count(%d). Exit.' % (j['failure_count']))
                return
            if j['pending_count'] != 0:
                self.debug_print('taxii_push_20: publication: Invalid pending_count(%d). Exit.' % (j['pending_count']))
                return
        except Exception as e:
            traceback.print_exc()
            raise e
