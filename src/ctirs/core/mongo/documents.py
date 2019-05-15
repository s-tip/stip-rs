# -*- coding: utf-8 -*-
import os
import datetime
import pytz
from mongoengine import fields
from mongoengine.document import Document
from mongoengine.errors import DoesNotExist
from ctirs.models.rs.models import STIPUser,System
from ctirs import COMMUNITY_ORIGIN_DIR_NAME

class Communities(Document):
    NOT_ASSIGN_COMMUNITY_NAME = 'SYSTEM_RESERVED (Not Assign)'
    DEFAULT_COMMUNITY_NAME = 'Default Community'
    name = fields.StringField(unique=True,max_length=30)
    dir_path = fields.StringField(unique=True,max_length=1024)
    webhooks = fields.ListField()

    @classmethod
    def get_default_community(cls):
        return Communities.objects.get(name=cls.DEFAULT_COMMUNITY_NAME)

    @classmethod
    def get_not_assign_community(cls):
        try:
            return Communities.objects.get(name=Communities.NOT_ASSIGN_COMMUNITY_NAME)
        except:
            #新規作成する
            Communities.init_community(Communities.NOT_ASSIGN_COMMUNITY_NAME)
            #再度取得する
            return Communities.get_not_assign_community()

    @classmethod
    def get_clients_from_community(cls,community):
        l = []
        for taxii_client in TaxiiClients.objects.filter(community=community,push=True):
            from ctirs.core.taxii.taxii import Client
            l.append(Client(taxii_client=taxii_client))
        return l

    @classmethod
    #コミュニティ初期化
    def init_community(cls,community_name):
        #Community作成
        c = Communities()
        c.name = community_name
        c.save()
        try:
            #ディレクトリ名作成
            community_all_root_dir = System.objects.get_community_root_dir()
            community_root_dir = os.path.join(community_all_root_dir,str(c.id))
            #すでに存在する場合はエラー
            if os.path.exists(community_root_dir) == True:
                c.delete()
                raise Exception('Can\'t create directory (%s)' % ('because already exists.'))
            #ディレクトリ作成
            os.mkdir(community_root_dir)
            #originalディレクトリ作成
            origin_root_dir = os.path.join(community_root_dir,COMMUNITY_ORIGIN_DIR_NAME)
            os.mkdir(origin_root_dir)

            #Community更新
            c.dir_path = community_root_dir
            c.save()
        except Exception as e:
            c.delete()
            raise e
        return

    @classmethod
    #導入直後の初回起動時などにコレクションがないときに自動的に作成する
    def init_communities(cls):
        init_communities = ['Default Community', 'AlienVault OTX', 'MISP', 'stip-taxii-server', 'from_sns']
        for init_community in init_communities:
            Communities.init_community(init_community)

    def to_dict(self):
        return {
                'name'  :   self.name,
                'id'    :   str(self.id)
                }
#起動時に Communities を check する
#Communities　がない場合は作成する
try:
    if Communities.objects.count() == 0:
        Communities.init_communities()
except:
    #migrate 前に通過してエラーになるので例外は pass
    pass

class Webhooks(Document):
    url = fields.StringField(max_length=1024)

#Information Souces
class InformationSources(Document):
    name = fields.StringField(max_length=128,unique=True,null=False)

    @classmethod
    def create(cls,name):
        d = InformationSources()
        d.name =name
        d.save()
        return d
    
#TaxiiServerの設定
class TaxiiServers(Document):
    setting_name = fields.StringField(max_length=128,required=True,unique=True,null=False)
    collection_name = fields.StringField(max_length=128,required=True,unique=True,null=False)
    #中身は InforamtionSources
    information_sources = fields.ListField()

    @classmethod
    #create 時に設定名とコレクション名が必要
    def create(cls,setting_name,collection_name):
        ts = TaxiiServers()
        ts.setting_name = setting_name
        ts.collection_name = collection_name
        ts.save()
        return ts
    
    #information_sourcesを更新する
    def modify_information_sources(self,information_sources):
        self.information_sources = information_sources
        self.save()

#ScheduleCron設定保存クラス　
class ScheduleCronJobs(Document):
    @classmethod
    def create(cls,**kwargs):
        document = ScheduleCronJobs()
        try:
            document.year = kwargs['year']
        except KeyError:
            document.year = '*'
        try:
            document.month = kwargs['month']
        except KeyError:
            document.month = '*'
        try:
            document.day = kwargs['day']
        except KeyError:
            document.day = '*'
        try:
            document.week = kwargs['week']
        except KeyError:
            document.week = '*'
        try:
            document.hour = kwargs['hour']
        except KeyError:
            document.hour = '*'
        try:
            document.minute = kwargs['minute']
        except KeyError:
            document.minute = '*'
        try:
            document.second = kwargs['second']
        except KeyError:
            document.second = '*'
        document.save()
        return document
    year = fields.StringField(max_length=128,default='*')
    month = fields.StringField(max_length=128,default='*')
    day = fields.StringField(max_length=128,default='*')
    week = fields.StringField(max_length=128,default='*')
    hour = fields.StringField(max_length=128,default='*')
    minute = fields.StringField(max_length=128,default='*')
    second = fields.StringField(max_length=128,default='*')

#ScheduleInterval設定保存クラス　
class ScheduleIntervalJobs(Document):
    @classmethod
    def create(cls,**kwargs):
        document = ScheduleIntervalJobs()
        try:
            document.seconds = int(kwargs['seconds'])
        except KeyError:
            document.seconds = '*'
        document.save()
        return document
    seconds = fields.IntField()

#ScheduleJobsクラス
class ScheduleJobs(Document):
    JOB_CRON = 'cron'
    JOB_INTERVAL = 'interval'
    STATUS_IN_OPERATION = 'in_operation'
    STATUS_STOP = 'stop'

    JOB_TYPES=(
        (JOB_CRON,      'cron'),
        (JOB_INTERVAL,  'interval'),
    )

    STATSES=(
        (STATUS_IN_OPERATION    ,'In Operation'),
        (STATUS_STOP           ,'Stop'),
    )

    @classmethod
    def create(cls,type_,**kwargs):
        if type_ == cls.JOB_CRON:
            cron_job = ScheduleCronJobs.create(**kwargs)
            document = ScheduleJobs()
            document.job_type = cls.JOB_CRON
            document.cron_job = cron_job
            document.status = cls.STATUS_STOP
            document.save()
            return document
        elif type_ == cls.JOB_INTERVAL:
            interval_job = ScheduleIntervalJobs.create(**kwargs)
            document = ScheduleJobs()
            document.job_type = cls.JOB_INTERVAL
            document.interval_job = interval_job
            document.status = cls.STATUS_STOP
            document.save()
            return document
    
    def remove(self):
        if self.job_type == self.JOB_CRON:
            self.cron_job.delete()
        elif self.job_type == self.JOB_INTERVAL:
            self.interval_job.delete()
        self.delete()

    job_type = fields.StringField(max_length=32,choices=JOB_TYPES)
    cron_job = fields.ReferenceField(ScheduleCronJobs)
    interval_job = fields.ReferenceField(ScheduleIntervalJobs)
    status = fields.StringField(max_length=32,choices=STATSES)

class OtxAdapter(Document):
    @classmethod
    def get(cls):
        try:
            otx = OtxAdapter.objects.get()
        except DoesNotExist:
            otx = OtxAdapter()
            otx.apikey = None
            otx.last_requested = None
            otx.save()
        return otx

    @classmethod
    def modify_settings(cls,apikey,community_id,uploader_id):
        community = Communities.objects.get(id=community_id)
        otx = OtxAdapter.objects.get()
        otx.community = community
        otx.apikey = apikey
        otx.uploader = uploader_id
        otx.save()

    @classmethod
    def modify_last_requested(cls):
        otx = OtxAdapter.objects.get()
        otx.last_requested = datetime.datetime.now(pytz.utc)
        otx.save()

    @classmethod
    #job追加
    def add_job(cls,type_,**kwargs):
        job = ScheduleJobs.create(type_,**kwargs)
        otx = OtxAdapter.objects.get()
        if job.job_type == ScheduleJobs.JOB_CRON:
            #type が cron の場合はリストに追加
            otx.jobs.append(job)
            otx.save()
        elif job.job_type == ScheduleJobs.JOB_INTERVAL:
            #type が interval の場合は document を 更新
            if otx.interval_schedule_job is not None:
                otx.interval_schedule_job.interval_job.delete()
                otx.interval_schedule_job.delete()
            otx.interval_schedule_job = job
            otx.save()
        return job

    @classmethod
    #job削除
    def remove_job(cls,jobs_id):
        job = ScheduleJobs.objects.get(id=jobs_id)
        otx = OtxAdapter.objects.get()
        otx.jobs.remove(job)
        otx.save()
        return
    
    @classmethod
    #job削除
    def remove_internal_job(cls):
        otx = OtxAdapter.objects.get()
        if otx.interval_schedule_job is not None:
            otx.interval_schedule_job.interval_job.delete()
            otx.interval_schedule_job.delete()
            otx.interval_schedule_job = None
            otx.save()    
            
    @property
    def uploader_name(self):
        otx = OtxAdapter.objects.get()
        return STIPUser.objects.get(id=otx.uploader).username

    #uploader には STIPUser の ID を格納
    uploader = fields.IntField()
    apikey = fields.StringField(max_length=100)
    last_requested = fields.DateTimeField(default=None)
    community = fields.ReferenceField(Communities)
    jobs = fields.ListField()
    interval_schedule_job = fields.ReferenceField(ScheduleJobs)

class isightAdapter(Document):
    @classmethod
    def get(cls):
        try:
            isight = isightAdapter.objects.get()
        except DoesNotExist:
            isight = isightAdapter()
            isight.public_key = None
            isight.private_key = None
            isight.last_requested = None
            isight.save()
        return isight

    @classmethod
    def modify_settings(cls,public_key,private_key,community_id,uploader_id):
        community = Communities.objects.get(id=community_id)
        isight = isightAdapter.objects.get()
        isight.community = community
        isight.public_key = public_key
        isight.private_key = private_key
        isight.uploader = uploader_id
        isight.save()

    @classmethod
    def modify_last_requested(cls):
        isight = isightAdapter.objects.get()
        isight.last_requested = datetime.datetime.now(pytz.utc)
        isight.save()

    @classmethod
    #job追加
    def add_job(cls,type_,**kwargs):
        job = ScheduleJobs.create(type_,**kwargs)
        isight = isightAdapter.objects.get()
        if job.job_type == ScheduleJobs.JOB_CRON:
            #type が cron の場合はリストに追加
            isight.jobs.append(job)
            isight.save()
        elif job.job_type == ScheduleJobs.JOB_INTERVAL:
            #type が interval の場合は document を 更新
            if isight.interval_schedule_job is not None:
                isight.interval_schedule_job.interval_job.delete()
                isight.interval_schedule_job.delete()
            isight.interval_schedule_job = job
            isight.save()
        return job

    @classmethod
    #job削除
    def remove_job(cls,jobs_id):
        job = ScheduleJobs.objects.get(id=jobs_id)
        isight = isightAdapter.objects.get()
        isight.jobs.remove(job)
        isight.save()
        return

    @classmethod
    #job削除
    def remove_internal_job(cls):
        isight = isightAdapter.objects.get()
        if isight.interval_schedule_job is not None:
            isight.interval_schedule_job.interval_job.delete()
            isight.interval_schedule_job.delete()
            isight.interval_schedule_job = None
            isight.save()

    @property
    def uploader_name(self):
        otx = OtxAdapter.objects.get()
        return STIPUser.objects.get(id=otx.uploader).username

    #uploader には STIPUser の ID を格納
    uploader = fields.IntField()
    public_key = fields.StringField(max_length=100)
    private_key = fields.StringField(max_length=100)
    last_requested = fields.DateTimeField(default=None)
    community = fields.ReferenceField(Communities)
    jobs = fields.ListField()
    interval_schedule_job = fields.ReferenceField(ScheduleJobs)

class MispAdapter(Document):
    @classmethod
    def get(cls):
        try:
            misp = MispAdapter.objects.get()
        except DoesNotExist:
            misp = MispAdapter()
            misp.url = None
            misp.apikey = None
            misp.last_requested = None
            misp.save()
        return misp

    @classmethod
    def modify_settings(cls,url,apikey,identity,community_id,uploader_id,published_only):
        community = Communities.objects.get(id=community_id)
        misp = MispAdapter.objects.get()
        misp.community = community
        misp.url = url
        misp.apikey = apikey
        misp.identity = identity
        misp.uploader = uploader_id
        misp.published_only = published_only
        misp.save()

    @classmethod
    def modify_last_requested(cls):
        misp = MispAdapter.objects.get()
        misp.last_requested = datetime.datetime.now(pytz.utc)
        misp.save()

    @classmethod
    #job追加
    def add_job(cls,type_,**kwargs):
        job = ScheduleJobs.create(type_,**kwargs)
        misp = MispAdapter.objects.get()
        if job.job_type == ScheduleJobs.JOB_CRON:
            #type が cron の場合はリストに追加
            misp.jobs.append(job)
            misp.save()
        elif job.job_type == ScheduleJobs.JOB_INTERVAL:
            #type が interval の場合は document を 更新
            if misp.interval_schedule_job is not None:
                misp.interval_schedule_job.interval_job.delete()
                misp.interval_schedule_job.delete()
            misp.interval_schedule_job = job
            misp.save()
        return job

    @classmethod
    #job削除
    def remove_job(cls,jobs_id):
        job = ScheduleJobs.objects.get(id=jobs_id)
        misp = MispAdapter.objects.get()
        misp.jobs.remove(job)
        misp.save()
        return

    @classmethod
    #job削除
    def remove_internal_job(cls):
        misp = MispAdapter.objects.get()
        if misp.interval_schedule_job is not None:
            misp.interval_schedule_job.interval_job.delete()
            misp.interval_schedule_job.delete()
            misp.interval_schedule_job = None
            misp.save()

    @property
    def uploader_name(self):
        misp = MispAdapter.objects.get()
        return STIPUser.objects.get(id=misp.uploader).username

    #uploader には STIPUser の ID を格納
    uploader = fields.IntField()
    url = fields.StringField(max_length=1024)
    apikey = fields.StringField(max_length=100)
    identity = fields.StringField(max_length=100)
    published_only = fields.BooleanField(default=True)
    last_requested = fields.DateTimeField(default=None)
    community = fields.ReferenceField(Communities)
    jobs = fields.ListField()
    interval_schedule_job = fields.ReferenceField(ScheduleJobs)

#起動時に各種アダプタ collectionを check する。存在しない場合は作成してくれる
if OtxAdapter.objects.count() == 0:
    adapter = OtxAdapter()
    adapter.save()
if isightAdapter.objects.count() == 0:
    adapter = isightAdapter()
    adapter.save()
if MispAdapter.objects.count() == 0:
    adapter = MispAdapter()
    adapter.save()

class TaxiiClients(Document):
    TAXII_PROTOCOL_VERSION_CHOICES=(
        ('1.1','1.1'),
        ('2.0','2.0'),
    )

    @classmethod
    def get_protocol_versions(cls):
        l = []
        for choice in cls.TAXII_PROTOCOL_VERSION_CHOICES:
            l.append(choice[0])
        return l

    @classmethod
    def create(cls,name,address='',port=0,ssl=False,path='',collection='',login_id='',login_password='',community_id='',ca=False,key_file=None,cert_file=None,protocol_version='',push=False,uploader_id=None):
        community = Communities.objects.get(id=community_id)
        try:
            t = TaxiiClients.objects.get(name=name)
        except DoesNotExist:
            t = TaxiiClients()
            t.last_requested = None
        t.address = address
        t.name = name
        t.port = port
        t.ssl = ssl
        t.path = path
        t.collection = collection
        t.login_id = login_id
        t.login_password = login_password
        t.community = community
        t.is_use_cert = ca
        if ca is True:
            t.key_file = key_file
            t.cert_file = cert_file
        else:
            t.key_file = None
            t.cert_file = None
        t.protocol_version = protocol_version
        t.push = push
        t.uploader = uploader_id
        t.save()
        return

    #job追加
    def add_job(self,type_,**kwargs):
        job = ScheduleJobs.create(type_,**kwargs)
        if job.job_type == ScheduleJobs.JOB_CRON:
            #type が cron の場合はリストに追加
            self.jobs.append(job)
            self.save()
        elif job.job_type == ScheduleJobs.JOB_INTERVAL:
            #type が interval の場合は document を 更新
            if self.interval_schedule_job is not None:
                self.interval_schedule_job.interval_job.delete()
                self.interval_schedule_job.delete()
            self.interval_schedule_job = job
            self.save()
        return job

    #job削除
    def remove_job(self,jobs_id):
        job = ScheduleJobs.objects.get(id=jobs_id)
        self.jobs.remove(job)
        self.save()

    #job削除(interval)
    def remove_interval_job(self):
        if self.interval_schedule_job is not None:
            self.interval_schedule_job.interval_job.delete()
            self.interval_schedule_job.delete()
            self.save()
        
    #template表示用/communityが削除されずに残っているか
    def is_exist_community(self):
        try:
            v = self.community
            return v == self.community
        except DoesNotExist:
            return False

    @property
    def uploader_name(self):
        return STIPUser.objects.get(id=self.uploader).username

    name = fields.StringField(max_length=100,unique=True)
    address = fields.StringField(max_length=100,default='localhost')
    port = fields.IntField(default=80)
    ssl = fields.BooleanField(default=False)
    path = fields.StringField(max_length=100,default='/taxii-data')
    collection = fields.StringField(max_length=100,default='Default')
    login_id = fields.StringField(max_length=100,default='login_id')
    login_password = fields.StringField(max_length=100,default='login_password')
    community = fields.ReferenceField(Communities)
    is_use_cert = fields.BooleanField(default=False)
    cert_file = fields.StringField(max_length=10240)
    key_file = fields.StringField(max_length=10240)
    last_requested = fields.DateTimeField(default=None)
    protocol_version = fields.StringField(max_length=16,choices=TAXII_PROTOCOL_VERSION_CHOICES,default='1.1')
    push = fields.BooleanField(default=False)
    #uploader には STIPUser の ID を格納
    uploader = fields.IntField()
    jobs = fields.ListField()
    interval_schedule_job = fields.ReferenceField(ScheduleJobs)

class Vias(Document):
    VIA_CHOICES=(
        ('file_upload','Local File'),
        ('taxii_poll','Taxii Poll'),
        ('adapter','Adapter'),
        ('rest','Rest API'),
        ('taxii_publish','Taxii Publish'),
        ('not_assign','NOT ASSIGN'),
    )

    via = fields.StringField(max_length=32,choices=VIA_CHOICES)
    #uploader には STIPUser の ID を格納
    uploader = fields.IntField()
    taxii_client = fields.ReferenceField(TaxiiClients)
    adapter_name = fields.StringField(max_length=32)
    taxii_publisher = fields.StringField(max_length=32)

    @classmethod
    def get_not_assign_via(cls,uploader=None):
        via = 'not_assign'
        try:
            #すでにある場合は返却
            return Vias.objects.get(via=via,uploader=uploader)
        except DoesNotExist:
            #存在しない場合は新規作成/保存後返却
            document = Vias()
            document.via = via
            document.uploader = uploader
            document.save()
            return document

    @classmethod
    def get_via_file_upload(cls,uploader=None):
        via = 'file_upload' 
        try:
            #すでにある場合は返却
            return Vias.objects.get(via=via,uploader=uploader)
        except DoesNotExist:
            #存在しない場合は新規作成/保存後返却
            document = Vias()
            document.via = via
            document.uploader = uploader
            document.save()
            return document

    @classmethod
    def get_via_rest_api_upload(cls,uploader=None):
        via = 'rest' 
        try:
            #すでにある場合は返却
            return Vias.objects.get(via=via,uploader=uploader)
        except DoesNotExist:
            #存在しない場合は新規作成/保存後返却
            document = Vias()
            document.via = via
            document.uploader = uploader
            document.save()
            return document

    @classmethod
    def get_via_taxii_poll(cls,taxii_client=None,uploader=None):
        via = 'taxii_poll' 
        try:
            #すでにある場合は返却
            return Vias.objects.get(via=via,taxii_client=taxii_client,uploader=uploader)
        except DoesNotExist:
            #存在しない場合は新規作成/保存後返却
            document = Vias()
            document.via = via
            document.taxii_client = taxii_client
            document.uploader = uploader
            document.save()
            return document

    @classmethod
    def get_via_adapter(cls,via,adapter_name,uploader=None):
        try:
            #すでにある場合は返却
            return Vias.objects.get(via=via,adapter_name=adapter_name,uploader=uploader)
        except DoesNotExist:
            #存在しない場合は新規作成/保存後返却
            document = Vias()
            document.via = via
            document.adapter_name = adapter_name
            document.uploader = uploader
            document.save()
            return document

    @classmethod
    def get_via_adapter_otx(cls,uploader=None):
        via = 'adapter' 
        adapter_name = 'AlienVault'
        return cls.get_via_adapter(via,adapter_name,uploader)

    @classmethod
    def get_via_adapter_isight(cls,uploader=None):
        via = 'adapter' 
        adapter_name = 'iSIGHT Partners'
        return cls.get_via_adapter(via,adapter_name,uploader)

    @classmethod
    def get_via_adapter_misp(cls,uploader=None):
        via = 'adapter' 
        adapter_name = 'MISP'
        return cls.get_via_adapter(via,adapter_name,uploader)

    @classmethod
    def get_via_taxii_publish(cls,taxii_publisher='undefined'):
        via = 'taxii_publish' 
        try:
            #すでにある場合は返却
            return Vias.objects.get(via=via,taxii_publisher=taxii_publisher)
        except DoesNotExist:
            #存在しない場合は新規作成/保存後返却
            document = Vias()
            document.via = via
            document.taxii_publisher = taxii_publisher
            document.save()
            return document

    #uploaderから screen_name 取得
    def get_screen_name_from_uploader(self):
        try:
            return STIPUser.objects.get(id=self.uploader).screen_name 
        except:
            #uploaderがない場合
            return 'undefined'

    #uploaderのscreen_nameを取得
    def get_uploader_screen_name(self):
        try:
            if self.via == 'taxii_poll':
                if self.uploader is not None:
                    #uploaderの指定がある場合
                    return self.get_screen_name_from_uploader()
                else:
                    #uploaderの指定がない場合は adapter 名
                    return self.taxii_client.name
            elif self.via == 'rest':
                #restの場合はuploader
                return self.get_screen_name_from_uploader()
            elif self.via == 'file_upload':
                #file_uploadの場合はuploader
                return self.get_screen_name_from_uploader()
            elif self.via == 'adapter':
                if self.uploader is not None:
                    #uploaderの指定がある場合
                    return self.get_screen_name_from_uploader()
                else:
                    #uploaderの指定がない場合は adapter 名
                    return self.adapter_name
            elif self.via == 'taxii_publish':
                #taxii_publishの場合はpublisher名
                return self.taxii_publisher
            elif self.via == 'not_assign':
                return self.get_screen_name_from_uploader()
            else:
                return 'undefined'
        except:
            #設定やユーザが削除されてエラーの場合は undefined とする
            return 'undefined'
        
    #sSearchを含むVIA_CHOICESを返却する
    @classmethod
    def get_search_via_choices(cls,sSearch):
        ret = []
        for choice in cls.VIA_CHOICES:
            v1,v2 = choice
            if sSearch.upper() in v2.upper():
                ret.append(v1)
        return ret

