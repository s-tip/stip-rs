from django.http.response import HttpResponse


def ajax_required(f):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
