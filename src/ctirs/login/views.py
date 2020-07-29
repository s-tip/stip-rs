import django.contrib.auth
from django.shortcuts import render
from django.http.response import HttpResponseRedirect
from ctirs.core.common import get_text_field_value
from ctirs.profile.views import top as profile_top


def get_login_username(request):
    return get_text_field_value(request, 'username', default_value='')


def get_login_passwrod(request):
    return get_text_field_value(request, 'password', default_value='')


# ログイン画面を表示
def login_top(request):
    return render(request, 'cover.html', {})


# ログイン画面から認証
def login(request):
    replace_dict = {}
    # テキストフィールドからusername/password取得
    username = get_login_username(request)
    password = get_login_passwrod(request)
    # 認証
    user = django.contrib.auth.authenticate(username=username, password=password)
    if user is not None:
        # ログイン
        django.contrib.auth.login(request, user)
        if not user.is_active:
            replace_dict['error_msg'] = 'Login Failed'
        else:
            # 認証成功(初期画面のdashboardへredirect)
            if not user.is_modified_password:
                # 初回ログイン時はパスワード変更画面に飛ばす
                return profile_top(request, msg='Please Change Your Password!!!')
            else:
                return HttpResponseRedirect('/dashboard/')
    else:
        # user/passwordが一致しない
        replace_dict['error_msg'] = 'Login Failed'

    # エラー表示(ログイン画面へ)
    return render(request, 'cover.html', replace_dict)
