from django.shortcuts import render
from ctirs.core.common import get_text_field_value, get_common_replace_dict
from ctirs.error.views import error_page, error_page_no_view_permission, error_page_free_format, error_page_inactive
from django.contrib.auth.decorators import login_required
from ctirs.models.rs.models import STIPUser
from ctirs.core.mongo.documents import Taxii2Clients, Communities


def get_taxii2_client_create_display_name(request):
    return get_text_field_value(request, 'display_name', default_value='')


def get_taxii2_client_create_api_root(request):
    return get_text_field_value(request, 'api_root', default_value='')


def get_taxii2_client_create_collection(request):
    return get_text_field_value(request, 'collection', default_value='')


def get_taxii2_client_create_login_id(request):
    return get_text_field_value(request, 'login_id', default_value='')


def get_taxii2_client_create_login_password(request):
    return get_text_field_value(request, 'login_password', default_value='')


def get_taxii2_client_create_community_id(request):
    return get_text_field_value(request, 'community_id', default_value='')


def get_taxii2_client_create_protocol_version(request):
    return get_text_field_value(request, 'protocol_version', default_value='')


def get_taxii2_client_create_push(request):
    return 'push' in request.POST


def get_taxii2_client_create_uploader_id(request):
    return get_text_field_value(request, 'uploader_id', default_value='')


def get_taxii2_client_delete_display_name(request):
    return get_text_field_value(request, 'display_name', default_value='')


def get_taxii2_client_create_can_read(request):
    return 'can_read' in request.POST


def get_taxii2_client_create_can_write(request):
    return 'can_write' in request.POST


@login_required
def top(request):
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        replace_dict = _get_taxii2_client_common_replace_dict(request)
        return render(request, 'taxii2_client.html', replace_dict)
    except Exception:
        return error_page(request)


@login_required
def create(request):
    if request.method != 'POST':
        return error_page_free_format(request, 'invalid method')
    if not request.user.is_active:
        return error_page_inactive(request)
    try:
        setting_name = get_taxii2_client_create_display_name(request)
        if(setting_name is None or len(setting_name) == 0):
            return error_page_free_format(request, 'No Display Name.')
        api_root = get_taxii2_client_create_api_root(request)
        if(api_root is None or len(api_root) == 0):
            return error_page_free_format(request, 'No API Root.')
        collection = get_taxii2_client_create_collection(request)
        if(collection is None or len(collection) == 0):
            return error_page_free_format(request, 'No Collection.')
        login_id = get_taxii2_client_create_login_id(request)
        login_password = get_taxii2_client_create_login_password(request)
        community_id = get_taxii2_client_create_community_id(request)
        protocol_version = get_taxii2_client_create_protocol_version(request)
        push = get_taxii2_client_create_push(request)
        uploader_id = int(get_taxii2_client_create_uploader_id(request))
        can_read = get_taxii2_client_create_can_read(request)
        can_write = get_taxii2_client_create_can_write(request)

        Taxii2Clients.create(
            setting_name,
            api_root=api_root,
            collection=collection,
            login_id=login_id,
            login_password=login_password,
            community_id=community_id,
            protocol_version=protocol_version,
            push=push,
            uploader_id=uploader_id,
            can_read=can_read,
            can_write=can_write)
        replace_dict = _get_taxii2_client_common_replace_dict(request)
        replace_dict['info_msg'] = 'Create or Modify Success!!'
        return render(request, 'taxii2_client.html', replace_dict)
    except Exception:
        return error_page(request)


@login_required
def delete(request):
    if request.method != 'GET':
        return error_page_free_format(request, 'invalid method')
    if not request.user.is_active:
        return error_page_inactive(request)
    try:
        display_name = get_taxii2_client_delete_display_name(request)
        if(display_name is None or len(display_name) == 0):
            return error_page_free_format(request, 'No Display Name.')
        taxii = Taxii2Clients.objects.get(name=display_name)
        taxii.delete()
        replace_dict = _get_taxii2_client_common_replace_dict(request)
        replace_dict['info_msg'] = 'Delete Success!!'
        return render(request, 'taxii2_client.html', replace_dict)
    except Exception:
        return error_page(request)


def _get_taxii2_client_common_replace_dict(request):
    replace_dict = get_common_replace_dict(request)
    replace_dict['taxii2_clients'] = Taxii2Clients.objects.all()
    replace_dict['protocol_versions'] = Taxii2Clients.get_protocol_versions()
    replace_dict['communities'] = Communities.objects.all()
    replace_dict['users'] = STIPUser.objects.all()
    return replace_dict
