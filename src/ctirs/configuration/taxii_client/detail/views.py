from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.core.common import get_common_replace_dict
from ctirs.core.mongo.documents import TaxiiClients, ScheduleJobs
from ctirs.core.taxii.taxii import Client
from ctirs.error.views import error_page, error_page_no_view_permission, error_page_free_format, error_page_inactive


def get_configuartion_taxii_client_detail_create_time(request):
    return get_text_field_value(request, 'schedule_time', default_value=None)


def get_configuartion_taxii_client_detail_interval_interval(request):
    interval_str = get_text_field_value(request, 'interval', default_value='')
    if interval_str == '':
        return 0
    else:
        return int(interval_str)


@login_required
def top(request, taxii_id):
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        replace_dict = get_common_replace_dict(request)
        replace_dict['client'] = TaxiiClients.objects.get(id=taxii_id)
        return render(request, 'configuration_taxii_client_detail.html', replace_dict)
    except Exception:
        return error_page(request)


@login_required
def interval(request, taxii_id):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        interval = get_configuartion_taxii_client_detail_interval_interval(request)
        taxii_client = TaxiiClients.objects.get(id=taxii_id)
        client = Client(taxii_client=taxii_client)
        client.remove_interval_job()
        taxii_client.interval_schedule_job = None
        taxii_client.save()
        if interval != 0:
            schedule_job = taxii_client.add_job(type_=ScheduleJobs.JOB_INTERVAL, seconds=interval)
            client.add_job(schedule_job)
        replace_dict = get_common_replace_dict(request)
        replace_dict['client'] = taxii_client
        if interval != 0:
            replace_dict['interval_info_msg'] = 'Set Interval %d sec' % (interval)
        else:
            replace_dict['interval_info_msg'] = 'Stop a job by interval'
        return render(request, 'configuration_taxii_client_detail.html', replace_dict)
    except Exception:
        return error_page(request)


@login_required
def create(request, taxii_id):
    if request.method != 'POST':
        return error_page_free_format(request, 'invalid method')
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        time = get_configuartion_taxii_client_detail_create_time(request)
        taxii_client = TaxiiClients.objects.get(id=taxii_id)
        times = time.split(':')
        schedule_job = taxii_client.add_job(type_=ScheduleJobs.JOB_CRON, hour=times[0], minute=times[1], second=times[2])
        client = Client(taxii_client=taxii_client)
        client.add_job(schedule_job)

        replace_dict = get_common_replace_dict(request)
        replace_dict['client'] = taxii_client
        return render(request, 'configuration_taxii_client_detail.html', replace_dict)
    except Exception:
        return error_page(request)


@login_required
def pause(request, taxii_id, job_id):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        taxii_client = TaxiiClients.objects.get(id=taxii_id)
        client = Client(taxii_client=taxii_client)
        client.pause_job(job_id)
        replace_dict = get_common_replace_dict(request)
        replace_dict['client'] = taxii_client
        return render(request, 'configuration_taxii_client_detail.html', replace_dict)
    except Exception:
        return error_page(request)


@login_required
def resume(request, taxii_id, job_id):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        taxii_client = TaxiiClients.objects.get(id=taxii_id)
        client = Client(taxii_client=taxii_client)
        client.resume_job(job_id)
        replace_dict = get_common_replace_dict(request)
        replace_dict['client'] = taxii_client
        return render(request, 'configuration_taxii_client_detail.html', replace_dict)
    except Exception:
        return error_page(request)


@login_required
def remove(request, taxii_id, job_id):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        taxii_client = TaxiiClients.objects.get(id=taxii_id)
        taxii_client.remove_job(job_id)
        client = Client(taxii_client=taxii_client)
        client.remove_job(job_id)
        replace_dict = get_common_replace_dict(request)
        replace_dict['client'] = taxii_client
        return render(request, 'configuration_taxii_client_detail.html', replace_dict)
    except Exception:
        return error_page(request)
