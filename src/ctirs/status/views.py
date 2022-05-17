import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.error.views import error_page_inactive, error_page_free_format, error_page
from ctirs.core.common import get_common_replace_dict
from ctirs.core.mongo.documents import Taxii2Statuses


def get_list_delete_status_id(request):
    return json.loads(get_text_field_value(request, 'status_id', default_value=[]))


@login_required
def top(request):
    if not request.user.is_active:
        return error_page_inactive(request)
    replace_dict = get_common_replace_dict(request)
    replace_dict['statuses'] = Taxii2Statuses.objects
    return render(request, 'status.html', replace_dict)


@login_required
def delete(request):
    if request.method != 'GET':
        return error_page_free_format(request, 'Invalid HTTP Method.')
    if not request.user.is_active:
        return error_page_inactive(request)
    delete_list = get_list_delete_status_id(request)
    try:
        for status_id in delete_list:
            doc = Taxii2Statuses.objects(status_id=status_id)
            doc.delete()
        return redirect('status')
    except Exception:
        return error_page(request)
