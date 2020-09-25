from django.apps import AppConfig
from django.core.management import call_command
from mongoengine import connect
from stip.common.boot import is_skip_sequence


class StipRsBoot(AppConfig):
    name = 'ctirs.core.boot_rs'

    def ready(self):
        from ctirs.models import System, MongoConfig, STIPUser

        is_skip_sequnece = is_skip_sequence()
        if not is_skip_sequnece:
            print('>>> Start Auto Deploy')
            print('>>> Start collcect static --noinput')
            call_command('collectstatic', '--noinput')

            call_command('makemigrations')
            call_command('migrate')

            stip_user_count = STIPUser.objects.count()
            print('>>> users record count: ' + str(stip_user_count))
            if stip_user_count == 0:
                print('>>> Start loaddata users')
                call_command('loaddata', 'users')
                print('>>> users record count: ' + str(STIPUser.objects.count()))
            else:
                print('>>> Skip loaddata users')

            mongo_config_count = MongoConfig.objects.count()
            print('>>> mongo record count: ' + str(mongo_config_count))
            if mongo_config_count == 0:
                print('>>> Start loaddata mongo')
                call_command('loaddata', 'mongo')
                print('>>> mongo record count: ' + str(MongoConfig.objects.count()))
            else:
                print('>>> Skip loaddata mongo')

            system_count = System.objects.count()
            print('>>> rs_system record count: ' + str(System.objects.count()))
            if system_count == 0:
                print('>>> Start loaddata rs_system')
                call_command('loaddata', 'rs_system')
                print('>>> rs_system record count: ' + str(System.objects.count()))
            else:
                print('>>> Skip loaddata rs_system')

        init_mongo()
        self.init_taxii_client_scheduler()
        self.set_user_country()

    def set_user_country(self):
        import os
        from ctirs.models.rs.models import STIPUser, get_os_info
        for user in STIPUser.objects.all():
            if not user.country_code:
                if os.name == 'posix':
                    _, os_country_code, _ = get_os_info()
                    user.country_code = os_country_code
                else:
                    user.country_code = 'US'
                user.save()

    def boot_scheduler(self, job, taxii_client):
        from ctirs.core.mongo.documents import ScheduleJobs
        status = job.status
        taxii_client.add_job(job)
        if status == ScheduleJobs.STATUS_IN_OPERATION:
            taxii_client.resume_job(job.id)
        else:
            taxii_client.pause_job(job.id)

    def init_taxii_client_scheduler(self):
        from ctirs.core.mongo.documents import TaxiiClients, Taxii2Clients
        from ctirs.core.taxii.taxii import Client
        for doc in TaxiiClients.objects:
            taxii_client = Client(taxii_client=doc)
            for job in doc.jobs:
                self.boot_scheduler(job, taxii_client)
            if doc.interval_schedule_job is not None:
                job = doc.interval_schedule_job
                self.boot_scheduler(job, taxii_client)
        for doc in Taxii2Clients.objects:
            taxii2_client = Client(taxii2_client=doc)
            for job in doc.jobs:
                self.boot_scheduler(job, taxii2_client)
            if doc.interval_schedule_job is not None:
                job = doc.interval_schedule_job
                self.boot_scheduler(job, taxii2_client)


def init_mongo():
    MONGO_DEFAULT_DB_NAME = 'ctirs'
    MONGO_DEFAULT_TXS21_DB_NAME = 'taxii21'
    MONGO_DEFAULT_HOST_NAME = 'localhost'
    MONGO_DEFAULT_PORT = 27017

    from ctirs.models.rs.models import MongoConfig
    config = MongoConfig.objects.get()
    try:
        connect(config.db, host=config.host, port=int(config.port))
        connect(MONGO_DEFAULT_TXS21_DB_NAME, host=config.host, port=int(config.port), alias='taxii21_alias')
    except BaseException:
        connect(MONGO_DEFAULT_DB_NAME, host=MONGO_DEFAULT_HOST_NAME, port=MONGO_DEFAULT_PORT)
        connect(MONGO_DEFAULT_TXS21_DB_NAME, host=MONGO_DEFAULT_HOST_NAME, port=MONGO_DEFAULT_PORT, alias='taxii21_alias')

    from ctirs.core.mongo.documents import TaxiiClients, Taxii2Clients
    for taxii_client in TaxiiClients.objects:
        if taxii_client.protocol_version.startswith('2.'):
            Taxii2Clients.create(
                taxii_client.name,
                taxii_client.path,
                taxii_client.collection,
                taxii_client.login_id,
                taxii_client.login_password,
                taxii_client.community.id,
                taxii_client.protocol_version,
                taxii_client.push,
                taxii_client.uploader
            )
            taxii_client.delete()
