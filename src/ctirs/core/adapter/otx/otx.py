import traceback
from mongoengine import DoesNotExist
from ctirs.core.adapter.otx.vendor.StixExport import StixExport
from ctirs.core.adapter.otx.vendor.OTXv2 import OTXv2
from ctirs.core.mongo.documents import OtxAdapter,Vias,ScheduleJobs
from ctirs.core.schedule.schedule import CtirsScheduler
from ctirs.core.adapter import _regist_stix
from ctirs.models.rs.models import System

class OtxAdapterControl(object):
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
        if OtxAdapterControl._regist_schedule_flag == True:
            return
        OtxAdapterControl._regist_schedule_flag = True
        self._schedule = CtirsScheduler()
        #schedulerを起動
        #起動時に1回のみ動作
        #各job設定ごとに
        otx = None
        try:
            otx = OtxAdapter.objects.get()
            for job in otx.jobs:
                #add_jobするとstatusが変わるためその前に保持
                status = job.status
                self.add_job(job)
                if status == ScheduleJobs.STATUS_IN_OPERATION:
                    self.resume_job(job.id)
                else:
                    self.pause_job(job.id)
        except DoesNotExist:
            #OtxAdapterが存在しない場合はjob追加を行わない
            pass
        #interval の設定があった場合は追加する
        if otx is not None:
            self._interval_job = otx.interval_schedule_job
        else:
            self._interval_job = None
        if self._interval_job is not None:
            if otx.interval_schedule_job.status == ScheduleJobs.STATUS_IN_OPERATION:
                self.add_job(otx.interval_schedule_job)

    #otxからmtimestamp以降のデータを取得する
    def get_otx_stix(self,mtimestamp=None):
        #OTXアダプタの設定を取得
        otx_conf = OtxAdapter.get()
        key = otx_conf.apikey
        #登録情報を取得
        community = otx_conf.community
        uploader = otx_conf.uploader
        via = Vias.get_via_adapter_otx(uploader)
            
        #otxから取得
        try:
            proxies = System.get_request_proxies()
            otx = OTXv2(key,proxies)
            slices = otx.getsince(mtimestamp)
        except Exception as e:
            traceback.print_exc()
            raise e

        #last_requested更新
        otx_conf.modify_last_requested()

        count = 0
        #ひとつずつ取得する
        for slice_ in slices:
            try:
                #stix一つごとに登録処理
                stix = StixExport(slice_)
                stix.build()
                content = stix.to_xml()
                #取得したSTIXを登録
                _regist_stix(content,community,via)
                count += 1
            except Exception as e:
                #エラーが発生した場合はログを表示して処理は実行する
                traceback.print_exc()
        #件数を返却
        return count
        
    #job起動用otxからmtimestamp以降のデータを取得する
    def _get_otx_stix_job(self):
        otx = OtxAdapter.objects.get()
        start_time_dt = otx.last_requested
        self.get_otx_stix(mtimestamp=start_time_dt.isoformat())
    
    #add job
    def add_job(self,schedule_job):
        #スケジューラに job 追加
        self._schedule.add_job(schedule_job,self._get_otx_stix_job)
        #job start
        self._schedule.start_job(schedule_job)
        #mongo の設定に格納する
        otx = OtxAdapter.objects.get()
        if schedule_job.job_type == ScheduleJobs.JOB_INTERVAL:
            #Interval指定の場合は_interval_jobを更新する
            otx.interval_schedule_job = schedule_job
            self._interval_job = schedule_job
        else:
            otx.jobs.append(schedule_job)
    
    #resume job
    def resume_job(self,job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        if schedule_job in OtxAdapter.get().jobs:
            if schedule_job.status == ScheduleJobs.STATUS_STOP:
                pass
            else:
                print('already working.')
                return
        else:
            raise Exception('invalid job_id')
        self._schedule.resume_job(schedule_job)
    
    #stop job
    def pause_job(self,job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        if schedule_job in OtxAdapter.get().jobs:
            if schedule_job.status == ScheduleJobs.STATUS_IN_OPERATION:
                pass
            else:
                print('not yet start.')
                return
        else:
            raise Exception('invalid job_id')
        
            return
        self._schedule.pause_job(schedule_job)
            
    #remove_job job
    def remove_job(self,job_id):
        #OtxAdapterのjobsからjob削除
        otx = OtxAdapter.get()
        otx.remove_job(job_id)
        #スケジューラからjob削除
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        self._schedule.remove_job(schedule_job)
        #mongoのschedule_jobsからschedule_job削除
        schedule_job.remove()
    
    #remove_job job(interval)
    def remove_interval_job(self):
        if self._interval_job is None:
            #まだ設定されていない
            return
        schedule_job = ScheduleJobs.objects.get(id=self._interval_job.id)
        #スケジューラからjob削除
        self._schedule.remove_job(schedule_job)
        self._interval_job = None
    
    '''
    #stixファイルの登録
    def _regist_otx_stix(self,content,community,via):
        #stixファイルを一時ファイルに出力
        stix_file_path = tempfile.mktemp(suffix='.xml')
        with open(stix_file_path,'wb+') as fp:
            #cb.contentがstixの中身(contentの型はstr)
            fp.write(content)
        #登録
        regist(stix_file_path,community,via)
        return
    '''
