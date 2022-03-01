import json
import tempfile
import traceback
from stix2 import parse
from stix2.v21.common import LanguageContent
from stix2.v21.bundle import Bundle
from stix2.v21.sdo import Opinion, Identity, Note
from django.http import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from stip.common import get_text_field_value
from stip.common.stip_stix2 import _get_stip_identname
from ctirs.api import error, get_normal_response_json, authentication
from ctirs.api.v1.decolators import api_key_auth
from mongoengine.queryset.visitor import Q
from ctirs.core.mongo.documents_stix import StixAttackPatterns, StixCampaignsV2,\
    StixCoursesOfActionV2, StixIdentities, StixIndicatorsV2, \
    StixIntrusionSets, StixLocations, StixMalwares,\
    StixNotes, StixObservedData, StixOpinions, \
    StixReports, StixThreatActorsV2, StixTools, \
    StixVulnerabilities, StixRelationships, StixSightings, StixLanguageContents, \
    StixOthers, StixFiles, Stix2Base
from ctirs.core.mongo.documents import Vias, Communities
from ctirs.core.stix.regist import regist
from ctirs.api.v1.package_id.views import delete_stix_file_package_id_document_info


def get_api_stix_files_v2_sighting_first_seen(request):
    return get_text_field_value(request, 'first_seen', default_value=None)


def get_api_stix_files_v2_sighting_last_seen(request):
    return get_text_field_value(request, 'last_seen', default_value=None)


def get_api_stix_files_v2_sighting_count(request):
    return get_text_field_value(request, 'count', default_value=0)


def get_api_stix_files_v2_common_object_id(request):
    return get_text_field_value(request, 'object_id', default_value=None)


def get_api_stix_files_v2_opinion_object_id(request):
    return get_api_stix_files_v2_common_object_id(request)


def get_api_stix_files_v2_opinion_opinion(request):
    return get_text_field_value(request, 'opinion', default_value=None)


def get_api_stix_files_v2_opinion_explanation(request):
    return get_text_field_value(request, 'explanation', default_value=None)


def get_api_stix_files_v2_note_object_id(request):
    return get_api_stix_files_v2_common_object_id(request)


def get_api_stix_files_v2_note_abstract(request):
    return get_text_field_value(request, 'abstract', default_value=None)


def get_api_stix_files_v2_note_content(request):
    return get_text_field_value(request, 'content', default_value=None)


def get_api_stix_files_v2_mark_revoke_object_id(request):
    return get_api_stix_files_v2_common_object_id(request)


def get_api_stix_files_v2_update_json(request):
    return get_api_stix_files_v2_common_object_id(request)


# /api/v1/stix_files_v2/<observed_data_id>/sighting
@csrf_exempt
@api_key_auth
def sighting(request, observed_data_id):
    ctirs_auth_user = authentication(request)
    if not ctirs_auth_user:
        return error(Exception('You have no permission for this operation.'))
    first_seen = get_api_stix_files_v2_sighting_first_seen(request)
    last_seen = get_api_stix_files_v2_sighting_last_seen(request)
    count = get_api_stix_files_v2_sighting_count(request)
    try:
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        sighting_id, content = StixSightings.create_by_observed_id(
            first_seen,
            last_seen,
            count,
            observed_data_id,
            ctirs_auth_user)

        resp = get_normal_response_json()
        d = {}
        d['sighting_object_id'] = sighting_id
        d['sighting_object_json'] = content
        resp['data'] = d
        return JsonResponse(resp, status=201, safe=False)

    except Exception as e:
        traceback.print_exc()
        return error(e)

# /api/v1/stix_files_v2/<object_ref>/language_contents
@csrf_exempt
@api_key_auth
def language_contents(request, object_ref):
    ctirs_auth_user = authentication(request)
    if not ctirs_auth_user:
        return error(Exception('You have no permission for this operation.'))
    try:
        if request.method == 'GET':
            return get_language_contents(request, object_ref)
        elif request.method == 'POST':
            return post_language_contents(request, object_ref, ctirs_auth_user)
        else:
            return HttpResponseNotAllowed(['GET', 'POST'])
    except Exception as e:
        return error(e)


def get_list_index_from_selector(selector):
    try:
        if (selector[0] == '[') and (selector[-1] == ']'):
            return int(selector[1:-1])
        return -1
    except BaseException:
        return -1


def is_exist_objects(selector, o_):
    index = get_list_index_from_selector(selector)
    if index > -1:
        return o_[index]
    else:
        if selector not in o_:
            return None
        else:
            return o_[selector]


def post_language_contents(request, object_ref, ctirs_auth_user):
    try:
        j = json.loads(request.body)
        stip_identity = _get_stip_identname(request.user)
        bundle = Bundle(stip_identity)
        object_ = get_object(object_ref)
        if object_ is None:
            return error(Exception('No document. (object_ref=%s)' % (object_ref)))

        for language_content in j['language_contents']:
            selector_str = language_content['selector']
            content_value = language_content['content']
            language = language_content['language']
            try:
                selector_elems = selector_str.split('.')
                last_elem = object_
                if len(selector_elems) == 1:
                    last_selector = selector_str
                    last_elem = is_exist_objects(selector_str, last_elem)
                else:
                    for selector in selector_elems[:-1]:
                        last_selector = selector
                        last_elem = is_exist_objects(selector, last_elem)
                        if last_elem is None:
                            raise Exception('selector is invalid: ' + str(selector_str))

                if isinstance(last_elem, list):
                    lc_lists = [''] * len(last_elem)
                    lc_lists[get_list_index_from_selector(selector_elems[-1])] = content_value
                    content = lc_lists
                    selector = '.'.join(selector_elems[:-1])
                elif isinstance(last_elem, dict):
                    content = {}
                    content[selector_elems[-1]] = content_value
                    selector = '.'.join(selector_elems[:-1])
                else:
                    content = content_value
                    selector = last_selector
            except Exception as e:
                traceback.print_exc()
                raise e

            contents = {}
            contents[language] = {selector: content}
            language_content = LanguageContent(
                created_by_ref=stip_identity,
                object_ref=object_ref,
                object_modified=object_['modified'],
                contents=contents
            )
            bundle.objects.append(language_content)

        _regist_bundle(bundle, ctirs_auth_user)
        resp = get_normal_response_json()
        bundle_json = json.loads(str(bundle))
        resp['data'] = {'bundle': bundle_json}
        return JsonResponse(resp, status=201, safe=False)
    except Exception as e:
        traceback.print_exc()
        return error(e)


def _regist_bundle(bundle, ctirs_auth_user):
    via = Vias.get_via_rest_api_upload(uploader=ctirs_auth_user.id)
    community = Communities.get_default_community()
    stix_file_path = tempfile.mktemp(suffix='.json')
    with open(stix_file_path, 'wb+') as fp:
        fp.write(bundle.serialize(indent=4, ensure_ascii=False).encode('utf-8'))
    regist(stix_file_path, community, via)


def get_language_contents(request, object_ref):
    try:
        object_modified = request.GET['object_modified']
        objects = StixLanguageContents.objects.filter(
            Q(object_ref=object_ref) & Q(object_modified=object_modified)).order_by('-modified')
        language_contents = []
        for o_ in objects:
            language_contents.append(o_.object_)
        resp = get_normal_response_json()
        resp['data'] = language_contents
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# /api/v1/stix_files_v2/object/<object_id>
@csrf_exempt
@api_key_auth
def object_main(request, object_id):
    try:
        if request.method == 'GET':
            return _get_object_main(request, object_id)
        if request.method == 'DELETE':
            return _delete_object_main(request, object_id)
        return HttpResponseNotAllowed(['GET', 'DELETE'])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)


# GET /api/v1/stix_files_v2/object/<object_id>
def _get_object_main(request, object_id):
    object_ = get_object(object_id)
    resp = get_normal_response_json()
    if object_:
        resp['data'] = object_
    else:
        resp['data'] = None
    return JsonResponse(resp, status=200, safe=False)


# DELETE /api/v1/stix_files_v2/object/<object_id>
def _delete_object_main(request, object_id):
    doc = _get_document(object_id)
    if not doc:
        return error(Exception(object_id + ' does not exist.'))
    try:
        delete_stix_file_package_id_document_info(doc.package_id)
        resp = get_normal_response_json()
        resp['data'] = {'remove_package_id': doc.package_id}
        return JsonResponse(resp, status=200, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)


def get_object(object_id):
    doc = _get_document(object_id)
    if not doc:
        return None
    return doc.object_


def _get_document(object_id):
    collections = [StixAttackPatterns, StixCampaignsV2,
                   StixCoursesOfActionV2, StixIdentities, StixIndicatorsV2,
                   StixIntrusionSets, StixLocations, StixMalwares,
                   StixNotes, StixObservedData, StixOpinions,
                   StixReports, StixThreatActorsV2, StixTools,
                   StixVulnerabilities, StixRelationships, StixSightings, StixLanguageContents, StixOthers]
    doc = None
    for collection in collections:
        docs = collection.objects.filter(object_id_=object_id)
        if not docs:
            continue
        return docs.order_by('-modified').limit(1)[0]
    return doc


# /api/v1/stix_files_v2/search_bundle
@api_key_auth
def search_bundle(request):
    SEARCH_KEY_OBJECT_ID = 'match[object_id]'
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        package_id_list = []
        if SEARCH_KEY_OBJECT_ID in request.GET.keys():
            object_id = request.GET[SEARCH_KEY_OBJECT_ID]
            doc = _get_document(object_id)
            package_id_list.append(doc.package_id)
        else:
            for doc in StixFiles.objects.filter(version__startswith='2.').order_by('-modified'):
                if doc.package_id not in package_id_list:
                    package_id_list.append(doc.package_id)
        resp = get_normal_response_json()
        d = {}
        d['package_id_list'] = package_id_list
        resp['data'] = d
        return JsonResponse(resp, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)


# /api/v1/stix_files_v2/create_opinion
@csrf_exempt
@api_key_auth
def create_opinion(request):
    try:
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        object_id = get_api_stix_files_v2_opinion_object_id(request)
        opinion = get_api_stix_files_v2_opinion_opinion(request)
        explanation = get_api_stix_files_v2_opinion_explanation(request)

        stip_identity = _get_stip_identname(request.user)
        ctirs_auth_user = authentication(request)

        opinion_o = Opinion(
            explanation=explanation,
            created_by_ref=stip_identity,
            opinion=opinion,
            object_refs=[object_id]
        )
        bundle = Bundle(stip_identity, opinion_o)
        _regist_bundle(bundle, ctirs_auth_user)
        resp = get_normal_response_json()
        return JsonResponse(resp, status=201, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)


# /api/v1/stix_files_v2/create_note
@csrf_exempt
@api_key_auth
def create_note(request):
    try:
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        object_id = get_api_stix_files_v2_note_object_id(request)
        abstract = get_api_stix_files_v2_note_abstract(request)
        content = get_api_stix_files_v2_note_content(request)

        stip_identity = _get_stip_identname(request.user)
        ctirs_auth_user = authentication(request)

        note_o = Note(
            abstract=abstract,
            created_by_ref=stip_identity,
            content=content,
            authors=[ctirs_auth_user.screen_name],
            object_refs=[object_id]
        )
        bundle = Bundle(stip_identity, note_o)
        _regist_bundle(bundle, ctirs_auth_user)
 
        resp = get_normal_response_json()
        return JsonResponse(resp, status=201, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)

# /api/v1/stix_files_v2/mark_revoke
@csrf_exempt
@api_key_auth
def mark_revoke(request):
    try:
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        object_id = get_api_stix_files_v2_mark_revoke_object_id(request)

        ctirs_auth_user = authentication(request)

        try:
            o_ = Stix2Base.newest_find(object_id)
        except IndexError:
            message = '%s does not exist (2)' % (object_id)
            print(message)
            return error(Exception(message))
        if o_ is None:
            message = '%s does not exist' % (object_id)
            print(message)
            return error(Exception(message))
        if o_.revoked:
            message = '%s already has been revoked' % (object_id)
            print(message)
            return error(Exception(message))
        # <todo> check matching created_by_ref
        d = Stix2Base.get_revoked_dict(o_)
        revoked_obj = parse(d, allow_custom=True)

        bundle = Bundle(revoked_obj, allow_custom=True)
        _regist_bundle(bundle, ctirs_auth_user)
        resp = get_normal_response_json()
        return JsonResponse(resp, status=201, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)

# /api/v1/stix_files_v2/update
@csrf_exempt
@api_key_auth
def update(request):
    try:
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        
        stix2 = json.loads(request.body)

        ctirs_auth_user = authentication(request)

        object_id = stix2['id']
        before = Stix2Base.newest_find(object_id)
        if before is None:
            message = '%s does not exist' % (object_id)
            print(message)
            return error(Exception(message))
        if before.revoked:
            message = '%s already has been revoked' % (object_id)
            print(message)
            return error(Exception(message))
        # <todo> check matching created_by_ref
        d = Stix2Base.get_modified_dict(before, stix2)
        modified_obj = parse(d, allow_custom=True)
        bundle = Bundle(modified_obj, allow_custom=True)
        _regist_bundle(bundle, ctirs_auth_user)
        resp = get_normal_response_json()
        return JsonResponse(resp, status=201, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)