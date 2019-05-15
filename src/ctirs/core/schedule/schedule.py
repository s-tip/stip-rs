# -*- coding: utf-8 -*-
from ctirs.core.mongo.documents import ScheduleJobs
from apscheduler.schedulers.background import BackgroundScheduler

class CtirsScheduler(object):
    #シングルトン
    __instance = None
    
    #Scheduler
    _schedule = BackgroundScheduler(timezone='UTC')
    _schedule.start()

    def __new__(cls,*args,**kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self):
        pass
        
    #add job
    def add_job(self,schedule_job,func):
        if schedule_job.job_type == ScheduleJobs.JOB_CRON:
            self._schedule.add_job(
                func,
                'cron',
                year=schedule_job.cron_job.year,
                month=schedule_job.cron_job.month,
                day=schedule_job.cron_job.day,
                week=schedule_job.cron_job.week,
                hour=schedule_job.cron_job.hour,
                minute=schedule_job.cron_job.minute,
                second=schedule_job.cron_job.second,
                id =str(schedule_job.id))
        elif schedule_job.job_type == ScheduleJobs.JOB_INTERVAL:
            self._schedule.add_job(
                func,
                'interval',
                seconds=schedule_job.interval_job.seconds,
                id =str(schedule_job.id))
        else:
            return

    #start job
    def start_job(self,schedule_job):
        #job開始
        schedule_job.status = ScheduleJobs.STATUS_IN_OPERATION
        schedule_job.save()

    #resume job
    def resume_job(self,schedule_job):
        #job再開
        self._schedule.resume_job(str(schedule_job.id))
        schedule_job.status = ScheduleJobs.STATUS_IN_OPERATION
        schedule_job.save()

    #pause job
    def pause_job(self,schedule_job):
        #job停止
        self._schedule.pause_job(str(schedule_job.id))
        schedule_job.status = ScheduleJobs.STATUS_STOP
        schedule_job.save()

    #remove job
    def remove_job(self,schedule_job):
        #スケジューラからjob削除
        self._schedule.remove_job(str(schedule_job.id))
        
