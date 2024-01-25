from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.models.rs.models import STIPUser


def get_configuration_user_ajax_change_auth_username(request):
    return get_text_field_value(request, 'username', default_value='')


def get_configuration_user_ajax_change_auth_value(request):
    return get_text_field_value(request, 'value', default_value='')


def get_configuration_user_ajax_change_active_value(request):
    return get_text_field_value(request, 'value', default_value='')


def check_ajax_request(request):
    if request.method != 'GET':
        return {
            'status': 'NG',
            'message': 'Invalid HTTP method'}
    if not request.user.is_active:
        return {
            'status': 'NG',
            'message': 'You account is inactive.'}
    if not request.user.is_admin:
        return {
            'status': 'NG',
            'message': 'No permission.'}
    return None


def get_common_error_dict():
    return {
        'status': 'NG',
        'message': 'A system error has occurred. Please check the system log.'}


@login_required
@csrf_protect
def change_auth(request):
    r = check_ajax_request(request)
    if r:
        return JsonResponse(r, safe=False)
    try:
        username = get_configuration_user_ajax_change_auth_username(request)
        value = True if get_configuration_user_ajax_change_auth_value(request) == 'true' else False
        u = STIPUser.objects.get(username=username)
        u.is_admin = value
        u.is_superuser = value
        u.save()
        r = {'status': 'OK',
             'message': 'Success'}
    except Exception:
        r = get_common_error_dict()
    finally:
        return JsonResponse(r, safe=False)


@login_required
@csrf_protect
def change_active(request):
    r = check_ajax_request(request)
    if r:
        return JsonResponse(r, safe=False)
    try:
        username = get_configuration_user_ajax_change_auth_username(request)
        value = True if get_configuration_user_ajax_change_active_value(request) == 'true' else False
        u = STIPUser.objects.get(username=username)
        u.is_active = value
        u.save()
        r = {'status': 'OK',
             'message': 'Success'}
    except Exception:
        r = get_common_error_dict()
    finally:
        return JsonResponse(r, safe=False)


@login_required
@csrf_protect
def unset_mfa(request):
    r = check_ajax_request(request)
    if r:
        return JsonResponse(r, safe=False)
    try:
        username = get_configuration_user_ajax_change_auth_username(request)
        u = STIPUser.objects.get(username=username)
        u.totp_secret = None
        u.save()
        r = {'status': 'OK',
             'message': 'Success'}
    except Exception:
        r = get_common_error_dict()
    finally:
        return JsonResponse(r, safe=False)
