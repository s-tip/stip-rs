import ctirs.api as api_root


def api_key_auth(f):
    def wrap(request, *args, **kwargs):
        ctirs_auth_user = api_root.authentication(request)
        if ctirs_auth_user is None:
            return api_root.error(Exception('You have no permission for this operation.'))
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
