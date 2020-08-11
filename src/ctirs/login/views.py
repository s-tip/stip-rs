import django.contrib.auth
import pyotp
from django.shortcuts import render
from django.http.response import HttpResponseRedirect
from ctirs.core.common import get_text_field_value
from ctirs.profile.views import top as profile_top
from ctirs.models import STIPUser

def get_login_username(request):
    return get_text_field_value(request, 'username', default_value='')


def get_login_passwrod(request):
    return get_text_field_value(request, 'password', default_value='')


def get_login_authcode(request):
    return get_text_field_value(request, 'authcode', default_value='')

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
            request.session['username'] = username
            if not user.is_modified_password:
                # 初回ログイン時はパスワード変更画面に飛ばす
                return profile_top(request, msg='Please Change Your Password!!!')
            else:
                # 認証成功
                user = STIPUser.objects.get(username=username)
                if user.totp_secret is None:
                    # 初期画面のdashboardへ
                    return HttpResponseRedirect('/dashboard/')
                else:
                    # Authentication Code 入力画面へ
                    return render(request, 'cover_totp.html')
    else:
        # user/passwordが一致しない
        replace_dict['error_msg'] = 'Login Failed'
    
    # エラー表示(ログイン画面へ)
    return render(request, 'cover.html', replace_dict)


def login_totp(request):
    replace_dict = {}
    # session から Username 取得
    username = request.session['username']
    # テキストフィールドから Authentication Code 取得
    authcode = get_login_authcode(request)
    # 共通鍵の取得・設定
    user = STIPUser.objects.get(username=username)
    totp = pyotp.TOTP(user.totp_secret)
    
    # 認証
    if totp.verify(authcode):
        # 認証成功(初期画面のdashboardへ)
        return HttpResponseRedirect('/dashboard/')
    else:
        # 認証失敗( Authentication Code 入力画面を表示)
        replace_dict['error_msg'] = 'Two-factor authentication failed.'
        return render(request, 'cover_totp.html', replace_dict)


