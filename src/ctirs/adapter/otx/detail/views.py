from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.core.common import get_common_replace_dict
from ctirs.core.mongo.documents import ScheduleJobs, OtxAdapter
from ctirs.error.views import error_page, error_page_no_view_permission, error_page_free_format, error_page_inactive
from ctirs.core.adapter.otx.otx import OtxAdapterControl

otx = OtxAdapterControl()


def get_adapter_otx_detail_create_time(request):
    return get_text_field_value(request, 'schedule_time', default_value=None)


def get_adapter_otx_detail_interval_interval(request):
    interval_str = get_text_field_value(request, 'interval', default_value='')
    if interval_str == '':
        return 0
    else:
        return int(interval_str)


def otx_common_render(request, info_msg=None, error_msg=None):
    try:
        replace_dict = get_common_replace_dict(request)
        # mongoからotx情報を取得
        oa = OtxAdapter.get()
        replace_dict['otx'] = oa
        if info_msg is not None:
            replace_dict['interval_info_msg'] = info_msg
        if error_msg is not None:
            replace_dict['interval_error_msg'] = error_msg
        # レンダリング
        return render(request, 'otx_detail.html', replace_dict)
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
    return otx_common_render(request)


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
        interval = get_adapter_otx_detail_interval_interval(request)
        print(interval)
        # schedular からジョブを削除
        otx.remove_interval_job()
        # mongo 格納の設定からジョブを削除
        OtxAdapter.remove_internal_job()
        if interval != 0:
            # Mongo の isightAdapter に jobを追加する (設定の保存のみ)
            job = OtxAdapter.add_job(type_=ScheduleJobs.JOB_INTERVAL, seconds=interval)
            # job 動作追加
            otx.add_job(job)
            info_msg = 'Set Interval %d sec' % (interval)
        else:
            # ジョブの追加をしない
            info_msg = 'Stop a job by interval'
        return otx_common_render(request, info_msg=info_msg)
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
        time = get_adapter_otx_detail_create_time(request)
        if time is None:
            return error_page_free_format(request, 'Invalid Time format.')
        times = time.split(':')
        # 数値変換チェック
        try:
            int(times[0])
            int(times[1])
            int(times[2])
        except ValueError:
            return error_page_free_format(request, 'Invalid Time format.')
        # Cron設定
        # job追加
        job = OtxAdapter.add_job(type_=ScheduleJobs.JOB_CRON, hour=times[0], minute=times[1], second=times[2])
        otx.add_job(job)
    except Exception:
        # エラーページ
        return error_page(request)
    return otx_common_render(request)


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
        otx.pause_job(job_id)
    except Exception:
        # エラーページ
        return error_page(request)
    return otx_common_render(request)


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
        otx.resume_job(job_id)
    except Exception:
        # エラーページ
        return error_page(request)
    return otx_common_render(request)


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
        otx.remove_job(job_id)
    except Exception:
        # エラーページ
        return error_page(request)
    return otx_common_render(request)
