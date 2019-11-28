import django.contrib.auth
from django.http.response import HttpResponseRedirect


# ログアウト
def logout(request):
    django.contrib.auth.logout(request)
    # ログイン画面へ
    return HttpResponseRedirect('/')
