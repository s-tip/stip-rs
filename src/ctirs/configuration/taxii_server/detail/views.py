from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ctirs.configuration.taxii_server.views import restart_taxii_server
from ctirs.core.common import get_text_field_value, get_common_replace_dict
from ctirs.core.mongo.documents import TaxiiServers,InformationSources
from ctirs.error.views import error_page,error_page_no_view_permission, error_page_inactive

def get_configuartion_taxii_server_detail_collection_name(request):
    return get_text_field_value(request,'collection_name',default_value=None)

def get_configuartion_taxii_server_detail_information_sources(request):
    is_str = get_text_field_value(request,'information_sources',default_value=None)
    if is_str is None:
        return []
    else:
        return is_str.split(',')

@login_required
def top(request,taxii_id):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        replace_dict = get_taxii_server_detail_common_replace_dict(request,taxii_id)
        #レンダリング
        return render(request,'configuration_taxii_server_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)


@login_required
def modify(request,taxii_id):
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        return error_page_inactive(request)
    #is_admin権限なしの場合はエラー
    if request.user.is_admin == False:
        return error_page_no_view_permission(request)
    try:
        collection_name = get_configuartion_taxii_server_detail_collection_name(request)
        arg_information_sources = get_configuartion_taxii_server_detail_information_sources(request)
        taxii_server = TaxiiServers.objects.get(id=taxii_id)
        taxii_server.collection_name = collection_name
        information_sources = []
        for arg_information_source in arg_information_sources:
            d = InformationSources.objects.get(id=arg_information_source)
            information_sources.append(d)
        taxii_server.information_sources = information_sources
        taxii_server.save()
        #TXS restart
        restart_taxii_server()
        replace_dict = get_taxii_server_detail_common_replace_dict(request,taxii_id)
        replace_dict['info_msg'] = 'Modify & Restart Success!!'
        #レンダリング
        return render(request,'configuration_taxii_server_detail.html',replace_dict)
    except Exception:
        #エラーページ
        return error_page(request)

def get_taxii_server_detail_common_replace_dict(request,taxii_id):
    replace_dict = get_common_replace_dict(request)
    replace_dict['information_sources'] = InformationSources.objects.all()
    replace_dict['taxii_server'] = TaxiiServers.objects.get(id=taxii_id)
    return replace_dict
