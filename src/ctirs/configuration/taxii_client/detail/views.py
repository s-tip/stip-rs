from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ctirs.core.common import get_text_field_value, get_common_replace_dict
from ctirs.core.mongo.documents import TaxiiClients,ScheduleJobs
from ctirs.core.taxii.taxii import Client
from ctirs.error.views import error_page,error_page_no_view_permission, error_page_free_format, error_page_inactive

def get_configuartion_taxii_client_detail_create_time(request):
    return get_text_field_value(request,'schedule_time',default_value=None)

def get_configuartion_taxii_client_detail_interval_interval(request):
    interval_str = get_text_field_value(request,'interval',default_value='')
    if interval_str == '':
        return 0
    else:
        return int(interval_str)

@login_required
def top(request,taxii_id):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        replace_dict = get_common_replace_dict(request)
        #mongoからtaxii_client情報を取得
        replace_dict['client'] = TaxiiClients.objects.get(id=taxii_id)
        #レンダリング
        return render(request,'configuration_taxii_client_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def interval(request,taxii_id):
    if request.method != 'GET':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        interval = get_configuartion_taxii_client_detail_interval_interval(request)
        #mongoからtaxii_client情報を取得
        taxii_client = TaxiiClients.objects.get(id=taxii_id)
        client = Client(taxii_id=taxii_id)
        #稼働しているスケジューラの job があったら削除する
        client.remove_interval_job()
        #taxii_client の internal_schedule_jobs を Noneにする
        taxii_client.interval_schedule_job = None
        taxii_client.save()
        if interval != 0:
            #Cron設定
            schedule_job = taxii_client.add_job(type_=ScheduleJobs.JOB_INTERVAL,seconds=interval)
            #job追加
            client.add_job(schedule_job)
        replace_dict = get_common_replace_dict(request)
        replace_dict['client'] = taxii_client
        if interval != 0:
            replace_dict['interval_info_msg'] = 'Set Interval %d sec' % (interval)
        else:
            replace_dict['interval_info_msg'] = 'Stop a job by interval'
        #レンダリング
        return render(request,'configuration_taxii_client_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def create(request,taxii_id):
    if request.method != 'POST':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        time = get_configuartion_taxii_client_detail_create_time(request)
        #mongoからtaxii_client情報を取得
        taxii_client = TaxiiClients.objects.get(id=taxii_id)
        #Cron設定
        times = time.split(':')
        schedule_job = taxii_client.add_job(type_=ScheduleJobs.JOB_CRON,hour=times[0],minute=times[1],second=times[2])
        #job追加
        client = Client(taxii_id=taxii_id)
        client.add_job(schedule_job)

        replace_dict = get_common_replace_dict(request)
        replace_dict['client'] = taxii_client
        #レンダリング
        return render(request,'configuration_taxii_client_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def pause(request,taxii_id,job_id):
    if request.method != 'GET':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        #job停止
        client = Client(taxii_id=taxii_id)
        client.pause_job(job_id)
        replace_dict = get_common_replace_dict(request)
        #mongoからtaxii_client情報を取得
        replace_dict['client'] = TaxiiClients.objects.get(id=taxii_id)
        #レンダリング
        return render(request,'configuration_taxii_client_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def resume(request,taxii_id,job_id):
    if request.method != 'GET':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        #job開始
        client = Client(taxii_id=taxii_id)
        client.resume_job(job_id)
        replace_dict = get_common_replace_dict(request)
        #mongoからtaxii_client情報を取得
        replace_dict['client'] = TaxiiClients.objects.get(id=taxii_id)
        #レンダリング
        return render(request,'configuration_taxii_client_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def remove(request,taxii_id,job_id):
    if request.method != 'GET':
        return error_page_free_format(request,'invalid method')
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        #mongoのtaxii_client情報から該当job_idを削除
        taxii_client = TaxiiClients.objects.get(id=taxii_id)
        taxii_client.remove_job(job_id)
        #job停止
        client = Client(taxii_id=taxii_id)
        client.remove_job(job_id)
        replace_dict = get_common_replace_dict(request)
        #mongoからtaxii_client情報を取得
        replace_dict['client'] = TaxiiClients.objects.get(id=taxii_id)
        #レンダリング
        return render(request,'configuration_taxii_client_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)


