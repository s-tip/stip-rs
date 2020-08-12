import django.contrib.auth
import pyotp
from django.shortcuts import render
from django.http.response import HttpResponseRedirect
from stip.common import get_text_field_value
from ctirs.profile.views import top as profile_top
from ctirs.models import STIPUser


def get_login_username(request):
    return get_text_field_value(request, 'username', default_value='')


def get_login_passwrod(request):
    return get_text_field_value(request, 'password', default_value='')


def get_login_authcode(request):
    return get_text_field_value(request, 'authcode', default_value='')


def login(request):
    replace_dict = {}
    username = get_login_username(request)
    password = get_login_passwrod(request)
    
    user = django.contrib.auth.authenticate(username=username, password=password)
    if user is not None:
        django.contrib.auth.login(request, user)
        if not user.is_active:
            replace_dict['error_msg'] = 'Login Failed'
        else:
            request.session['username'] = username
            if not user.is_modified_password:
                return profile_top(request, msg='Please Change Your Password!!!')
            else:
                user = STIPUser.objects.get(username=username)
                if user.totp_secret is None:
                    return HttpResponseRedirect('/dashboard/')
                else:
                    return render(request, 'cover_totp.html')
    else:
        replace_dict['error_msg'] = 'Login Failed'
    return render(request, 'cover.html', replace_dict)


def login_totp(request):
    replace_dict = {}
    username = request.session['username']
    authcode = get_login_authcode(request)

    user = STIPUser.objects.get(username=username)
    totp = pyotp.TOTP(user.totp_secret)

    if totp.verify(authcode):
        return HttpResponseRedirect('/dashboard/')
    else:
        replace_dict['error_msg'] = 'Two-factor authentication failed.'
        return render(request, 'cover_totp.html', replace_dict)
