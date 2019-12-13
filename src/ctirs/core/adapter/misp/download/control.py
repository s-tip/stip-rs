import traceback
from mongoengine import DoesNotExist
from ctirs.core.mongo.documents import MispAdapter, Vias, ScheduleJobs
from ctirs.core.mongo.documents_stix import StixFiles
from ctirs.core.schedule.schedule import CtirsScheduler
from ctirs.core.adapter.misp.download.downloader import MISPDownloader
from ctirs.core.adapter.misp.download.converter import MISP2STIXConverter
from ctirs.core.adapter import _regist_stix


class MispAdapterDownloadControl(object):
    ns_url = 'http://s-tip.fujtisu.com'
    ns_name = 's-tip'
    default_identity_name = 's-tip'

    # MISP2STIX Converter
    mc = MISP2STIXConverter(
        identity_name=default_identity_name,
        ns_url=ns_url,
        ns_name=ns_name
    )

    # シングルトン
    __instance = None
    # Scheduler
    _regist_schedule_flag = False

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self):
        # 二重登録チェック
        if MispAdapterDownloadControl._regist_schedule_flag:
            return
        MispAdapterDownloadControl._regist_schedule_flag = True
        self._schedule = CtirsScheduler()
        # schedulerを起動
        # 起動時に1回のみ動作
        # 各job設定ごとに
        misp = None
        try:
            misp = MispAdapter.objects.get()
            for job in misp.jobs:
                # add_jobするとstatusが変わるためその前に保持
                status = job.status
                self.add_job(job)
                if status == ScheduleJobs.STATUS_IN_OPERATION:
                    self.resume_job(job.id)
                else:
                    self.pause_job(job.id)
        except DoesNotExist:
            # OtxAdapterが存在しない場合はjob追加を行わない
            pass
        # interval の設定があった場合は追加する
        if misp is not None:
            self._interval_job = misp.interval_schedule_job
        else:
            self._interval_job = None
        if self._interval_job is not None:
            if misp.interval_schedule_job.status == ScheduleJobs.STATUS_IN_OPERATION:
                self.add_job(misp.interval_schedule_job)

    # misp から from_dt から to_dt までのデータを取得する
    def get_misp_stix(self, from_dt=None, to_dt=None, identity=default_identity_name):
        # identity を更新
        self.mc.identity_name = identity
        # misp アダプタの設定を取得
        misp_conf = MispAdapter.get()
        url = misp_conf.url
        stix_id_prefix = misp_conf.stix_id_prefix
        apikey = misp_conf.apikey
        published_only = misp_conf.published_only
        # 登録情報を取得
        community = misp_conf.community
        uploader = misp_conf.uploader
        via = Vias.get_via_adapter_misp(uploader)

        # mispから取得
        try:
            if url[-1] != '/':
                url += '/'
            url = url + 'events/xml/download.json'
            md = MISPDownloader(url, apikey)
            text = md.get(from_dt=from_dt, to_dt=to_dt)
            if text is None:
                return 0
            stix_packages = self.mc.convert(text=text.encode(), published_only=published_only, stix_id_prefix=stix_id_prefix)
        except Exception as e:
            traceback.print_exc()
            raise e

        # last_requested更新
        misp_conf.modify_last_requested()

        count = 0
        # ひとつずつ取得する
        for stix_package in stix_packages:
            try:
                # stix一つごとに登録処理
                # 取得したSTIXを登録
                try:
                    StixFiles.objects.get(package_id=stix_package.id_)
                except DoesNotExist:
                    # 存在しない場合は登録する
                    _regist_stix(stix_package.to_xml(), community, via)
                    count += 1
            except Exception as e:
                # エラーが発生した場合はログを表示して処理は実行する
                traceback.print_exc()

        # 件数を返却
        return count

    # job起動用 misp から last_requested 以降のデータを取得する
    def _get_misp_stix_job(self):
        misp = MispAdapter.objects.get()
        start_time_dt = misp.last_requested
        print(start_time_dt)
        self.get_misp_stix(from_dt=start_time_dt)

    # add job
    def add_job(self, schedule_job):
        # スケジューラに job 追加
        self._schedule.add_job(schedule_job, self._get_misp_stix_job)
        # job start
        self._schedule.start_job(schedule_job)
        # mongo の設定に格納する
        misp = MispAdapter.objects.get()
        if schedule_job.job_type == ScheduleJobs.JOB_INTERVAL:
            # Interval指定の場合は_interval_jobを更新する
            misp.interval_schedule_job = schedule_job
            self._interval_job = schedule_job
        else:
            misp.jobs.append(schedule_job)

    # resume job
    def resume_job(self, job_id):
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        if schedule_job in MispAdapter.get().jobs:
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
        if schedule_job in MispAdapter.get().jobs:
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
        # MispAdapter の jobs から job 削除
        misp = MispAdapter.get()
        misp.remove_job(job_id)
        # スケジューラから job 削除
        schedule_job = ScheduleJobs.objects.get(id=job_id)
        self._schedule.remove_job(schedule_job)
        # mongo の schedule_jobs から schedule_job 削除
        schedule_job.remove()

    def remove_interval_job(self):
        if self._interval_job is None:
            # まだ設定されていない
            return
        schedule_job = ScheduleJobs.objects.get(id=self._interval_job.id)
        # スケジューラからjob削除
        self._schedule.remove_job(schedule_job)
        self._interval_job = None
