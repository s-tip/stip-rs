import os
import json
import traceback
import datetime
import pytz
import re
import jaconv
import pykakasi
from stix2matcher import matcher
from stix.core.stix_package import STIXPackage
from mongoengine.queryset.visitor import Q
from django.http import HttpResponseNotAllowed
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ctirs.api import error, get_normal_response_json
from ctirs.core.mongo.documents import Communities
from ctirs.core.mongo.documents_stix import ObservableCaches, SimilarScoreCache, StixFiles, \
    StixCampaigns, StixIncidents, StixIndicators, StixObservables, StixThreatActors, \
    StixExploitTargets, StixCoursesOfAction, StixTTPs, ExploitTargetCaches, \
    IndicatorV2Caches, StixLanguageContents, LabelCaches, CustomObjectCaches, StixCustomObjects
from stip.common.tld import TLD
from stip.common.matching_customizer import MatchingCustomizer
from stip.common.stix_customizer import StixCustomizer
from mongoengine import DoesNotExist
from .stix2_indicator import _get_observed_data
from ctirs.models.rs.models import System
from ctirs.api.v1.decolators import api_key_auth

EXACT_EDGE_TYPE = 'Exact'
SIMILARTY_1_EDGE_TYPE = 'Similarity: 1'
SIMILARTY_2_EDGE_TYPE = 'Similarity: 2'
SIMILARTY_3_EDGE_TYPE = 'Similarity: 3'
SIMILARTY_4_EDGE_TYPE = 'Similarity: 4'
SIMILARTY_5_EDGE_TYPE = 'Similarity: 5'
SIMILARTY_6_EDGE_TYPE = 'Similarity: 6'
SIMILARTY_7_EDGE_TYPE = 'Similarity: 7'
SIMILARTY_8_EDGE_TYPE = 'Similarity: 8'

matching_patterns = MatchingCustomizer.get_instance().get_matching_patterns()
kakasi = pykakasi.kakasi()


def get_boolean_value(d, key, default_value):
    if key not in d:
        return default_value
    v = d[key]
    if default_value:
        return False if v.lower() == 'false' else True
    elif not default_value:
        return True if v.lower() == 'true' else False
    return None


# GET /api/v1/gv/l1_info_for_l1table
@api_key_auth
def l1_info_for_l1table(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        iDisplayLength = int(request.GET['iDisplayLength'])
        iDisplayStart = int(request.GET['iDisplayStart'])
        sSearch = request.GET['sSearch']
        sort_col = int(request.GET['iSortCol'])
        sort_dir = request.GET['sSortDir']
        try:
            aliases_str = request.GET['aliases']
            alias_lists = json.loads(aliases_str)
        except BaseException:
            alias_lists = []

        order_query = None

        SORT_INDEX_TYPE = 0
        SORT_INDEX_VALUE = 1
        SORT_INDEX_PACKAGE_NAME = 2
        SORT_INDEX_TILE = 3
        SORT_INDEX_DESCRIPTION = 4
        SORT_INDEX_TIMESTAMP = 5

        if sort_col == SORT_INDEX_TYPE:
            order_query = 'type'
        elif sort_col == SORT_INDEX_VALUE:
            order_query = 'value'
        elif sort_col == SORT_INDEX_PACKAGE_NAME:
            order_query = 'package_name'
        elif sort_col == SORT_INDEX_TILE:
            order_query = 'title'
        elif sort_col == SORT_INDEX_DESCRIPTION:
            order_query = 'description'
        elif sort_col == SORT_INDEX_TIMESTAMP:
            order_query = 'produced'

        if order_query is not None:
            if sort_dir == 'desc':
                order_query = '-' + order_query

        tmp_sSearches = list(set(sSearch.split(' ')))
        if '' in tmp_sSearches:
            tmp_sSearches.remove('')

        sSearches = []
        for item in tmp_sSearches:
            sSearches.append(item)
            for alias_list in alias_lists:
                if item in alias_list:
                    sSearches.extend(alias_list)

        sSearches = list(set(sSearches))

        filters = Q()
        for sSearch in sSearches:
            filters = filters | Q(type__icontains=sSearch)
            filters = filters | Q(value__icontains=sSearch)
            filters = filters | Q(package_name__icontains=sSearch)
            filters = filters | Q(title__icontains=sSearch)
            filters = filters | Q(description__icontains=sSearch)
        objects = ObservableCaches.objects.filter(filters).order_by(order_query)

        data = []
        for d in objects[iDisplayStart:(iDisplayStart + iDisplayLength)]:
            r = {}
            r['type'] = d.type
            r['value'] = d.value
            r['package_name'] = d.package_name
            r['package_id'] = d.stix_file.package_id
            r['title'] = d.title
            r['description'] = d.description
            r['created'] = str(d.created)
            r['stix_v2'] = d.stix_file.is_stix_v2()
            r['observable_id'] = d.observable_id
            data.append(r)

        r_data = {}
        r_data['iTotalRecords'] = ObservableCaches.objects.count()
        r_data['iTotalDisplayRecords'] = objects.count()
        r_data['data'] = data
        resp = get_normal_response_json()
        resp['data'] = r_data
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/package_list
@api_key_auth
def package_list(request):
    REQUIRED_COMMENT_KEY = 'required_comment'
    LIMIT_KEY = 'limit'
    ORDER_BY_KEY = 'order_by'
    DEFAULT_ORDER_BY = 'package_name'
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        required_comment = False
        if (REQUIRED_COMMENT_KEY in request.GET):
            if request.GET[REQUIRED_COMMENT_KEY].lower() == 'true':
                required_comment = True

        stix_files = StixFiles.objects.filter()
        if (ORDER_BY_KEY in request.GET):
            try:
                stix_files = stix_files.order_by(request.GET[ORDER_BY_KEY])
            except BaseException:
                stix_files = stix_files.order_by(DEFAULT_ORDER_BY)
        else:
            stix_files = stix_files.order_by(DEFAULT_ORDER_BY)

        try:
            limit = int(request.GET[LIMIT_KEY])
        except BaseException:
            limit = None
        if limit is not None:
            stix_files = stix_files[:limit]

        rsp_stix_files = []
        for stix_file in stix_files:
            rsp_stix_files.append(stix_file.get_rest_api_document_info(required_comment))
        resp = get_normal_response_json()
        resp['data'] = rsp_stix_files
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/package_name_list
@api_key_auth
def package_name_list(request):
    LIMIT_KEY = 'limit'
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        stix_files = StixFiles.objects.filter(Q(is_post_sns__ne=False)).only('package_name', 'package_id').order_by('package_name')
        try:
            limit = int(request.GET[LIMIT_KEY])
        except BaseException:
            limit = None
        if limit is not None:
            stix_files = stix_files[:limit]

        rsp_stix_files = []
        for stix_file in stix_files:
            rsp_stix_files.append(stix_file.get_rest_api_package_name_info())
        resp = get_normal_response_json()
        resp['data'] = rsp_stix_files
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


def _get_exact_matched_info(package_id):
    ret_observable_cashes = []

    cache_collections = [
        ObservableCaches,
        ExploitTargetCaches,
    ]

    for cache_collection in cache_collections:
        caches = cache_collection.objects.filter(package_id=package_id)
        for cache in caches:
            if cache.value is None:
                continue
            exacts = cache_collection.objects.filter(
                Q(type__exact=cache.type)
                & Q(value__exact=cache.value)
                & Q(package_id__ne=package_id))
            ret_observable_cashes.extend(exacts)

            if isinstance(cache, ObservableCaches):
                indicator_v2_cachses = IndicatorV2Caches.objects.filter(Q(package_id__ne=package_id))
                for indicator_v2_cache in indicator_v2_cachses:
                    observed_data = _get_observed_data(cache)
                    matches = matcher.match(indicator_v2_cache.pattern, [observed_data])
                    if len(matches) != 0:
                        indicator_v2_cache.type = cache.type
                        indicator_v2_cache.value = cache.value
                        indicator_v2_cache.start_collection = cache_collection
                        ret_observable_cashes.append(indicator_v2_cache)

    indicator_v2_caches = IndicatorV2Caches.objects.filter(package_id=package_id)
    for indicator_v2_cache in indicator_v2_caches:
        query_set = _get_observables_cashes_query(indicator_v2_cache.pattern, package_id)
        caches = ObservableCaches.objects.filter(query_set)
        for cache in caches:
            observed_data = _get_observed_data(cache)
            matches = matcher.match(indicator_v2_cache.pattern, [observed_data])
            if len(matches) != 0:
                cache.start_collection = IndicatorV2Caches
                cache.pattern = indicator_v2_cache.pattern
                ret_observable_cashes.append(cache)

        exacts = IndicatorV2Caches.objects.filter(
            Q(pattern__exact=indicator_v2_cache.pattern)
            & Q(package_id__ne=package_id))
        for exact in exacts:
            exact.cache_list = IndicatorV2Caches
            exact.start_collection = IndicatorV2Caches
            ret_observable_cashes.append(exact)

    label_caches = LabelCaches.objects.filter(package_id=package_id)
    for label_cache in label_caches:
        exacts = LabelCaches.objects.filter(
            Q(label__iexact=label_cache.label)
            & Q(package_id__ne=package_id))
        for exact in exacts:
            ret_observable_cashes.append(exact)
    return ret_observable_cashes


url_pattern = re.compile(r'url:value\s*=\s*\'(\S+)\'')
ipv4_pattern = re.compile(r'ipv4-addr:value\s*=\s*\'(\S+)\'')
domain_name_pattern = re.compile(r'domain-name:value\s*=\s*\'(\S+)\'')
md5_pattern = re.compile(r'file:hashes\.\'MD5\'\s*=\s*\'(\S+)\'')
sha1_pattern = re.compile(r'file:hashes\.\'SHA-1\'\s*=\s*\'(\S+)\'')
sha256_pattern = re.compile(r'file:hashes\.\'SHA-256\'\s*=\s*\'(\S+)\'')
sha512_pattern = re.compile(r'file:hashes\.\'SHA-512\'\s*=\s*\'(\S+)\'')


def _get_observables_cashes_query(pattern, package_id):
    q = Q()
    for v in url_pattern.findall(pattern):
        q |= (Q(package_id__ne=package_id) & Q(type__exact='uri') & Q(value__exact=v))
    for v in ipv4_pattern.findall(pattern):
        q |= (Q(package_id__ne=package_id) & Q(type__exact='ipv4') & Q(value__exact=v))
    for v in domain_name_pattern.findall(pattern):
        q |= (Q(package_id__ne=package_id) & Q(type__exact='domain_name') & Q(value__exact=v))
    for v in md5_pattern.findall(pattern):
        q |= (Q(package_id__ne=package_id) & Q(type__exact='md5') & Q(value__exact=v))
    for v in sha1_pattern.findall(pattern):
        q |= (Q(package_id__ne=package_id) & Q(type__exact='sha1') & Q(value__exact=v))
    for v in sha256_pattern.findall(pattern):
        q |= (Q(package_id__ne=package_id) & Q(type__exact='sha256') & Q(value__exact=v))
    for v in sha512_pattern.findall(pattern):
        q |= (Q(package_id__ne=package_id) & Q(type__exact='sha512') & Q(value__exact=v))
    return q


def _get_matches_observable_caches_vs_indicator_v2_cache(observable_caches, indicator_v2_cache, cache_list):
    ret_observable_cashes = []
    for observable_cache in observable_caches:
        observed_data = _get_observed_data(observable_cache)
        matches = matcher.match(indicator_v2_cache.pattern, [observed_data])
        if len(matches) != 0:
            indicator_v2_cache.type = observable_cache.type
            indicator_v2_cache.value = observable_cache.value
            indicator_v2_cache.cache_list = cache_list
            ret_observable_cashes.append(observable_cache)
    return ret_observable_cashes


def _get_similar_ipv4(package_id):
    CACHE_TYPE = 'ipv4'
    cashes = ObservableCaches.objects.filter(
        package_id=package_id,
        type=CACHE_TYPE)
    r = []
    for cache in cashes:
        octets = cache.value.split('.')
        ipv4_1_3 = '.'.join(octets[0:3]) + '.'
        ipv4_4 = int(octets[3])
        similar_ipv4_observable_caches = ObservableCaches.objects.filter(
            Q(type__exact=CACHE_TYPE)
            & Q(ipv4_1_3__exact=ipv4_1_3)
            & Q(ipv4_4__ne=ipv4_4)
            & Q(package_id__ne=package_id)
        )
        for info in similar_ipv4_observable_caches:
            v = {
                'source_value': cache.value,
                'cache': info}
            r.append(v)
    return r


def _get_similar_domain(package_id):
    CACHE_TYPE = 'domain_name'
    rs_system = System.objects.get()
    tld = TLD(rs_system.public_suffix_list_file_path)
    cashes = ObservableCaches.objects.filter(
        package_id=package_id,
        type=CACHE_TYPE)
    r = []
    for start_cache in cashes:
        without_tld, domain_tld = tld.split_domain(start_cache.value)
        if domain_tld is None:
            continue
        domain_last = without_tld.split('.')[-1]
        similar_domain_observable_caches = ObservableCaches.objects.filter(
            Q(type__exact=CACHE_TYPE)
            & Q(domain_tld=domain_tld)
            & Q(domain_last=domain_last)
            & Q(package_id__ne=package_id)
        )
        for end_cache in similar_domain_observable_caches:
            edge_type = _get_domain_similarity_type(start_cache, end_cache)
            if edge_type is not None:
                v = {
                    'source_value': start_cache.value,
                    'cache': end_cache
                }
                r.append(v)
    return r


def _get_domain_similarity_type(start_cache, end_cache):
    try:
        score_cache = SimilarScoreCache.objects.get(
            Q(type=SimilarScoreCache.DOMAIN_SCORE_CACHE_TYPE)
            & Q(start_cache=start_cache)
            & Q(end_cache=end_cache)
        )
        return score_cache.edge_type
    except DoesNotExist:
        pass

    start_without_tld_list = list(reversed(start_cache.domain_without_tld.split('.')))
    end_without_tld_list = list(reversed(end_cache.domain_without_tld.split('.')))
    min_length = min(len(start_without_tld_list), len(end_without_tld_list))
    max_length = max(len(start_without_tld_list), len(end_without_tld_list))

    same_count = 0
    for index in range(min_length):
        if start_without_tld_list[index] == end_without_tld_list[index]:
            same_count += 1
        else:
            break
    score = float(same_count) / float(max_length)
    edge_type = None
    if score == 0:
        edge_type = None
    elif score <= 0.125:
        edge_type = SIMILARTY_8_EDGE_TYPE
    elif score <= 0.25:
        edge_type = SIMILARTY_7_EDGE_TYPE
    elif score <= 0.375:
        edge_type = SIMILARTY_6_EDGE_TYPE
    elif score <= 0.5:
        edge_type = SIMILARTY_5_EDGE_TYPE
    elif score <= 0.625:
        edge_type = SIMILARTY_4_EDGE_TYPE
    elif score <= 0.75:
        edge_type = SIMILARTY_3_EDGE_TYPE
    elif score <= 0.875:
        edge_type = SIMILARTY_2_EDGE_TYPE
    elif score < 1.0:
        edge_type = SIMILARTY_1_EDGE_TYPE
    elif score == 1.0:
        edge_type = None

    SimilarScoreCache.create(SimilarScoreCache.DOMAIN_SCORE_CACHE_TYPE, start_cache, end_cache, edge_type)
    return edge_type


def _get_ipv4_similarity_type(start_cache, end_cache):
    try:
        score_cache = SimilarScoreCache.objects.get(
            Q(type=SimilarScoreCache.IPV4_SCORE_CACHE_TYPE)
            & Q(start_cache=start_cache)
            & Q(end_cache=end_cache)
        )
        return score_cache.edge_type
    except DoesNotExist:
        pass
    delta = abs(start_cache.ipv4_4 - end_cache.ipv4_4)
    edge_type = ''
    if delta <= 2**1:
        edge_type = SIMILARTY_1_EDGE_TYPE
    elif delta <= 2**2:
        edge_type = SIMILARTY_2_EDGE_TYPE
    elif delta <= 2**3:
        edge_type = SIMILARTY_3_EDGE_TYPE
    elif delta <= 2**4:
        edge_type = SIMILARTY_4_EDGE_TYPE
    elif delta <= 2**5:
        edge_type = SIMILARTY_5_EDGE_TYPE
    elif delta <= 2**6:
        edge_type = SIMILARTY_6_EDGE_TYPE
    elif delta <= 2**7:
        edge_type = SIMILARTY_7_EDGE_TYPE
    else:
        edge_type = SIMILARTY_8_EDGE_TYPE
    SimilarScoreCache.create(SimilarScoreCache.IPV4_SCORE_CACHE_TYPE, start_cache, end_cache, edge_type)
    return edge_type


def _get_ip_4th_value(ipv4):
    return int(ipv4.split('.')[3])


def _get_fuzzy_matched_info(package_id):
    fuzzy_matched_list = []
    matching_patterns = MatchingCustomizer.get_instance().get_matching_patterns()
    custom_objects = StixCustomizer.get_instance().get_custom_objects()

    for target in StixCustomObjects.objects.filter(package_id=package_id):
        fuzzy_matched_list = _fuzzy_match(target, package_id, matching_patterns, custom_objects, fuzzy_matched_list)
    return fuzzy_matched_list


def _fuzzy_match(target, package_id, matching_patterns, custom_objects, fuzzy_matched_list):
    for matching_pattern in matching_patterns:
        try:
            target_cache_type = matching_pattern['targets'][0]
            target_cache = CustomObjectCaches.objects.get(type=target_cache_type, package_id=package_id)
            another_cache_type = matching_pattern['targets'][1]
            target_value = target.object_[target_cache_type.split(':')[1]]
            fm_rule = _get_fuzzy_matching_rule(custom_objects, target_cache_type)
        except DoesNotExist:
            try:
                target_cache_type = matching_pattern['targets'][1]
                target_cache = CustomObjectCaches.objects.get(type=target_cache_type, package_id=package_id)
                another_cache_type = matching_pattern['targets'][0]
                target_value = target.object_[target_cache_type.split(':')[1]]
                fm_rule = _get_fuzzy_matching_rule(custom_objects, target_cache_type)
            except DoesNotExist:
                continue

        if type(target_value) != str:
            continue

        another_caches = CustomObjectCaches.objects.filter(
            type__in=[target_cache_type, another_cache_type],
            package_id__ne=package_id)

        for another_cache in another_caches:
            another_target_value = another_cache.value
            if type(another_target_value) != str:
                continue
            if not fm_rule.get('list_matching', False):
                continue
            matching_lists = fm_rule.get('lists', [])
            if len(matching_lists) == 0:
                continue

            fmi = None
            for matching_list in matching_lists:
                if target_value not in matching_list:
                    continue
                if another_target_value not in matching_list:
                    continue
                fmi = _create_fuzzy_match_info(target_cache, another_cache, fm_rule, target_value, another_target_value)
            if fmi:
                fuzzy_matched_list.append(fmi)
                continue

            normalize_target_value = _get_normalized_value(target_value, fm_rule)
            normalize_another_target_value = _get_normalized_value(another_target_value, fm_rule)
            if normalize_target_value == normalize_another_target_value:
                fuzzy_matched_list.append(_create_fuzzy_match_info(target_cache, another_cache, fm_rule, target_value, another_target_value))
    return fuzzy_matched_list


class FuzzyMatchInfo(object):
    def __init__(self):
        self.reason = {}
        self.start_node = {}
        self.end_node = {}


def _create_fuzzy_match_info(target_cache, another_cache, fm_rule, target_value, another_target_value):
    fmi = FuzzyMatchInfo()
    fmi.start_node = {
        'package_id': target_cache.package_id,
        'node_id': target_cache.node_id,
    }
    fmi.end_node = {
        'package_id': another_cache.package_id,
        'node_id': another_cache.node_id,
    }
    fmi.reason = {
        'title': 'Fuzzy Matching',
        'rule': fm_rule,
        'val_1': target_value,
        'val_2': another_target_value
    }
    return fmi


def _normalize2zen(v):
    return jaconv.h2z(v, kana=True, digit=True, ascii=True)


def _normalize2kun(v):
    list_ = kakasi.convert(v)
    v = ''
    for item in list_:
        v += item['kunrei']
    return v


def _get_normalized_value(target_value, rule):
    v = target_value
    if rule.get('match_zen_han', False):
        v = _normalize2zen(v)
    if rule.get('match_kata_hira', False):
        v = jaconv.kata2hira(v)
    if rule.get('match_eng_jpn', False):
        v = _normalize2kun(v)
    if rule.get('case_insensitive', False):
        v = v.lower()
    return v
 

def _get_fuzzy_matching_rule(custom_objects, target_cache_type):
    object_name, property_name = target_cache_type.split(':')
    custom_objects = StixCustomizer.get_instance().get_custom_objects()
    for custom_object in custom_objects:
        if custom_object['name'] == object_name:
            for prop in custom_object['properties']:
                if prop['name'] == property_name:
                    return prop['fuzzy_matching']
    return None


def get_matched_packages(package_id, exact=True, similar_ipv4=False, similar_domain=False):
    exact_dict = {}
    similar_ipv4_dict = {}
    similar_domain_dict = {}
    fuzzy_dict = {}
    package_id_list = []

    if exact:
        infos = _get_exact_matched_info(package_id)
        for info in infos:
            key = info.package_id
            package_id_list.append(key)
            if key not in exact_dict:
                exact_dict[key] = 1
            else:
                exact_dict[key] += 1

    if similar_ipv4:
        infos = _get_similar_ipv4(package_id)
        for info in infos:
            cache = info['cache']
            key = cache.package_id
            package_id_list.append(key)
            if key not in similar_ipv4_dict:
                similar_ipv4_dict[key] = 1
            else:
                similar_ipv4_dict[key] += 1

    if similar_domain:
        infos = _get_similar_domain(package_id)
        for info in infos:
            cache = info['cache']
            key = cache.package_id
            package_id_list.append(key)
            if key not in similar_domain_dict:
                similar_domain_dict[key] = 1
            else:
                similar_domain_dict[key] += 1

    infos = _get_fuzzy_matched_info(package_id)
    for info in infos:
        key = info.end_node['package_id']
        package_id_list.append(key)
        if key not in fuzzy_dict:
            fuzzy_dict[key] = 1
        else:
            fuzzy_dict[key] += 1

    package_id_set = list(set(package_id_list))

    ret = []
    for p_id in package_id_set:
        d = {}
        d['package_id'] = p_id
        d['package_name'] = StixFiles.objects.get(package_id=p_id).package_name
        if exact:
            d['exact'] = 0 if (p_id in exact_dict) is False else exact_dict[p_id]
        if ((similar_ipv4) or (similar_domain)):
            s_dict = {
                'ipv4': 0 if (p_id in similar_ipv4_dict) is False else similar_ipv4_dict[p_id],
                'domain': 0 if (p_id in similar_domain_dict) is False else similar_domain_dict[p_id]}
            d['similar'] = s_dict
        d['fuzzy'] = 0 if (p_id in fuzzy_dict) is False else fuzzy_dict[p_id]
        ret.append(d)
    return ret


# GET /api/v1/gv/matched_packages
@api_key_auth
def matched_packages(request):
    PACKAGE_ID_KEY = 'package_id'
    EXACT_KEY = 'exact'
    SIMILAR_IPV4_KEY = 'similar_ipv4'
    SIMILAR_DOMAIN_KEY = 'similar_domain'
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        package_id = request.GET[PACKAGE_ID_KEY]
        exact = get_boolean_value(request.GET, EXACT_KEY, True)
        similar_ipv4 = get_boolean_value(request.GET, SIMILAR_IPV4_KEY, False)
        similar_domain = get_boolean_value(request.GET, SIMILAR_DOMAIN_KEY, False)

        ret = get_matched_packages(package_id, exact=exact, similar_ipv4=similar_ipv4, similar_domain=similar_domain)
        resp = get_normal_response_json()
        resp['data'] = ret
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/contents_and_edges
@csrf_exempt
@api_key_auth
def contents_and_edges(request):
    PACKAGE_ID_KEY = 'package_id'
    COMPARED_PACKAGE_IDS_KEY = 'compared_package_ids'
    EXACT_KEY = 'exact'
    SIMILAR_IPV4_KEY = 'similar_ipv4'
    SIMILAR_DOMAIN_KEY = 'similar_domain'
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        package_id = request.GET[PACKAGE_ID_KEY]
        compared_package_ids = request.GET.getlist(COMPARED_PACKAGE_IDS_KEY)
        exact = get_boolean_value(request.GET, EXACT_KEY, True)
        similar_ipv4 = get_boolean_value(request.GET, SIMILAR_IPV4_KEY, False)
        similar_domain = get_boolean_value(request.GET, SIMILAR_DOMAIN_KEY, False)

        edges = []

        fuzzy_infos = _get_fuzzy_matched_info(package_id)
        for fuzzy_info in fuzzy_infos:
            if fuzzy_info.end_node['package_id'] not in compared_package_ids:
                continue
            start_node = fuzzy_info.start_node
            end_node = fuzzy_info.end_node
            edge = {
                'edge_type': fuzzy_info.reason['title'],
                'start_node': start_node,
                'end_node': end_node,
                'reason': fuzzy_info.reason,
            }
            edges.append(edge)

        if exact:
            end_infos = _get_exact_matched_info(package_id)
            for end_info in end_infos:
                if end_info.package_id not in compared_package_ids:
                    continue
                end_node = {
                    'package_id': end_info.package_id,
                    'node_id': end_info.node_id
                }

                if hasattr(end_info, 'start_collection'):
                    collection = end_info.start_collection
                else:
                    collection = type(end_info)
                if collection == IndicatorV2Caches:
                    start_caches = collection.objects.filter(
                        package_id=package_id,
                        pattern=end_info.pattern)
                elif collection == LabelCaches:
                    start_caches = collection.objects.filter(
                        package_id=package_id,
                        label__iexact=end_info.label)
                elif collection == CustomObjectCaches:
                    if hasattr(end_info, 'start_type'):
                        start_type = end_info.start_type
                    else:
                        start_type = end_info.type
                    start_caches = collection.objects.filter(
                        package_id=package_id,
                        type=start_type,
                        value=end_info.value)
                else:
                    start_caches = collection.objects.filter(
                        package_id=package_id,
                        type=end_info.type,
                        value=end_info.value)
                for start_cache in start_caches:
                    start_node = {
                        'package_id': package_id,
                        'node_id': start_cache.node_id
                    }
                    edge = {
                        'edge_type': EXACT_EDGE_TYPE,
                        'start_node': start_node,
                        'end_node': end_node
                    }
                    edges.append(edge)

        if similar_ipv4:
            end_infos = _get_similar_ipv4(package_id)
            for end_info in end_infos:
                end_cache = end_info['cache']
                if end_cache.package_id not in compared_package_ids:
                    continue
                end_node = {
                    'package_id': end_cache.package_id,
                    'node_id': end_cache.node_id
                }
                source_value = end_info['source_value']
                start_caches = ObservableCaches.objects.filter(
                    package_id=package_id,
                    type=end_cache.type,
                    value=source_value)
                for start_cache in start_caches:
                    start_node = {
                        'package_id': package_id,
                        'node_id': start_cache.node_id
                    }
                    edge_type = _get_ipv4_similarity_type(start_cache, end_cache)
                    edge = {
                        'edge_type': edge_type,
                        'start_node': start_node,
                        'end_node': end_node
                    }
                    edges.append(edge)

        if similar_domain:
            end_infos = _get_similar_domain(package_id)
            for end_info in end_infos:
                end_cache = end_info['cache']
                if end_cache.package_id not in compared_package_ids:
                    continue
                end_node = {
                    'package_id': end_cache.package_id,
                    'node_id': end_cache.node_id
                }
                source_value = end_info['source_value']
                start_caches = ObservableCaches.objects.filter(
                    package_id=package_id,
                    type=end_cache.type,
                    value=source_value)
                for start_cache in start_caches:
                    edge_type = _get_domain_similarity_type(start_cache, end_cache)
                    if edge_type is None:
                        continue
                    start_node = {
                        'package_id': package_id,
                        'node_id': start_cache.node_id
                    }
                    edge = {
                        'edge_type': edge_type,
                        'start_node': start_node,
                        'end_node': end_node
                    }
                    edges.append(edge)

        contents = []
        contents.append(_get_contents_item(package_id))
        for compared_package_id in compared_package_ids:
            contents.append(_get_contents_item(compared_package_id))

        data = {}
        data['contents'] = contents
        data['edges'] = edges

        resp = get_normal_response_json()
        resp['data'] = data
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/package_list_for_sharing_table
@api_key_auth
def package_list_for_sharing_table(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        iDisplayLength = int(request.GET['iDisplayLength'])
        iDisplayStart = int(request.GET['iDisplayStart'])
        sSearch = request.GET['sSearch']
        sort_col = int(request.GET['iSortCol'])
        sort_dir = request.GET['sSortDir']

        order_query = None
        SORT_INDEX_PACKAGE_NAME = 3

        if sort_col == SORT_INDEX_PACKAGE_NAME:
            order_query = 'package_name'

        if order_query is not None:
            if sort_dir == 'desc':
                order_query = '-' + order_query

        community_objects = Communities.objects.filter(name__icontains=sSearch)
        objects = StixFiles.objects.filter(
            Q(package_name__icontains=sSearch)
            | Q(input_community__in=community_objects)) \
            .order_by(order_query)
        objects = objects.filter(Q(is_post_sns__ne=False))

        data = []
        for d in objects[iDisplayStart:(iDisplayStart + iDisplayLength)]:
            r = {}
            r['comment'] = d.comment
            r['package_name'] = d.package_name
            r['package_id'] = d.package_id
            r['version'] = d.version
            try:
                r['input_community'] = d.input_community.name
            except BaseException:
                r['input_community'] = ''
            data.append(r)

        r_data = {}
        r_data['iTotalRecords'] = StixFiles.objects.count()
        r_data['iTotalDisplayRecords'] = objects.count()
        r_data['data'] = data
        resp = get_normal_response_json()
        resp['data'] = r_data
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)

# /api/v1/stix_files
@csrf_exempt
@api_key_auth
def stix_files_id(request, package_id):
    try:
        if request.method == 'GET':
            return get_stix_files_id(request, package_id)
        elif request.method == 'DELETE':
            return delete_stix_files_id(request, package_id)
        else:
            return HttpResponseNotAllowed(['GET', 'DELETE'])
    except Exception as e:
        return error(e)


# GET /api/v1/gv/stix_file/<package_id>
def get_stix_files_id(request, package_id):
    try:
        stix_file = StixFiles.objects.get(package_id=package_id)
        resp = get_normal_response_json()
        resp['data'] = stix_file.to_dict()
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# DELETE /api/v1/gv/stix_file/<package_id>
def delete_stix_files_id(request, package_id):
    try:
        origin_path = StixFiles.delete_by_package_id(package_id)
        if os.path.exists(origin_path):
            os.remove(origin_path)
        return JsonResponse({}, status=204)
    except Exception as e:
        traceback.print_exc()
        return error(e)

# PUT /api/v1/gv/stix_file/<package_id>/comment
@csrf_exempt
@api_key_auth
def stix_file_comment(request, package_id):
    try:
        if request.method != 'PUT':
            return HttpResponseNotAllowed(['PUT'])
        if 'comment' not in request.GET:
            return error(Exception('No input comment.'))
        comment = request.GET['comment']
        stix_file = StixFiles.objects.get(package_id=package_id)
        stix_file.comment = comment
        stix_file.save()
        return JsonResponse({}, status=204)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/stix_file/<package_id>/l1_info
@api_key_auth
def stix_file_l1_info(request, package_id):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        caches = ObservableCaches.objects.filter(package_id=package_id)
        data = []
        for cache in caches:
            r = {
                'type': cache.type,
                'value': cache.value,
                'observable_id': cache.observable_id,
            }
            data.append(r)
        resp = get_normal_response_json()
        resp['data'] = data
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/stix_file/<package_id>/stix
@api_key_auth
def stix_file_stix(request, package_id):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        resp = get_normal_response_json()
        stix_file = StixFiles.objects.get(package_id=package_id)
        resp['data'] = _get_stix_content_dict(stix_file)
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/communities
@api_key_auth
def communities(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        resp = get_normal_response_json()
        resp['data'] = []
        for community in Communities.objects.all():
            resp['data'].append(community.to_dict())
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/count_by_type
@api_key_auth
def count_by_type(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        ret_types = [
            ('Packages', StixFiles.objects.count()),
            ('Campaigns', StixCampaigns.objects.count()),
            ('Incidents', StixIncidents.objects.count()),
            ('Indicators', StixIndicators.objects.count()),
            ('Observables', StixObservables.objects.count()),
            ('Threat Actors', StixThreatActors.objects.count()),
            ('Exploit Targets', StixExploitTargets.objects.count()),
            ('Courses Of Action', StixCoursesOfAction.objects.count()),
            ('TTPs', StixTTPs.objects.count()),
        ]
        resp = get_normal_response_json()
        resp['data'] = []
        for ret_type in ret_types:
            type_, count_ = ret_type
            d = {
                'type': type_,
                'count': count_
            }
            resp['data'].append(d)
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/latest_package_list
@api_key_auth
def latest_package_list(request):
    DEFAULT_LATEST_NUM = 10
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        try:
            num = int(request.GET['num'])
        except BaseException:
            num = DEFAULT_LATEST_NUM

        resp = get_normal_response_json()
        resp['data'] = []
        for stix_file in StixFiles.objects.order_by('-produced')[:num]:
            resp['data'] .append(stix_file.get_rest_api_document_info())
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


def count_by_community(community, latest_days):
    if latest_days == -1:
        oldest_stix_file = StixFiles.objects.order_by('produced').limit(1)[0]
        delta = datetime.datetime.now() - oldest_stix_file.produced
        latest_days = (delta.days) + 2

    today = datetime.datetime.now(pytz.utc)
    past_day = _get_past_day(today, latest_days - 1)
    objects = StixFiles.objects.filter(
        Q(input_community=community)
        & Q(produced__gte=past_day))

    date_count = {}
    for item in objects:
        date_string = item.produced.strftime('%Y-%m-%d')
        if (date_string in date_count):
            date_count[date_string] += 1
        else:
            date_count[date_string] = 1

    ret = []
    for i in range(latest_days):
        past_day = _get_past_day(today, i)
        date_string = past_day.strftime('%Y-%m-%d')
        if (date_string in date_count):
            num = date_count[date_string]
        else:
            num = 0
        count = {
            'date': date_string,
            'num': num,
        }
        ret.append(count)
    return ret


def _get_past_day(today, delta_int):
    past_delta = datetime.timedelta(days=delta_int)
    past_day = today - past_delta
    past_day = datetime.datetime(past_day.year, past_day.month, past_day.day)
    return past_day


# GET /api/v1/gv/latest_stix_count_by_community
@api_key_auth
def latest_stix_count_by_community(request):
    LASTEST_DAYS_KEY = 'latest_days'
    DEFAULT_LATEST_DAYS = 7
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        try:
            latest_days = int(request.GET[LASTEST_DAYS_KEY])
        except BaseException:
            latest_days = DEFAULT_LATEST_DAYS
        resp = get_normal_response_json()
        resp['data'] = []
        for community in Communities.objects.all():
            count = count_by_community(community, latest_days)
            d = {
                'community': community.name,
                'count': count
            }
            resp['data'].append(d)
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/language_contents
@api_key_auth
def language_contents(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        object_ref = request.GET['object_ref']
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


def _get_stix_content_dict(stix_file):
    if stix_file.version.startswith('2.'):
        return json.loads(stix_file.content.read())
    else:
        stix_package = STIXPackage.from_xml(stix_file.origin_path)
        return stix_package.to_dict()


def _get_contents_item(package_id):
    stix_file = StixFiles.objects.get(package_id=package_id)
    return {
        'package_id': package_id,
        'package_name': stix_file.package_name,
        'version': stix_file.version,
        'dict': _get_stix_content_dict(stix_file)
    }
