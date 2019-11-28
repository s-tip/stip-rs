from django.shortcuts import render
from ctirs.core.common import get_text_field_value, get_common_replace_dict
from ctirs.error.views import error_page, error_page_inactive
from ctirs.models import STIPUser
from django.contrib.auth.decorators import login_required

def get_profile_change_password_old_password(request):
    return get_text_field_value(request,'old_password',default_value='')

def get_profile_change_password_new_password(request):
    return get_text_field_value(request,'new_password',default_value='')

def get_profile_change_screen_name_screen_name(request):
    return get_text_field_value(request,'screen_name',default_value='')

@login_required
def top(request,msg=None):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    try:
        replace_dict = get_common_replace_dict(request)
        if msg is not None:
            replace_dict['error_change_password_msg'] = msg
        #レンダリング
        return render(request,'profile.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def change_password(request):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)

    try:
        replace_dict = get_common_replace_dict(request)
        old_password = get_profile_change_password_old_password(request)
        new_password = get_profile_change_password_new_password(request)
        user = request.user
        #古いパスワードが正しいかチェック
        if user.check_password(old_password) != True:
            #古いパスワードが間違っている
            replace_dict['error_change_password_msg'] = 'Old Password is wrong!!'
            return render(request,'profile.html',replace_dict)
        #新しいパスワードに変更
        user.set_password(new_password)
        if user.username == 'admin':
            #build_in account のパスワード変更
            STIPUser.change_build_password(new_password)
        user.is_modified_password = True
        user.save()
        #レンダリング
        return render(request,'change_password_done.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

@login_required
def change_screen_name(request):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    try:
        replace_dict = get_common_replace_dict(request)
        screen_name = get_profile_change_screen_name_screen_name(request)
        if len(screen_name) == 0:
            #スクリーン名長が0
            return render(request,'profile.html',replace_dict)
        user = request.user
        user.screen_name = screen_name
        user.save()
        replace_dict['info_change_screen_msg'] = 'Change Screen Name Success!!'
        #レンダリング
        return render(request,'profile.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)
