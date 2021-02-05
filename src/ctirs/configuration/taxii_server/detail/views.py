from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stip.common import get_text_field_value
from ctirs.configuration.taxii_server.views import restart_taxii_server
from ctirs.core.common import get_common_replace_dict
from ctirs.core.mongo.documents import TaxiiServers, Communities
from ctirs.error.views import error_page, error_page_no_view_permission, error_page_inactive


def get_configuartion_taxii_server_detail_collection_name(request):
    return get_text_field_value(request, 'collection_name', default_value=None)


def get_configuartion_taxii_server_detail_communities(request):
    is_str = get_text_field_value(request, 'communities', default_value=None)
    if is_str is None:
        return []
    else:
        return is_str.split(',')


@login_required
def top(request, taxii_id):
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        replace_dict = get_taxii_server_detail_common_replace_dict(request, taxii_id)
        return render(request, 'configuration_taxii_server_detail.html', replace_dict)
    except Exception:
        return error_page(request)


@login_required
def modify(request, taxii_id):
    if not request.user.is_active:
        return error_page_inactive(request)
    if not request.user.is_admin:
        return error_page_no_view_permission(request)
    try:
        collection_name = get_configuartion_taxii_server_detail_collection_name(request)
        arg_communities = get_configuartion_taxii_server_detail_communities(request)
        taxii_server = TaxiiServers.objects.get(id=taxii_id)
        taxii_server.collection_name = collection_name
        communities = []
        for arg_community in arg_communities:
            d = Communities.objects.get(id=arg_community)
            communities.append(d)
        taxii_server.communities = communities
        taxii_server.save()
        restart_taxii_server()
        replace_dict = get_taxii_server_detail_common_replace_dict(request, taxii_id)
        replace_dict['info_msg'] = 'Modify & Restart Success!!'
        return render(request, 'configuration_taxii_server_detail.html', replace_dict)
    except Exception:
        return error_page(request)


def get_taxii_server_detail_common_replace_dict(request, taxii_id):
    replace_dict = get_common_replace_dict(request)
    replace_dict['communities'] = Communities.objects.all()
    replace_dict['taxii_server'] = TaxiiServers.objects.get(id=taxii_id)
    return replace_dict
