import os
import json
import traceback
import datetime
import pytz
import re
from stix2matcher import matcher
from stix.core.stix_package import STIXPackage
from mongoengine.queryset.visitor import Q
from django.http import HttpResponseNotAllowed
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ctirs.api import error, authentication, get_normal_response_json
from ctirs.core.mongo.documents import Communities
from ctirs.core.mongo.documents_stix import ObservableCaches, SimilarScoreCache, StixFiles, \
    StixCampaigns, StixIncidents, StixIndicators, StixObservables, StixThreatActors, \
    StixExploitTargets, StixCoursesOfAction, StixTTPs, ExploitTargetCaches, \
    IndicatorV2Caches, StixLanguageContents, LabelCaches
from stip.common.tld import TLD
from mongoengine import DoesNotExist
from .stix2_indicator import _get_observed_data
from ctirs.models.rs.models import System

# EDGE 文字列
EXACT_EDGE_TYPE = 'Exact'
SIMILARTY_1_EDGE_TYPE = 'Similarity: 1'
SIMILARTY_2_EDGE_TYPE = 'Similarity: 2'
SIMILARTY_3_EDGE_TYPE = 'Similarity: 3'
SIMILARTY_4_EDGE_TYPE = 'Similarity: 4'
SIMILARTY_5_EDGE_TYPE = 'Similarity: 5'
SIMILARTY_6_EDGE_TYPE = 'Similarity: 6'
SIMILARTY_7_EDGE_TYPE = 'Similarity: 7'
SIMILARTY_8_EDGE_TYPE = 'Similarity: 8'


# 共通
# REST API から boolean の値を取得する
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
# L1用 table 返却
def l1_info_for_l1table(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        # ajax parameter取得
        # 表示する長さ
        iDisplayLength = int(request.GET['iDisplayLength'])
        # 表示開始位置インデックス
        iDisplayStart = int(request.GET['iDisplayStart'])
        # 検索文字列
        sSearch = request.GET['sSearch']
        # ソートする列
        sort_col = int(request.GET['iSortCol'])
        # ソート順番 (desc指定で降順)
        sort_dir = request.GET['sSortDir']
        # alias情報
        # 存在しない場合は空としてあつかつ
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

        # type
        if sort_col == SORT_INDEX_TYPE:
            order_query = 'type'
        # value
        elif sort_col == SORT_INDEX_VALUE:
            order_query = 'value'
        # pacakge_name
        elif sort_col == SORT_INDEX_PACKAGE_NAME:
            order_query = 'package_name'
        # title
        elif sort_col == SORT_INDEX_TILE:
            order_query = 'title'
        # description
        elif sort_col == SORT_INDEX_DESCRIPTION:
            order_query = 'description'
        # timestamp
        elif sort_col == SORT_INDEX_TIMESTAMP:
            order_query = 'produced'

        # 昇順/降順
        if order_query is not None:
            # descが降順
            if sort_dir == 'desc':
                order_query = '-' + order_query

        # query
        # 検索ワードをリスト化
        tmp_sSearches = list(set(sSearch.split(' ')))
        # 空要素は取り除く
        if '' in tmp_sSearches:
            tmp_sSearches.remove('')

        # 検索リスト作成
        sSearches = []
        for item in tmp_sSearches:
            # まず、元の単語は追加する
            sSearches.append(item)
            # alias_lists 1つずつチェックする
            for alias_list in alias_lists:
                # 検索ワードがalias_listにあれば、そのリストに含まれるすべての単語が検索対象
                if item in alias_list:
                    sSearches.extend(alias_list)

        # 重複を省く
        sSearches = list(set(sSearches))

        # Filterを作成する
        filters = Q()
        # alias含め、その文字列が含まれていたらヒットとする
        for sSearch in sSearches:
            filters = filters | Q(type__icontains=sSearch)
            filters = filters | Q(value__icontains=sSearch)
            filters = filters | Q(package_name__icontains=sSearch)
            filters = filters | Q(title__icontains=sSearch)
            filters = filters | Q(description__icontains=sSearch)
        # 検索
        objects = ObservableCaches.objects.filter(filters).order_by(order_query)

        # 検索結果から表示範囲のデータを抽出する
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

        # response data 作成
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
def package_list(request):
    REQUIRED_COMMENT_KEY = 'required_comment'
    LIMIT_KEY = 'limit'
    ORDER_BY_KEY = 'order_by'
    DEFAULT_ORDER_BY = 'package_name'
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))

        required_comment = False
        if (REQUIRED_COMMENT_KEY in request.GET):
            if request.GET[REQUIRED_COMMENT_KEY].lower() == 'true':
                required_comment = True

        # 全取得
        stix_files = StixFiles.objects.filter()
        # order_by指定があればソートする
        # それ以外に場合はpackage_nameを辞書順でソートする
        if (ORDER_BY_KEY in request.GET):
            try:
                stix_files = stix_files.order_by(request.GET[ORDER_BY_KEY])
            except BaseException:
                stix_files = stix_files.order_by(DEFAULT_ORDER_BY)
        else:
            stix_files = stix_files.order_by(DEFAULT_ORDER_BY)

        # limit取得
        try:
            limit = int(request.GET[LIMIT_KEY])
        except BaseException:
            limit = None
        # 指定があれば上位の指定数だけを返却する
        if limit is not None:
            stix_files = stix_files[:limit]

        rsp_stix_files = []
        # 返却データ作成
        for stix_file in stix_files:
            rsp_stix_files.append(stix_file.get_rest_api_document_info(required_comment))
        resp = get_normal_response_json()
        resp['data'] = rsp_stix_files
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/package_name_list
def package_name_list(request):
    LIMIT_KEY = 'limit'
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))

        # 全取得
        stix_files = StixFiles.objects.filter(Q(is_post_sns__ne=False)).only('package_name', 'package_id').order_by('package_name')

        # limit取得
        try:
            limit = int(request.GET[LIMIT_KEY])
        except BaseException:
            limit = None
        # 指定があれば上位の指定数だけを返却する
        if limit is not None:
            stix_files = stix_files[:limit]

        rsp_stix_files = []
        # 返却データ作成
        for stix_file in stix_files:
            rsp_stix_files.append(stix_file.get_rest_api_package_name_info())
        resp = get_normal_response_json()
        resp['data'] = rsp_stix_files
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# exact matchした情報を取得する
def _get_exact_matched_info(package_id):
    ret_observable_cashes = []

    # match 検索対象の cache list
    cache_collections = [
        ObservableCaches,  # STIX 1.x/2.x の Observables
        ExploitTargetCaches,
    ]

    for cache_collection in cache_collections:
        caches = cache_collection.objects.filter(package_id=package_id)
        for cache in caches:
            # type,valueが一緒で、検索 package_idと異なる Cache を検索 (observables 間検索)
            # Obaservable の値がない場合はスキップする
            if cache.value is None:
                continue
            exacts = cache_collection.objects.filter(
                Q(type__exact=cache.type)
                & Q(value__exact=cache.value)
                & Q(package_id__ne=package_id))
            ret_observable_cashes.extend(exacts)

            # ObservableCaches の検索の場合はさらに その Observable が STIX v2 の indicator pattern 文字列にヒットするか判定する
            if isinstance(cache, ObservableCaches):
                # Observable と STIX 2.x の indicators 間
                indicator_v2_cachses = IndicatorV2Caches.objects.filter(Q(package_id__ne=package_id))
                for indicator_v2_cache in indicator_v2_cachses:
                    observed_data = _get_observed_data(cache)
                    matches = matcher.match(indicator_v2_cache.pattern, [observed_data])
                    if len(matches) != 0:
                        indicator_v2_cache.type = cache.type
                        indicator_v2_cache.value = cache.value
                        # start_node の検索先は ObservableCaches or ExploitTargetCaches
                        indicator_v2_cache.start_collection = cache_collection
                        # 格納する end_info は (指定の package_id) の ObservableCache に該当する IndicatorV2Cache
                        ret_observable_cashes.append(indicator_v2_cache)

    # STIX2 indicator cache の matching
    indicator_v2_caches = IndicatorV2Caches.objects.filter(package_id=package_id)
    for indicator_v2_cache in indicator_v2_caches:
        # 対象の IndicatorV2Caches に Match する (Package_id は別の) ObservableCaches を検索する
        query_set = _get_observables_cashes_query(indicator_v2_cache.pattern, package_id)
        caches = ObservableCaches.objects.filter(query_set)
        for cache in caches:
            observed_data = _get_observed_data(cache)
            matches = matcher.match(indicator_v2_cache.pattern, [observed_data])
            if len(matches) != 0:
                # start_info は IndicatorV2Caches から検索
                cache.start_collection = IndicatorV2Caches
                cache.pattern = indicator_v2_cache.pattern
                # 格納する end_info は (指定の package_id) の Indicator v2 にマッチする ObservableCache
                ret_observable_cashes.append(cache)

        # 自分以外の PackageID で STIX2 indicator pattern を検索する
        exacts = IndicatorV2Caches.objects.filter(
            Q(pattern__exact=indicator_v2_cache.pattern)
            & Q(package_id__ne=package_id))
        for exact in exacts:
            exact.cache_list = IndicatorV2Caches
            # start_node の検索先は ObservableCaches or ExploitTargetCaches
            exact.start_collection = IndicatorV2Caches
            # 格納するのは (指定の package_id) の Indicator v2 にマッチする (指定の package_id 以外に)IndicatorV2Cache
            ret_observable_cashes.append(exact)

    label_caches = LabelCaches.objects.filter(package_id=package_id)
    for label_cache in label_caches:
        exacts = LabelCaches.objects.filter(
            Q(label__iexact=label_cache.label)
            & Q(package_id__ne=package_id))
        for exact in exacts:
            ret_observable_cashes.append(exact)
    return ret_observable_cashes


# pattern 文字列から ObservableCaches を絞り込む Query インスタンスを取得する
url_pattern = re.compile(r'url:value\s*=\s*\'(\S+)\'')
ipv4_pattern = re.compile(r'ipv4-addr:value\s*=\s*\'(\S+)\'')
domain_name_pattern = re.compile(r'domain-name:value\s*=\s*\'(\S+)\'')
md5_pattern = re.compile(r'file:hashes\.\'MD5\'\s*=\s*\'(\S+)\'')
sha1_pattern = re.compile(r'file:hashes\.\'SHA-1\'\s*=\s*\'(\S+)\'')
sha256_pattern = re.compile(r'file:hashes\.\'SHA-256\'\s*=\s*\'(\S+)\'')
sha512_pattern = re.compile(r'file:hashes\.\'SHA-512\'\s*=\s*\'(\S+)\'')


def _get_observables_cashes_query(pattern, package_id):
    q = Q()
    # pattern 文字列から種別と値を正規表現で抽出し、 OR 検索で連結する
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


# IPv4 の類似結果情報を取得する
def _get_similar_ipv4(package_id):
    CACHE_TYPE = 'ipv4'
    # 指定の package_id で ipv4 のものを取得する
    cashes = ObservableCaches.objects.filter(
        package_id=package_id,
        type=CACHE_TYPE)
    r = []
    for cache in cashes:
        octets = cache.value.split('.')
        ipv4_1_3 = '.'.join(octets[0:3]) + '.'
        ipv4_4 = int(octets[3])
        # ipv4 で 第3オクテットまで同一で,第4オクテットが異なり
        # 検索 package_idと異なる Observable Cache を検索
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


# domain の類似結果情報を取得する
def _get_similar_domain(package_id):
    CACHE_TYPE = 'domain_name'
    rs_system = System.objects.get()
    tld = TLD(rs_system.public_suffix_list_file_path)
    # 指定の package_id で domain_name のものを取得する
    cashes = ObservableCaches.objects.filter(
        package_id=package_id,
        type=CACHE_TYPE)
    r = []
    for start_cache in cashes:
        without_tld, domain_tld = tld.split_domain(start_cache.value)
        # tld がない domain 名は similar 対象外
        if domain_tld is None:
            continue
        domain_last = without_tld.split('.')[-1]
        # domain_name で TLD が同じで
        # かつ、 TLD の直前のサーバー名(domain_last)が同じ
        # 検索 package_idと異なる Observable Cache を検索
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


# domain の 類似度を判定する
# すでにtypeがdomainであること、tldが一致していることが前提
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

    # .区切りで抽出し、reverseする
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

    # cache 作成
    SimilarScoreCache.create(SimilarScoreCache.DOMAIN_SCORE_CACHE_TYPE, start_cache, end_cache, edge_type)
    return edge_type


# IPv4 の 類似度を判定する
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
    # 第4オクテットの差分の絶対値で判別
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
    # cache 作成
    SimilarScoreCache.create(SimilarScoreCache.IPV4_SCORE_CACHE_TYPE, start_cache, end_cache, edge_type)
    return edge_type


# 指定された IPv4 文字列の第4オクテットの数値を取得する
def _get_ip_4th_value(ipv4):
    return int(ipv4.split('.')[3])


# 関連 CTI 検索 (GV/API 経由共通)
def get_matched_packages(package_id, exact=True, similar_ipv4=False, similar_domain=False):
    exact_dict = {}
    similar_ipv4_dict = {}
    similar_domain_dict = {}
    package_id_list = []

    # exact match情報取得
    if exact:
        infos = _get_exact_matched_info(package_id)
        for info in infos:
            key = info.package_id
            package_id_list.append(key)
            if key not in exact_dict:
                exact_dict[key] = 1
            else:
                exact_dict[key] += 1

    # IPv4 類似度情報取得
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

    # domain 類似度情報取得
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

    # 返却データ作成
    # package_id の set を作成(重複を省くため)
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
        ret.append(d)
    return ret


# GET /api/v1/gv/matched_packages
def matched_packages(request):
    PACKAGE_ID_KEY = 'package_id'
    EXACT_KEY = 'exact'
    SIMILAR_IPV4_KEY = 'similar_ipv4'
    SIMILAR_DOMAIN_KEY = 'similar_domain'
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))

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
def contents_and_edges(request):
    PACKAGE_ID_KEY = 'package_id'
    COMPARED_PACKAGE_IDS_KEY = 'compared_package_ids'
    EXACT_KEY = 'exact'
    SIMILAR_IPV4_KEY = 'similar_ipv4'
    SIMILAR_DOMAIN_KEY = 'similar_domain'
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))

        package_id = request.GET[PACKAGE_ID_KEY]
        compared_package_ids = request.GET.getlist(COMPARED_PACKAGE_IDS_KEY)
        exact = get_boolean_value(request.GET, EXACT_KEY, True)
        similar_ipv4 = get_boolean_value(request.GET, SIMILAR_IPV4_KEY, False)
        similar_domain = get_boolean_value(request.GET, SIMILAR_DOMAIN_KEY, False)

        edges = []
        if exact:
            # exact match情報取得
            # end_infos には compared_package_ids候補が格納される
            end_infos = _get_exact_matched_info(package_id)
            for end_info in end_infos:
                # compared_package_ids に含まれていない package_id はskip
                if end_info.package_id not in compared_package_ids:
                    continue
                # 終点情報
                end_node = {
                    'package_id': end_info.package_id,
                    'node_id': end_info.node_id
                }

                # 検索対象となるコレクションを取得
                if hasattr(end_info, 'start_collection'):
                    # start_collection 指定がある場合はそのコレクションから
                    collection = end_info.start_collection
                else:
                    # 指定がない場合は end_info と同じ
                    collection = type(end_info)
                # コレクションから終点情報に合致する始点を検索
                if collection == IndicatorV2Caches:
                    start_caches = collection.objects.filter(
                        package_id=package_id,
                        pattern=end_info.pattern)
                elif collection == LabelCaches:
                    start_caches = collection.objects.filter(
                        package_id=package_id,
                        label__iexact=end_info.label)
                else:
                    start_caches = collection.objects.filter(
                        package_id=package_id,
                        type=end_info.type,
                        value=end_info.value)
                # 開始位置情報と線情報を格納する
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
            # similar ipv4情報取得
            end_infos = _get_similar_ipv4(package_id)
            for end_info in end_infos:
                # compared_package_ids に含まれていない package_id はskip
                end_cache = end_info['cache']
                if end_cache.package_id not in compared_package_ids:
                    continue
                # 終点情報
                end_node = {
                    'package_id': end_cache.package_id,
                    'node_id': end_cache.node_id
                }
                # IPの値を取得
                source_value = end_info['source_value']
                # 終点情報に類似する始点を検索
                start_caches = ObservableCaches.objects.filter(
                    package_id=package_id,
                    type=end_cache.type,
                    value=source_value)
                for start_cache in start_caches:
                    # 始点情報
                    start_node = {
                        'package_id': package_id,
                        'node_id': start_cache.node_id
                    }
                    # IPv4 similarity計測
                    edge_type = _get_ipv4_similarity_type(start_cache, end_cache)
                    edge = {
                        'edge_type': edge_type,
                        'start_node': start_node,
                        'end_node': end_node
                    }
                    edges.append(edge)

        if similar_domain:
            # similar domain情報取得
            end_infos = _get_similar_domain(package_id)
            for end_info in end_infos:
                # compared_package_ids に含まれていない package_id はskip
                end_cache = end_info['cache']
                if end_cache.package_id not in compared_package_ids:
                    continue
                # 終点情報
                end_node = {
                    'package_id': end_cache.package_id,
                    'node_id': end_cache.node_id
                }
                # IPの値を取得
                source_value = end_info['source_value']
                # 終点情報に類似する始点を検索
                start_caches = ObservableCaches.objects.filter(
                    package_id=package_id,
                    type=end_cache.type,
                    value=source_value)
                for start_cache in start_caches:
                    edge_type = _get_domain_similarity_type(start_cache, end_cache)
                    if edge_type is None:
                        continue
                    # 始点情報
                    start_node = {
                        'package_id': package_id,
                        'node_id': start_cache.node_id
                    }
                    # domain domain計測
                    edge = {
                        'edge_type': edge_type,
                        'start_node': start_node,
                        'end_node': end_node
                    }
                    edges.append(edge)

        # contents作成
        contents = []
        # pacakge_id指定分
        contents.append(_get_contents_item(package_id))
        # compared_package_ids指定分
        for compared_package_id in compared_package_ids:
            contents.append(_get_contents_item(compared_package_id))

        # 返却データ作成
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
# sharing table (package)返却
def package_list_for_sharing_table(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        # ajax parameter取得
        # 表示する長さ
        iDisplayLength = int(request.GET['iDisplayLength'])
        # 表示開始位置インデックス
        iDisplayStart = int(request.GET['iDisplayStart'])
        # 検索文字列
        sSearch = request.GET['sSearch']
        # ソートする列
        sort_col = int(request.GET['iSortCol'])
        # ソート順番 (desc指定で降順)
        sort_dir = request.GET['sSortDir']

        order_query = None
        SORT_INDEX_PACKAGE_NAME = 3

        # pakcage_name
        if sort_col == SORT_INDEX_PACKAGE_NAME:
            order_query = 'package_name'

        # 昇順/降順
        if order_query is not None:
            # descが降順
            if sort_dir == 'desc':
                order_query = '-' + order_query

        # 検索対象のコミュニティリストを検索
        community_objects = Communities.objects.filter(name__icontains=sSearch)
        # 検索
        objects = StixFiles.objects.filter(
            Q(package_name__icontains=sSearch)
            | Q(input_community__in=community_objects)) \
            .order_by(order_query)
        objects = objects.filter(Q(is_post_sns__ne=False))

        # 検索結果から表示範囲のデータを抽出する
        data = []
        for d in objects[iDisplayStart:(iDisplayStart + iDisplayLength)]:
            r = {}
            r['comment'] = d.comment
            r['package_name'] = d.package_name
            r['package_id'] = d.package_id
            try:
                r['input_community'] = d.input_community.name
            except BaseException:
                r['input_community'] = ''
            data.append(r)

        # response data 作成
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
# GET/POSTの受付
@csrf_exempt
def stix_files_id(request, package_id):
    try:
        if request.method == 'GET':
            # stix_file一覧取得
            return get_stix_files_id(request, package_id)
        elif request.method == 'DELETE':
            # stix_file削除
            return delete_stix_files_id(request, package_id)
        else:
            return HttpResponseNotAllowed(['GET', 'DELETE'])
    except Exception as e:
        return error(e)


# GET /api/v1/gv/stix_file/<package_id>
# stix_file 返却
def get_stix_files_id(request, package_id):
    try:
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        # 検索
        stix_file = StixFiles.objects.get(package_id=package_id)
        # response data 作成
        resp = get_normal_response_json()
        resp['data'] = stix_file.to_dict()
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# DELETE /api/v1/gv/stix_file/<package_id>
# stix_file 削除
def delete_stix_files_id(request, package_id):
    try:
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        # mongoから該当レコード削除
        origin_path = StixFiles.delete_by_package_id(package_id)
        # ファイル削除
        if os.path.exists(origin_path):
            os.remove(origin_path)
        # response data 作成
        return JsonResponse({}, status=204)
    except Exception as e:
        traceback.print_exc()
        return error(e)

# PUT /api/v1/gv/stix_file/<package_id>/comment
# stix コメント変更
@csrf_exempt
def stix_file_comment(request, package_id):
    try:
        if request.method != 'PUT':
            return HttpResponseNotAllowed(['PUT'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        if 'comment' not in request.GET:
            return error(Exception('No input comment.'))
        comment = request.GET['comment']
        # 検索してコメント保存
        stix_file = StixFiles.objects.get(package_id=package_id)
        stix_file.comment = comment
        stix_file.save()
        return JsonResponse({}, status=204)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/stix_file/<package_id>/l1_info
# L1情報取得
def stix_file_l1_info(request, package_id):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))

        # 該当するキャッシュを検索する
        caches = ObservableCaches.objects.filter(package_id=package_id)
        # 返却データを作成する
        data = []
        for cache in caches:
            r = {
                'type': cache.type,
                'value': cache.value,
                'observable_id': cache.observable_id,
            }
            data.append(r)
        # response data 作成
        resp = get_normal_response_json()
        resp['data'] = data
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/stix_file/<package_id>/stix
# STIX content 作成
def stix_file_stix(request, package_id):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        resp = get_normal_response_json()
        stix_file = StixFiles.objects.get(package_id=package_id)
        resp['data'] = _get_stix_content_dict(stix_file)
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/communities
# STIX content 作成
def communities(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        resp = get_normal_response_json()
        resp['data'] = []
        for community in Communities.objects.all():
            resp['data'].append(community.to_dict())
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


# GET /api/v1/gv/count_by_type
# STIX content 作成
def count_by_type(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        # 返却データ作成
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
def latest_package_list(request):
    DEFAULT_LATEST_NUM = 10
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        try:
            num = int(request.GET['num'])
        except BaseException:
            num = DEFAULT_LATEST_NUM

        resp = get_normal_response_json()
        resp['data'] = []
        # producedを降順でソート
        for stix_file in StixFiles.objects.order_by('-produced')[:num]:
            resp['data'] .append(stix_file.get_rest_api_document_info())
        return JsonResponse(resp)
    except Exception as e:
        traceback.print_exc()
        return error(e)


def count_by_community(community, latest_days):
    # latest_days が -1 指定の場合(ALL 指定の場合)
    if latest_days == -1:
        # 最古の produced を取得し、現在までの差分を計算し latest_days とする
        oldest_stix_file = StixFiles.objects.order_by('produced').limit(1)[0]
        delta = datetime.datetime.now() - oldest_stix_file.produced
        # oldest_stix_fileが時間指定でカウントさせれるように時間差分追加
        latest_days = (delta.days) + 2

    # 指定のcommunityのlatest_daysまでの全 document 取得
    today = datetime.datetime.now(pytz.utc)
    past_day = _get_past_day(today, latest_days - 1)
    objects = StixFiles.objects.filter(
        Q(input_community=community)
        & Q(produced__gte=past_day))

    # 取得した document を日付ごとにカウント
    date_count = {}
    for item in objects:
        date_string = item.produced.strftime('%Y-%m-%d')
        if (date_string in date_count):
            date_count[date_string] += 1
        else:
            date_count[date_string] = 1

    # 返却データ作成
    ret = []
    for i in range(latest_days):
        # 1日おきの日付文字列を作成する
        past_day = _get_past_day(today, i)
        # 1日幅で指定のコミュニティの件数をカウントする
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


# 本日から指定の数日分のdatetime型(00:00:00固定)を返却
def _get_past_day(today, delta_int):
    past_delta = datetime.timedelta(days=delta_int)
    past_day = today - past_delta
    past_day = datetime.datetime(past_day.year, past_day.month, past_day.day)
    return past_day


# GET /api/v1/gv/latest_stix_count_by_community
# 1日ごとの各コミュニティーごとのファイル数を返却する
def latest_stix_count_by_community(request):
    LASTEST_DAYS_KEY = 'latest_days'
    DEFAULT_LATEST_DAYS = 7
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        # 最新何日からカウントするか取得する
        try:
            latest_days = int(request.GET[LASTEST_DAYS_KEY])
        except BaseException:
            latest_days = DEFAULT_LATEST_DAYS
        # 返却データ作成
        resp = get_normal_response_json()
        resp['data'] = []
        # communityごとにカウントする
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
def language_contents(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 認証する
        user = authentication(request)
        if user is None:
            return error(Exception('You have no permission for this operation.'))
        # 表示する長さ
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


# package_id指定のstix辞書形式を返却
def _get_stix_content_dict(stix_file):
    if stix_file.version.startswith('2.'):
        # STIX 2.x
        return json.loads(stix_file.content.read())
    else:
        # STIX 1.x
        stix_package = STIXPackage.from_xml(stix_file.origin_path)
        return stix_package.to_dict()


# contents_and_edgesで返却するpackage_idごとの辞書を作成する
def _get_contents_item(package_id):
    stix_file = StixFiles.objects.get(package_id=package_id)
    return {
        'package_id': package_id,
        'package_name': stix_file.package_name,
        'version': stix_file.version,
        'dict': _get_stix_content_dict(stix_file)
    }
