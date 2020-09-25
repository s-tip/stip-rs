from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.core.common import get_common_replace_dict
from ctirs.core.mongo.documents import ScheduleJobs, MispAdapter
from ctirs.error.views import error_page, error_page_no_view_permission, error_page_free_format, error_page_inactive
from ctirs.core.adapter.misp.download.control import MispAdapterDownloadControl

misp = MispAdapterDownloadControl()


def get_adapter_misp_detail_create_time(request):
    return get_text_field_value(request, 'schedule_time', default_value=None)


def get_adapter_misp_detail_interval_interval(request):
    interval_str = get_text_field_value(request, 'interval', default_value='')
    if interval_str == '':
        return 0
    else:
        return int(interval_str)


def misp_common_render(request, info_msg=None, error_msg=None):
    try:
        replace_dict = get_common_replace_dict(request)
        # mongo から misp 情報を取得
        ma = MispAdapter.get()
        replace_dict['misp'] = ma
        if info_msg is not None:
            replace_dict['interval_info_msg'] = info_msg
        if error_msg is not None:
            replace_dict['interval_error_msg'] = error_msg
        # レンダリング
        return render(request, 'misp_detail.html', replace_dict)
    except Exception:
        # エラーページ
        return error_page(request)


@login_required
def top(request):
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    return misp_common_render(request)


@login_required
def interval(request):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        interval = get_adapter_misp_detail_interval_interval(request)
        # schedular からジョブを削除
        misp.remove_interval_job()
        # mongo 格納の設定からジョブを削除
        MispAdapter.remove_internal_job()
        if interval != 0:
            # Mongo の misp に jobを追加する (設定の保存のみ)
            job = MispAdapter.add_job(type_=ScheduleJobs.JOB_INTERVAL, seconds=interval)
            # job 動作追加
            misp.add_job(job)
            info_msg = 'Set Interval %d sec' % (interval)
        else:
            # ジョブの追加をしない
            info_msg = 'Stop a job by interval'
        return misp_common_render(request, info_msg=info_msg)
    except Exception:
        # エラーページ
        return error_page(request)


@login_required
def create(request):
    if request.method != 'POST':
        return error_page_free_format(request, 'invalid method')
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        time = get_adapter_misp_detail_create_time(request)
        if time is None:
            return error_page_free_format(request, 'Invalid Time format.')
        times = time.split(':')
        if len(times) == 1:
            return error_page_free_format(request, 'Invalid Time format.')
        # 数値変換チェック
        try:
            int(times[0])
            int(times[1])
            int(times[2])
        except ValueError:
            return error_page_free_format(request, 'Invalid Time format.')

        # Cron設定
        # job追加
        job = MispAdapter.add_job(type_=ScheduleJobs.JOB_CRON, hour=times[0], minute=times[1], second=times[2])
        misp.add_job(job)
    except Exception:
        # エラーページ
        return error_page(request)
    return misp_common_render(request)


@login_required
def pause(request, job_id):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        # job停止
        misp.pause_job(job_id)
    except Exception:
        # エラーページ
        return error_page(request)
    return misp_common_render(request)


@login_required
def resume(request, job_id):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        # job開始
        misp.resume_job(job_id)
    except Exception:
        # エラーページ
        return error_page(request)
    return misp_common_render(request)


@login_required
def remove(request, job_id):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        # isight.remove_job(job_id)
        misp.remove_job(job_id)
    except Exception:
        # エラーページ
        return error_page(request)
    return misp_common_render(request)
