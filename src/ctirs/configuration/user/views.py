from django.shortcuts import render
from ctirs.core.common import get_text_field_value, get_common_replace_dict
from ctirs.error.views import error_page, error_page_no_view_permission, error_page_free_format, error_page_inactive
from django.contrib.auth.decorators import login_required
from ctirs.models.rs.models import STIPUser


def get_configuration_user_create_user_username(request):
    return get_text_field_value(request, 'username', default_value='')


def get_configuration_user_create_user_password(request):
    return get_text_field_value(request, 'password', default_value='')


def get_configuration_user_create_user_screen_name(request):
    return get_text_field_value(request, 'screen_name', default_value='')


def get_configuration_user_delete_user_username(request):
    return get_text_field_value(request, 'username', default_value='')


def get_configuration_user_create_user_is_admin(request):
    return get_configuration_user_check_value(request, 'is_admin')


def get_configuration_user_check_value(request, key):
    if (key in request.POST):
        if(request.POST[key] == 'on'):
            return True
    return False

def get_configuration_user_change_password_top_username(request):
    return get_text_field_value(request, 'username', default_value='')

def get_configuration_user_change_password_username(request):
    return get_text_field_value(request, 'username', default_value='')

def get_configuration_user_change_password_password(request):
    return get_text_field_value(request, 'password', default_value='')

@login_required
def top(request):
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        replace_dict = get_common_replace_dict(request)
        replace_dict['users'] = STIPUser.objects.all()
        # レンダリング
        return render(request, 'user.html', replace_dict)
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
        username = get_configuration_user_create_user_username(request)
        if(username is None or len(username) == 0):
            return error_page_free_format(request, 'No Username.')
        password = get_configuration_user_create_user_password(request)
        if(password is None or len(password) == 0):
            return error_page_free_format(request, 'No Password.')
        screen_name = get_configuration_user_create_user_screen_name(request)
        # screen_nameが存在しない場合はusernameを利用する
        if(screen_name is None or len(screen_name) == 0):
            screen_name = username
        is_admin = get_configuration_user_create_user_is_admin(request)
        # user作成
        stip_user = STIPUser.objects.create_user(username, screen_name, password, is_admin=is_admin)
        # api_key設定
        stip_user.change_api_key()
        replace_dict = get_common_replace_dict(request)
        replace_dict['users'] = STIPUser.objects.all()
        replace_dict['info_msg'] = 'Create Success!!'
        # レンダリング
        return render(request, 'user.html', replace_dict)
    except Exception:
        # エラーページ
        return error_page(request)

@login_required
def change_password_top(request):
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        username = get_configuration_user_change_password_top_username(request)
        replace_dict = get_common_replace_dict(request)
        replace_dict['change_pwd_username'] = username
        # レンダリング
        return render(request, 'change_pwd.html', replace_dict)
    except Exception:
        # エラーページ
        return error_page(request)

@login_required
def change_password(request):
    # activeユーザー以外はエラー
    if not request.user.is_active:
        return error_page_inactive(request)
    # is_admin権限なしの場合はエラー
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        username = get_configuration_user_change_password_username(request)
        password = get_configuration_user_change_password_password(request)
        stip_user = STIPUser.objects.get(username=username)
        stip_user.is_modified_password = False
        stip_user.set_password(password)
        stip_user.save()
        replace_dict = get_common_replace_dict(request)
        replace_dict['info_msg'] = 'Change Password Successfully!!'
        # レンダリング
        return render(request, 'change_pwd.html', replace_dict)
    except Exception:
        # エラーページ
        return error_page(request)

