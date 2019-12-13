from django.shortcuts import render
from ctirs.core.common import get_common_replace_dict


def top(request):
    if not request.user.is_authenticated():
        return render(request, 'cover.html')
    else:
        replace_dict = get_common_replace_dict(request)
        return render(request, 'dashboard.html', replace_dict)
