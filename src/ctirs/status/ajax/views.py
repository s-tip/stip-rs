from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.poll.views import get_client


def get_list_delete_status_id(request):
    return get_text_field_value(request, 'status_id', default_value=None)


def get_list_delete_taxii_id(request):
    return get_text_field_value(request, 'taxii_id', default_value=None)


@login_required
def check(request):
    try:
        if request.method != 'GET':
            raise Exception('Invalid HTTP method')
        if not request.user.is_active:
            raise Exception('Your account is inactive')

        taxii_id = get_list_delete_taxii_id(request)
        if taxii_id is None:
            raise Exception('Invalid TAXII ID')
        status_id = get_list_delete_status_id(request)
        if status_id is None:
            raise Exception('Invalid status ID')
        _, cl = get_client('2.x', taxii_id)
        js = cl.status(status_id)
        r = {'status': 'OK',
             'data': js}
    except Exception as e:
        r = {'status': 'NG',
             'message': str(e)}
    finally:
        return JsonResponse(r, safe=False)
