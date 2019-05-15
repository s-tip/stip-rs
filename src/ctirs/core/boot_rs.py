# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.core.management import call_command
from mongoengine import connect
from stip.common.boot import is_skip_sequence

class StipRsBoot(AppConfig):
    name = 'ctirs.core.boot_rs'

    def ready(self):
        from ctirs.models import System, MongoConfig,STIPUser

        is_skip_sequnece = is_skip_sequence()
        if is_skip_sequnece == False:
            print '>>> Start Auto Deploy'
            print '>>> Start collcect static --noinput'
            #collectstatic
            call_command('collectstatic','--noinput')
            
            #migrate を行うタイミング
            #DB が存在しない時のエラー
            try:
                print '>>> STIPUser record count: ' + str(STIPUser.objects.count())
                #STIPUser が取得可能なので 初期 migrate 不要
                print '>>> Skip migrate'
            except:
                #エラーの場合は migrate
                call_command('migrate')

            #create_user_user は loaddata でデータ注入できると思われる
            #loaddata (users)
            stip_user_count = STIPUser.objects.count()
            print '>>> users record count: ' + str(stip_user_count)
            if stip_user_count == 0:
                print '>>> Start loaddata users'
                call_command('loaddata','users')
                print '>>> users record count: ' + str(STIPUser.objects.count())
            else:
                print '>>> Skip loaddata users'

            #loaddata (mongo)
            mongo_config_count = MongoConfig.objects.count()
            print '>>> mongo record count: ' + str(mongo_config_count)
            if mongo_config_count == 0:
                print '>>> Start loaddata mongo'
                call_command('loaddata','mongo')
                print '>>> mongo record count: ' + str(MongoConfig.objects.count())
            else:
                print '>>> Skip loaddata mongo'

            #loaddata (rs_system)
            system_count = System.objects.count()
            print '>>> rs_system record count: ' + str(System.objects.count())
            if system_count == 0:
                print '>>> Start loaddata rs_system'
                call_command('loaddata','rs_system')
                print '>>> rs_system record count: ' + str(System.objects.count())
            else:
                print '>>> Skip loaddata rs_system'

        #mongo を初期化する
        self.init_mongo()
        #taxii client のスケジューラー起動
        self.init_taxii_client_scheduler()
        
    #mongo 初期化
    def init_mongo(self):
        MONGO_DEFAULT_DB_NAME = 'ctirs'
        MONGO_DEFAULT_HOST_NAME = 'localhost'
        MONGO_DEFAULT_PORT = 27017

        try:
            from ctirs.models.rs.models import MongoConfig
            config = MongoConfig.objects.get()
            connect(config.db,host=config.host,port=int(config.port))
        except:
            #デフォルト設定を用いる
            connect(MONGO_DEFAULT_DB_NAME,host=MONGO_DEFAULT_HOST_NAME,port=MONGO_DEFAULT_PORT)
             
    #scheduler 起動
    def boot_scheduler(self,job,taxii_client):
        from ctirs.core.mongo.documents import ScheduleJobs
        status = job.status
        taxii_client.add_job(job)
        #稼働中のステータスの場合のみschedulerに登録
        if status == ScheduleJobs.STATUS_IN_OPERATION:
            taxii_client.resume_job(job.id)
        else:
            taxii_client.pause_job(job.id)

    #taxii client スケジューラ起動
    def init_taxii_client_scheduler(self):
        from ctirs.core.mongo.documents import TaxiiClients
        from ctirs.core.taxii.taxii import Client
        #schedulerを起動
        #mongoに格納されている全TaxiiClientsドキュメントについて
        for doc in TaxiiClients.objects:
            taxii_client = Client(taxii_id=doc.id)
            #各job設定ごとに
            for job in doc.jobs:
                self.boot_scheduler(job, taxii_client)
            #interval
            if doc.interval_schedule_job is not None:
                job = doc.interval_schedule_job
                self.boot_scheduler(job, taxii_client)

