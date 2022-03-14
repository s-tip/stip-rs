from django.contrib.auth.decorators import login_required
from django.db.models import Q as QQ
from django.http import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from mongoengine.queryset.visitor import Q
from mongoengine import DoesNotExist
from ctirs.api import JsonResponse
from ctirs.core.mongo.documents import Communities, Vias, TaxiiClients, Taxii2Clients
from ctirs.core.mongo.documents_stix import StixFiles
from ctirs.core.taxii.taxii import Client
from ctirs.models.rs.models import STIPUser
from ctirs.core.adapter.misp.upload.control import MispUploadAdapterControl


@login_required
def get_table_info(request):
    iDisplayLength = int(request.GET['iDisplayLength'])
    sEcho = request.GET['sEcho']
    iDisplayStart = int(request.GET['iDisplayStart'])
    sSearch = request.GET['sSearch']

    sort_col = int(request.GET['iSortCol_0'])
    sort_dir = request.GET['sSortDir_0']
    order_query = None
    if sort_col == 1:
        order_query = 'modified'
    elif sort_col == 2:
        order_query = 'package_name'
    elif sort_col == 3:
        order_query = 'package_id'
    elif sort_col == 4:
        order_query = 'version'

    if order_query is not None:
        if sort_dir == 'desc':
            order_query = '-' + order_query

    s_input_communities = Communities.objects.filter(Q(name__icontains=sSearch))
    s_via_choices = Vias.get_search_via_choices(sSearch)
    s_uploaders = []
    for uploader in STIPUser.objects.filter(QQ(screen_name__icontains=sSearch) | QQ(username__icontains=sSearch)):
        s_uploaders.append(uploader.id)
    s_vias = Vias.objects.filter(Q(via__in=s_via_choices) | Q(uploader__in=s_uploaders) | Q(adapter_name__icontains=sSearch))

    objects = StixFiles.objects \
        .filter(
            Q(package_name__icontains=sSearch)
            | Q(package_id__icontains=sSearch)
            | Q(version__icontains=sSearch)
            | Q(input_community__in=s_input_communities)
            | Q(via__in=s_vias)
        )\
        .order_by(order_query)

    aaData = []
    count = 0
    for d in objects[iDisplayStart:(iDisplayStart + iDisplayLength)]:
        l = []
        l.append('<input type="checkbox" file_id="%s"/ class="delete-checkbox">' % (d.id))
        l.append(d.modified.strftime('%Y/%m/%d %H:%M:%S'))
        l.append(d.package_name)
        l.append(d.package_id)
        l.append(d.version)
        try:
            l.append(d.input_community.name)
        except DoesNotExist:
            l.append('&lt;deleted&gt;')
        l.append(d.via.get_via_display())
        l.append(d.via.get_uploader_screen_name())
        link_str = ''
        if d.version.startswith('1.'):
            link_str += '<a href="/list/download?id=%s&version=%s">STIX %s (Original)</a><br/>' % (d.id, d.version, d.version)
            link_str += ('<a href="/list/download?id=%s&version=2.1">STIX 2.1</a>' % (d.id))
        elif d.version == '2.0':
            link_str += ('<a href="/list/download?id=%s&version=1.2">STIX 1.2</a><br/>' % (d.id))
            link_str += ('<a href="/list/download?id=%s&version=2.0">STIX 2.0 (Original)</a><br/>' % (d.id))
            link_str += ('<a href="/list/download?id=%s&version=2.1">STIX 2.1</a>' % (d.id))
        elif d.version == '2.1':
            link_str += ('<a href="/list/download?id=%s&version=1.2">STIX 1.2</a><br/>' % (d.id))
            link_str += ('<a href="/list/download?id=%s&version=2.1">STIX 2.1 (Original)</a>' % (d.id))
        l.append(link_str)
        if request.user.is_admin:
            l.append('<a><span class="glyphicon glyphicon-share-alt publish-share-alt-icon" data-file-id="%s" data-package-name="%s" data-package-id="%s" title="Publish to.."></span></a>' % (d.id, d.package_name, d.package_id))
        else:
            l.append('<span class="glyphicon glyphicon-ban-circle" disabled></span>')
        link_str = ('<a><span class="glyphicon glyphicon-export misp-import-icon" package_id="%s" title="Import into MISP .."></span></a>' % (d.package_id))
        l.append(link_str)
        aaData.append(l)
        count += 1

    resp = {}
    all_count = StixFiles.objects.count()
    resp['iTotalRecords'] = all_count
    resp['iTotalDisplayRecords'] = objects.count()
    resp['sEcho'] = sEcho
    resp['aaData'] = aaData
    return JsonResponse(resp)


@login_required
def publish(request):
    stix_id = request.GET['stix_id']
    taxii_id = request.GET['taxii_id']
    protocol_version = request.GET['protocol_version']
    stix = StixFiles.objects.get(id=stix_id)
    if protocol_version.startswith('1.'):
        taxii_client = TaxiiClients.objects.get(id=taxii_id)
        client = Client(taxii_client=taxii_client)
    else:
        taxii_client = Taxii2Clients.objects.get(id=taxii_id)
        client = Client(taxii2_client=taxii_client)
    if not client._can_write:
        resp = {'status': 'NG',
                'message': 'This collection is not for publishing.'}
        return JsonResponse(resp)
    try:
        msg = client.push(stix)
        resp = {'status': 'OK',
                'message': msg}
    except Exception as e:
        resp = {'status': 'NG',
                'message': str(e)}
    return JsonResponse(resp)


@login_required
@csrf_exempt
def misp_import(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        package_id = request.POST['package_id']
        control = MispUploadAdapterControl()
        control.upload_misp(package_id)
        resp = {'status': 'OK',
                'message': 'Success'}
    except Exception as e:
        resp = {'status': 'NG',
                'message': str(e)}
    return JsonResponse(resp)
