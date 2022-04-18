import pytz
import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.core.common import get_common_replace_dict
from ctirs.error.views import error_page, error_page_no_view_permission, error_page_inactive
from ctirs.core.mongo.documents import TaxiiClients, Taxii2Clients
from ctirs.core.taxii.taxii import Client

DEFAULT_LIMIT_NUM = 10


def get_start_start(request):
    return get_text_field_value(request, 'poll_start', default_value=None)


def get_start_end(request):
    return get_text_field_value(request, 'poll_end', default_value=None)


def get_protocol_version(request):
    return get_text_field_value(request, 'protocol_version', default_value=None)


def get_limit(request):
    try:
        return int(get_text_field_value(request, 'poll_limit', default_value=DEFAULT_LIMIT_NUM))
    except ValueError:
        return DEFAULT_LIMIT_NUM


def get_next(request):
    return get_text_field_value(request, 'poll_next', default_value=None)


def get_match_id(request):
    return get_text_field_value(request, 'poll_match_id', default_value=None)


def get_match_spec_version(request):
    return get_text_field_value(request, 'poll_match_spec_version', default_value=None)


def get_match_type(request):
    return get_text_field_value(request, 'poll_match_type', default_value=None)


def get_match_version(request):
    return get_text_field_value(request, 'poll_match_version', default_value=None)


@login_required
def top(request):
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        replace_dict = get_common_replace_dict(request)
        replace_dict['taxii_clients'] = TaxiiClients.objects.all()
        replace_dict['taxii2_clients'] = Taxii2Clients.objects.all()
        return render(request, 'poll.html', replace_dict)
    except Exception:
        return error_page(request)


@login_required
def detail(request, id_):
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        protocol_version = get_protocol_version(request)
        replace_dict = get_common_replace_dict(request)
        if protocol_version.startswith('1.'):
            replace_dict['taxii'] = TaxiiClients.objects.get(id=id_)
        elif protocol_version.startswith('2.'):
            replace_dict['taxii'] = Taxii2Clients.objects.get(id=id_)
        else:
            raise Exception('Invalid taxii protocol version.')
        return render(request, 'poll_detail.html', replace_dict)
    except Exception:
        return error_page(request)


def get_datetime_from_string(str_):
    if str_ is None:
        return None
    return datetime.datetime.strptime(str_, '%Y/%m/%d %H:%M:%S').replace(tzinfo=pytz.utc)


@login_required
def start(request, id_):
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    protocol_version = get_protocol_version(request)
    start = get_datetime_from_string(get_start_start(request))
    end = get_datetime_from_string(get_start_end(request))
    limit = get_limit(request)
    next = get_next(request)
    match_id = get_match_id(request)
    match_spec_version = get_match_spec_version(request)
    match_type = get_match_type(request)
    match_version = get_match_version(request)
    try:
        replace_dict = get_common_replace_dict(request)
        filtering_params = {}
        if protocol_version.startswith('1.'):
            taxii_client = TaxiiClients.objects.get(id=id_)
            replace_dict['taxii'] = taxii_client
            cl = Client(taxii_client=taxii_client)
        elif protocol_version.startswith('2.'):
            taxii2_client = Taxii2Clients.objects.get(id=id_)
            replace_dict['taxii'] = taxii2_client
            cl = Client(taxii2_client=taxii2_client)
            filtering_params['limit'] = limit
            if next is not None:
                filtering_params['next'] = next
            match = {}
            if match_id is not None:
                match['id'] = match_id
            if match_spec_version is not None:
                match['spec_version'] = match_spec_version
            if match_type is not None:
                match['type'] = match_type
            if match_version is not None:
                match['version'] = match_version
            filtering_params['match'] = match
        else:
            raise Exception('Invalid taxii protocol version.')

        if cl._can_read:
            cl.set_start_time(start)
            cl.set_end_time(end)
            count = cl.poll(filtering_params=filtering_params)
            replace_dict['info_msg'] = 'Poll end successfully!! (Get %d stix files.)' % (count)
        else:
            replace_dict['error_msg'] = 'This collection is not for polling'
        return render(request, 'poll_detail.html', replace_dict)
    except Exception:
        return error_page(request)
