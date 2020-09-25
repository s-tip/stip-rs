import stip.common.login as login_views

REDIRECT_TO = 'dashboard'


def login(request):
    return login_views.login(request, REDIRECT_TO)


def login_totp(request):
    return login_views.login_totp(request, REDIRECT_TO)
