import json
import tempfile
import traceback
from stix2.v21.common import LanguageContent
from stix2.v21.bundle import Bundle
from django.http import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from ctirs.api import error, get_normal_response_json, authentication
from ctirs.core.common import get_text_field_value
from mongoengine import DoesNotExist
from mongoengine.queryset.visitor import Q
from ctirs.core.mongo.documents_stix import StixAttackPatterns, StixCampaignsV2,\
    StixCoursesOfActionV2, StixIdentities, StixIndicatorsV2, \
    StixIntrusionSets, StixLocations, StixMalwares,\
    StixNotes, StixObservedData, StixOpinions, \
    StixReports, StixThreatActorsV2, StixTools, \
    StixVulnerabilities, StixRelationships, StixSightings, StixLanguageContents, StixOthers
from ctirs.core.mongo.documents import Vias, Communities
from ctirs.core.stix.regist import regist
from stip.common.stip_stix2 import _get_stip_identname


def get_api_stix_files_v2_sighting_first_seen(request):
    return get_text_field_value(request, 'first_seen', default_value=None)


def get_api_stix_files_v2_sighting_last_seen(request):
    return get_text_field_value(request, 'last_seen', default_value=None)


def get_api_stix_files_v2_sighting_count(request):
    return get_text_field_value(request, 'count', default_value=0)

# /api/v1/stix_files_v2/<observed_data_id>/sighting
# GET/POSTの受付
@csrf_exempt
def sighting(request, observed_data_id):
    # apikey認証
    ctirs_auth_user = authentication(request)
    if ctirs_auth_user is None:
        return error(Exception('You have no permission for this operation.'))
    first_seen = get_api_stix_files_v2_sighting_first_seen(request)
    last_seen = get_api_stix_files_v2_sighting_last_seen(request)
    count = get_api_stix_files_v2_sighting_count(request)
    # first_seen, last_seen, optional とも option
    try:
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])

        # SightingObjects 作成
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
# GET/POSTの受付
@csrf_exempt
def language_contents(request, object_ref):
    # apikey認証
    ctirs_auth_user = authentication(request)
    if ctirs_auth_user is None:
        return error(Exception('You have no permission for this operation.'))
    try:
        if request.method == 'GET':
            # language_contents 取得
            return get_language_contents(request, object_ref)
        elif request.method == 'POST':
            # language_contents 作成
            return post_language_contents(request, object_ref, ctirs_auth_user)
        else:
            return HttpResponseNotAllowed(['GET', 'POST'])
    except Exception as e:
        return error(e)


# セレクタがリストの要素を表しているか
# 異なる場合は -1, 表している場合はその index
def get_list_index_from_selector(selector):
    try:
        if (selector[0] == '[') and (selector[-1] == ']'):
            return int(selector[1:-1])
        return -1
    except BaseException:
        return -1


# o_ の中に selector に示されたキーが存在するか?
def is_exist_objects(selector, o_):
    # list 要素チェック
    index = get_list_index_from_selector(selector)
    if index > -1:
        # list
        return o_[index]
    else:
        # dict
        if selector not in o_:
            return None
        else:
            return o_[selector]


def get_selector_trimed_last_index(selector):
    elems = selector.split('')


# language_contents 作成
def post_language_contents(request, object_ref, ctirs_auth_user):
    try:
        j = json.loads(request.body)
        # S-TIP Identity 作成する
        stip_identity = _get_stip_identname(request.user)
        # bundle 作成
        bundle = Bundle(stip_identity)
        # 参照元の obejct を取得
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
                # selector の 要素をチェックする
                if len(selector_elems) == 1:
                    # selector が . でつながられていない場合
                    last_selector = selector_str
                    last_elem = is_exist_objects(selector_str, last_elem)
                else:
                    # selector が . でつながられている場合は最後までたどる
                    for selector in selector_elems[:-1]:
                        last_selector = selector
                        last_elem = is_exist_objects(selector, last_elem)
                        if last_elem is None:
                            raise Exception('selector is invalid: ' + str(selector_str))

                if isinstance(last_elem, list):
                    # 空要素で初期化し、該当 index の要素だけ上書きする
                    lc_lists = [''] * len(last_elem)
                    lc_lists[get_list_index_from_selector(selector_elems[-1])] = content_value
                    content = lc_lists
                    selector = '.'.join(selector_elems[:-1])
                elif isinstance(last_elem, dict):
                    # 空辞書で初期化し、該当 index の要素だけ上書きする
                    content = {}
                    content[selector_elems[-1]] = content_value
                    selector = '.'.join(selector_elems[:-1])
                else:
                    # list ではない
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

        # viaを取得
        via = Vias.get_via_rest_api_upload(uploader=ctirs_auth_user.id)
        community = Communities.get_default_community()
        # stixファイルを一時ファイルに出力
        stix_file_path = tempfile.mktemp(suffix='.json')
        with open(stix_file_path, 'wb+') as fp:
            fp.write(bundle.serialize(indent=4, ensure_ascii=False))
        # 登録処理
        regist(stix_file_path, community, via)
        resp = get_normal_response_json()
        bundle_json = json.loads(str(bundle))
        resp['data'] = {'bundle': bundle_json}
        return JsonResponse(resp, status=201, safe=False)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# language_contents  取得
def get_language_contents(request, object_ref):
    try:
        # 表示する長さ
        object_modified = request.GET['object_modified']
        objects = StixLanguageContents.objects.filter(
            Q(object_ref=object_ref)
            & Q(object_modified=object_modified)).order_by('-modified')
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
# object_id からその object の中身を返却する
@csrf_exempt
def get_object_main(request, object_id):
    # apikey認証
    ctirs_auth_user = authentication(request)
    if ctirs_auth_user is None:
        return error(Exception('You have no permission for this operation.'))
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        object_ = get_object(object_id)
        resp = get_normal_response_json()
        if object_ is None:
            resp['data'] = None
        else:
            resp['data'] = object_
        return JsonResponse(resp, status=200, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)


# object_id から object 情報取得
def get_object(object_id):
    collections = [StixAttackPatterns, StixCampaignsV2,
                   StixCoursesOfActionV2, StixIdentities, StixIndicatorsV2,
                   StixIntrusionSets, StixLocations, StixMalwares,
                   StixNotes, StixObservedData, StixOpinions,
                   StixReports, StixThreatActorsV2, StixTools,
                   StixVulnerabilities, StixRelationships, StixSightings, StixLanguageContents, StixOthers]
    doc = None
    for collection in collections:
        try:
            doc = collection.objects.get(object_id_=object_id)
            break
        except DoesNotExist:
            pass
    if doc is None:
        return doc
    return doc.object_
