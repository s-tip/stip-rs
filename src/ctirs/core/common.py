from django.utils.datastructures import MultiValueDictKeyError
from ctirs.core.mongo.documents import TaxiiClients, Taxii2Clients


def get_trim_double_quotation(s):
    return s.strip('\"')


def get_text_field_value(request, item_name, default_value=None):
    if request.method == 'GET':
        l = request.GET
    elif request.method == 'POST':
        l = request.POST
    else:
        return default_value
    try:
        v = l[item_name]
        if len(v) == 0:
            return default_value
        else:
            return v.strip()
    except MultiValueDictKeyError:
        return default_value


def get_next_location(request):
    return get_text_field_value(request, 'next', default_value='/')


def get_common_replace_dict(request):
    replace_dict = {}
    replace_dict['user'] = request.user
    replace_dict['taxiis'] = TaxiiClients.objects
    replace_dict['taxii2s'] = Taxii2Clients.objects
    return replace_dict
