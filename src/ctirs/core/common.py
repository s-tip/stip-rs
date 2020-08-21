from stip.common import get_text_field_value
from ctirs.core.mongo.documents import TaxiiClients, Taxii2Clients


def get_trim_double_quotation(s):
    return s.strip('\"')


def get_next_location(request):
    return get_text_field_value(request, 'next', default_value='/')


def get_common_replace_dict(request):
    replace_dict = {}
    replace_dict['user'] = request.user
    replace_dict['taxiis'] = TaxiiClients.objects
    replace_dict['taxii2s'] = Taxii2Clients.objects
    return replace_dict
