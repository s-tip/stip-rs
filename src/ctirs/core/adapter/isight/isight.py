# -*- coding: utf-8 -*
import email
import hmac
import hashlib
import requests
import traceback
import calendar
from mongoengine import DoesNotExist
from ctirs.core.mongo.documents import isightAdapter, Vias, ScheduleJobs
from ctirs.core.schedule.schedule import CtirsScheduler
from ctirs.core.adapter import _regist_stix
from ctirs.models.rs.models import System

class iSightAdapterControl(object):
    #固定値
    ACCEPT_VERSION = '2.5'
    API_URL = 'api.isightpartners.com'
    ACCEPT_JSON = 'application/json'
    ACCEPT_XML = 'application/stix'

    #シングルトン
    __instance = None
    #Scheduler
    _regist_schedule_flag = False
    
    def __new__(cls,*args,**kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self):
        #二重登録チェック
        if iSightAdapterControl._regist_schedule_flag == True:
            return
        iSightAdapterControl._regist_schedule_flag = True
        self._schedule = CtirsScheduler()
        #schedulerを起動
        #起動時に1回のみ動作
        #各job設定ごとに
        isight = None
        try:
            isight = isightAdapter.objects.get()
            for job in isight.jobs:
                #add_jobするとstatusが変わるためその前に保持
                status = job.status
                self.add_job(job)
                if status == ScheduleJobs.STATUS_IN_OPERATION:
                    self.resume_job(job.id)
                else:
                    self.pause_job(job.id)
        except DoesNotExist:
            #isightが存在しない場合はjob追加を行わない
            pass
        #interval の設定があった場合は追加する
        if isight is not None:
            self._interval_job = isight.interval_schedule_job
        else:
            self._interval_job = None
        if self._interval_job is not None:
            if isight.interval_schedule_job.status == ScheduleJobs.STATUS_IN_OPERATION:
                self.add_job(isight.interval_schedule_job)

    #時間文字列はYYYY/MM/DD HH:MM:SSとする
    def get_isight_stix(self,start_time=None,end_time=None):
        #登録情報を取得
        isight_adapter = isightAdapter.get()
        community = isight_adapter.community
        uploader = isight_adapter.uploader
        via = Vias.get_via_adapter_isight(uploader)
        try:
            #範囲内のリストを取得する
            l = self._get_isight_stix_report_list(start_time,end_time)
        except Exception as e:
            traceback.print_exc()
            raise e

        #last_requested更新
        isight_adapter.modify_last_requested()
        
        #リストの各要素をSTIXで取得してregistする
        count = 0
        for report_id in l:
            try:
                content = self._get_isight_stix_report(report_id)
                #ファイル登録
                #self._regist_isight_stix(content,community,via)
                _regist_stix(content,community,via)
                count += 1
            except Exception as e:
                #エラーが発生した場合はログを表示して処理は実行する
                traceback.print_exc()
        return count 
    
    #job起動用iSIGHT STIX取得
    def _get_isight_stix_job(self):
        isight_adapter = isightAdapter.objects.get()
        start_time_dt = isight_adapter.last_requested
        start_time =  calendar.timegm(start_time_dt.timetuple())
        self.get_isight_stix(start_time=start_time)
    
    #add job
    def add_job(self,schedule_job):
        #スケジューラに job 追加
        self._schedule.add_job(schedule_job,self._get_isight_stix_job)
        #job start
        self._schedule.start_job(schedule_job)
        #mongo の設定に格納する
        isight = isightAdapter.get()
        if schedule_job.job_type == ScheduleJobs.JOB_INTERVAL:
            #Interval指定の場合は_interval_jobを更新する
            isight.interval_schedule_job = schedule_job
            self._interval_job = schedule_job
        else:
            isight.jobs.append(schedule_job)

    #resume job
    def resume_job(self,job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        if schedule_job in isightAdapter.get().jobs:
            if schedule_job.status == ScheduleJobs.STATUS_STOP:
                pass
            else:
                print 'already working.'
                return
        else:
            raise Exception('invalid job_id')
        self._schedule.resume_job(schedule_job)
    
    #remove_job job(interval)
    def remove_interval_job(self):
        if self._interval_job is None:
            #まだ設定されていない
            return
        schedule_job = ScheduleJobs.objects.get(id=self._interval_job.id)
        #スケジューラからjob削除
        self._schedule.remove_job(schedule_job)
        self._interval_job = None

    #stop job
    def pause_job(self,job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        if schedule_job in isightAdapter.get().jobs:
            if schedule_job.status == ScheduleJobs.STATUS_IN_OPERATION:
                pass
            else:
                print 'not yet start.'
                return
        else:
            raise Exception('invalid job_id')
            return
        self._schedule.pause_job(schedule_job)
            
    #remove_job job
    def remove_job(self,job_id):
        #isightAdapterのjobsからjob削除
        isight_adapter = isightAdapter.get()
        isight_adapter.remove_job(job_id)
        #スケジューラからjob削除
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        self._schedule.remove_job(schedule_job)
        #mongoのschedule_jobsからschedule_job削除
        schedule_job.remove()
    
    #指定のreport_idのSTIXイメージを取得する
    def _get_isight_stix_report(self,report_id):
        query = '/report/%s' % (report_id)
        headers = self._get_headers(query,accept=self.ACCEPT_XML)
        resp = self._load_data(query,headers)
        if resp.status_code != 200:
            return None
        else:
            return resp.text
    
    #指定の時間範囲内のレポートリストを取得する
    def _get_isight_stix_report_list(self,start_time=None,end_time=None):
        query = '/report/index?'
        #時間範囲の引数を作成
        query_args = []
        if (start_time is not None):
            query_args.append('startDate=%d' % (start_time))
        if (end_time is not None):
            query_args.append('endDate=%d' % (end_time))
        for arg in query_args:
            query += (arg + '&')
        #最後の&(引数がない場合の?)を削除
        query = query[:-1]
            
        headers = self._get_headers(query,accept=self.ACCEPT_JSON)
        resp = self._load_data(query,headers)
        print resp.json()
        if resp.status_code != 200:
            return []
        else:
            j = resp.json()
            ret = []
            if j[u'success'] != True:
                return []
            for message in j[u'message']:
                ret.append(message[u'reportId'])
            return ret
    
    #API通信
    def _load_data(self,query,headers):
        url = 'https://%s%s' % (self.API_URL,query)
        proxies = System.get_request_proxies()
        resp = requests.get(url,headers=headers,proxies=proxies)
        return resp
    
    #APIで利用するHTTP Header作成
    def _get_headers(self,query,accept='application/json'):
        #各種キーをmongoに格納されている設定から取得
        isight_adapter = isightAdapter.objects.get()
        private_key = str(isight_adapter.private_key)
        public_key = str(isight_adapter.public_key)
    
        time_stamp = email.Utils.formatdate(localtime=True)
        new_data = query + self.ACCEPT_VERSION + accept + time_stamp
        hashed = hmac.new(private_key, new_data, hashlib.sha256)
        headers = {
            'Accept': accept,
            'Accept-Version': self.ACCEPT_VERSION,
            'X-Auth': public_key,
            'X-Auth-Hash': hashed.hexdigest(),
            'Date': time_stamp
        }
        return headers
    