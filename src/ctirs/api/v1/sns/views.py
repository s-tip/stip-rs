import pytz
import datetime
import re
import string
from mongoengine.errors import DoesNotExist
from mongoengine.queryset.visitor import Q
from django.http import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse, HttpResponseNotFound
from ctirs.api import error
from ctirs.core.mongo.documents import Vias, MispAdapter
from ctirs.core.mongo.documents_stix import StixFiles, ObservableCaches
from ctirs.core.adapter.misp.upload.control import MispUploadAdapterControl
from stix.data_marking import MarkingSpecification
from stix.extensions.marking.simple_marking import SimpleMarkingStructure
import stip.common.const as const
import stip.common.tag as tag

DEFAULT_RETURN_FEEDS_NUM = 10
STIP_SNS_COMMENT_TITLE_PREFIX = 'Comment to '
STIP_SNS_LIKE_TITLE_PREFIX = 'Like to '
STIP_SNS_UNLIKE_TITLE_PREFIX = 'Unlike to '
STIP_SNS_TOOL_NAME_VALUE = 'S-TIP'
STIP_SNS_TOOL_VENDOR_VALUE = 'Fujitsu'
STIP_SNS_USER_NAME_PREFIX = 'User Name: '


# 共通
#     : 指定文字列は str(datetime) / 2018-02-22 08:54:47.187184 形式で GMT のタイムゾーン時間帯で送る
#     : +09:00 のようなtimezone付きは python 2.7 ではサポートしていないようなのでつけない
# 文字列からdatetime型を返却する
def get_datetime_from_str(s, default=None):
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.utc)
    except BaseException:
        return default


# GET /api/v1/sns/feeds
# start_time の 引数を返却
def get_feeds_start_time(request):
    # 引数1: start_time : この時間を最新として古い順に検索する
    #     : デフォルトは datetime.datetime.now()
    #     : 指定文字列は str(datetime) / 2018-02-22 08:54:47.187184 形式で GMT のタイムゾーン時間帯で送る
    #     : +09:00 のようなtimezone付きは python 2.7 ではサポートしていないようなのでつけない
    try:
        start_time_str = request.GET['start_time']
    except KeyError:
        start_time_str = None
    # 文字列指定があれば
    if start_time_str is not None:
        start_time = get_datetime_from_str(start_time_str, default=datetime.datetime.now(pytz.utc))
    else:
        # 指定なし現在時刻
        start_time = datetime.datetime.now(pytz.utc)
    return start_time


# GET /api/v1/sns/feeds
# last_feed の 引数を返却
def get_feeds_last_feed(request):
    # last_feed : この時間より新しいフィードを取得する
    try:
        last_feed_str = request.GET['last_feed']
    except KeyError:
        last_feed_str = None
    # 文字列指定があれば
    if last_feed_str is not None:
        last_feed = get_datetime_from_str(last_feed_str, default=None)
    else:
        # 指定なし
        last_feed = None
    return last_feed


# GET /api/v1/sns/feeds
# range_big_datetime の 引数を返却
def get_feeds_range_big_datetime(request):
    # range_big_datetime
    try:
        str_ = request.GET['range_big_datetime']
    except KeyError:
        str_ = None
    # 文字列指定があれば
    if str_ is not None:
        dt = get_datetime_from_str(str_, default=None)
    else:
        # 指定なし
        dt = None
    return dt


# GET /api/v1/sns/feeds
# range_small_datetime の 引数を返却
def get_feeds_range_small_datetime(request):
    # range_small_datetime
    try:
        str_ = request.GET['range_small_datetime']
    except KeyError:
        str_ = None
    # 文字列指定があれば
    if str_ is not None:
        dt = get_datetime_from_str(str_, default=None)
    else:
        # 指定なし
        dt = None
    return dt


# GET /api/v1/sns/feeds
# content の 引数を返却
def get_feeds_content(request):
    # 引数3: content : contentを返却するときはTrue(大文字小文字問わず)指定。デフォルトはFalse
    try:
        return request.GET['content'].lower() == 'true'
    except KeyError:
        return False
    except ValueError:
        return False


# GET /api/v1/sns/feeds
# user_id の 引数を返却 (longで)
def get_feeds_user_id(request):
    try:
        return int(request.GET['user_id'])
    except KeyError:
        return None
    except ValueError:
        return None


# GET /api/v1/sns/feeds
# instance の 引数を返却 (longで)
def get_feeds_instance(request):
    try:
        return request.GET['instance']
    except KeyError:
        return None


# GET /api/v1/sns/feeds
# index の 引数を返却
def get_feeds_index(request):
    return get_int_value(request, 'index')


# GET /api/v1/sns/feeds
# size の 引数を返却
def get_feeds_size(request):
    return get_int_value(request, 'size')


# 引数の文字列を int 変換して返却
# key がない, 変換失敗時は default 返却
def get_int_value(request, key, default=0):
    try:
        return int(request.GET[key])
    except KeyError:
        return default
    except ValueError:
        return default


# GET /api/v1/sns/attaches
# package_id の 引数を返却
def get_attaches_package_id(request):
    return get_package_id_from_get_argument(request)


# GET /api/v1/sns/comments
# package_id の 引数を返却
def get_comments_original_package_id(request):
    return get_package_id_from_get_argument(request)


# GET /api/v1/sns/content
# package_id の 引数を返却
def get_content_original_package_id(request):
    return get_package_id_from_get_argument(request)


# package_id の version を返却
def get_content_version(request):
    try:
        return request.GET['version']
    except KeyError:
        return None


# GET /api/v1/sns/check
# last_time の 引数を返却
def get_check_last_datetime(request):
    # 引数1: last_datetime : この時間より新しい日時の個数を検索する
    try:
        last_time_str = request.GET['last_feed_time']
    except KeyError:
        last_time_str = None
    # 文字列指定があれば
    if last_time_str is not None:
        last_time = get_datetime_from_str(last_time_str, default=None)
    else:
        last_time = None
    return last_time


# GET /api/v1/sns/check
# usr_id の 引数を返却
def get_check_user_id(request):
    try:
        return request.GET['user_id']
    except KeyError:
        return None


# GET /api/v1/sns/query
# query_string の 引数を返却
def get_query_query_string(request):
    try:
        return request.GET['query_string']
    except KeyError:
        return None


# GET パラメタから package_id を取得する
def get_package_id_from_get_argument(request):
    try:
        return request.GET['package_id']
    except KeyError:
        return None


# StixFile ドキュメントから返却辞書を作成
def get_return_dictionary_from_stix_file_document(stix_file, content=False):
    d = {}
    d['package_id'] = str(stix_file.package_id)
    d['package_name'] = stix_file.package_name
    d['created'] = str(stix_file.created)
    d['produced'] = str(stix_file.produced)
    # uploader は STIPUser の ID
    d['uploader'] = str(stix_file.via.uploader)
    if content:
        d['content'] = stix_file.content.read().decode('utf-8')
    d['version'] = str(stix_file.version)
    return d


# GET /api/v1/sns/feeds
@csrf_exempt
def feeds(request):
    try:
        # GET 以外はエラー
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        # 引数取得
        start_time = get_feeds_start_time(request)
        last_feed = get_feeds_last_feed(request)
        range_big_datetime = get_feeds_range_big_datetime(request)  # 期間範囲指定の大きい方(新しい方)。この時間を含む
        range_small_datetime = get_feeds_range_small_datetime(request)  # 期間範囲指定の小さい方(古い方)。この時間を含む
        user_id = get_feeds_user_id(request)
        instance = get_feeds_instance(request)
        content = get_feeds_content(request)
        query_string = request.GET.get(key='query_string', default=None)
        # index は 0 開始
        index = get_feeds_index(request)
        size = get_feeds_size(request)  # 指定なし時は size = -1

        # 返却条件は SNS に返却
        QQ = Q(is_post_sns__ne=False)
        if last_feed is not None:
            # last_feed の指定があった場合 (last_feed より新しい投稿を返却)
            QQ &= Q(produced__gt=last_feed)
        else:
            # last_feed の指定がない場合 (start_timeを最新として古い投稿を返却)
            QQ &= Q(produced__lte=start_time)

        # range_big_datetime 指定あり
        # 最大より古く(<=)
        if range_big_datetime is not None:
            QQ &= Q(produced__lte=range_big_datetime)
        # range_small_datetime 指定あり
        # 最小より新しい(>=)
        if range_small_datetime is not None:
            QQ &= Q(produced__gte=range_small_datetime)

        if query_string is not None:
            # 空白スペース区切りで分割
            query_strings = query_string.split(' ')
            # 空白スペース区切りで検索文字列が指定されていない場合(検索対象: 投稿/タイトル/ユーザ名/スクリーン名/タグ)(タグ以外は大文字小文字区別せず)
            if len(query_strings) == 1:
                if check_symbols(query_strings[0]) and tag.is_tag(query_strings[0]):
                    QQ &= (Q(sns_tags__in=query_strings))
                else:
                    QQ &= (Q(package_name__icontains=query_strings[0]) | Q(post__icontains=query_strings[0]) | Q(sns_user_name__icontains=query_strings[0]) | Q(sns_screen_name__icontains=query_strings[0]))
            # 空白スペース区切りの場合(検索対象: 投稿/タイトル/ユーザ名/スクリーン名/タグ)(タグ以外は大文字小文字区別せず)
            else:
                f_flag = True
                for q in query_strings:
                    if f_flag:
                        if check_symbols(q) and tag.is_tag(q):
                            query = Q(sns_tags__in=[q])
                        else:
                            query = Q(package_name__icontains=q) | Q(post__icontains=q) | Q(sns_user_name__icontains=q) | Q(sns_screen_name__icontains=q)
                        f_flag = False
                    else:
                        if check_symbols(q) and tag.is_tag(q):
                            query &= Q(sns_tags__in=[q])
                        else:
                            query &= Q(package_name__icontains=q) | Q(post__icontains=q) | Q(sns_user_name__icontains=q) | Q(sns_screen_name__icontains=q)
                QQ &= (query)

        # user_id が指定の場合はその user_id の投稿のみを抽出
        from ctirs.models.rs.models import STIPUser
        if user_id is not None:
            stip_user = STIPUser.objects.get(id=user_id)
            QQ &= (
                # SNS 産 STIX なら instance 名とユーザ名が一致した
                (Q(is_created_by_sns=True) & Q(sns_user_name=stip_user.username) & Q(sns_instance=instance)) |
                # SNS 産以外の STIX なら ユーザ名が一致した
                (Q(is_created_by_sns__ne=True) & Q(sns_user_name=stip_user.username))
            )

        else:
            # 未定の場合は存在している STIP_USER だけ有効
            stip_users = STIPUser.objects.only('id')
            stip_user_list = []
            for stip_user in stip_users:
                stip_user_list.append(stip_user.id)
            stip_users_vias = Vias.objects.filter(uploader__in=stip_user_list)
            QQ & Q(via__in=stip_users_vias)

        # count = 0
        feeds_list = []
        stix_files = StixFiles.objects(QQ).order_by('-produced').skip(index).timeout(False)
        # サイズ指定がある場合は limit 設定
        if size != -1:
            stix_files = stix_files.limit(size)
        # 指定された数値分 StixFiles から取得する(produced順にソートする かつ is_post_sns が False以外 かつ version が 2.0 以外)
        # for stix_file in StixFiles.objects(QQ).order_by('-produced').all().timeout(False):
        for stix_file in stix_files:
            feeds_list.append(get_return_dictionary_from_stix_file_document(stix_file, content=content))
        r = {}
        r['feeds'] = feeds_list
        return JsonResponse(r, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)

# GET /api/v1/sns/attaches
@csrf_exempt
def attaches(request):
    try:
        # GET 以外はエラー
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        # 引数取得
        package_id = get_attaches_package_id(request)
        if package_id is None:
            print('/api/v1/sns/attaches package_id is None.')
            return HttpResponseNotFound()
        try:
            stix_file = StixFiles.objects.get(package_id=package_id)
            d = get_return_dictionary_from_stix_file_document(stix_file)
            return JsonResponse(d, safe=False)
        except DoesNotExist:
            # 該当レコードがなかった
            print('/api/v1/sns/attaches DoesNotExist (%s)' % (str(package_id)))
            return HttpResponseNotFound()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)

# GET /api/v1/sns/related_packages
@csrf_exempt
def related_packages(request):
    try:
        # GET 以外はエラー
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 引数取得
        original_package_id = get_comments_original_package_id(request)
        if original_package_id is None:
            print('/api/v1/sns/related_packages package_id is None.')
            return HttpResponseNotFound()
        related_packages_list = []
        # original_package_id を related_packages リスト要素に含む stix_fileを返却
        for stix_file in StixFiles.objects(related_packages=original_package_id):
            related_packages_list.append(get_return_dictionary_from_stix_file_document(stix_file))
        return JsonResponse(related_packages_list, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)

# GET /api/v1/sns/content
@csrf_exempt
def content(request):
    try:
        # GET 以外はエラー
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 引数取得
        package_id = get_content_original_package_id(request)
        version = get_content_version(request)

        if package_id is None:
            print('/api/v1/sns/content package_id is None.')
            return HttpResponseNotFound()

        stix_file = StixFiles.objects.get(package_id=package_id)
        doc = _get_stix_file_document(stix_file)
        if not version:
            return JsonResponse(doc, safe=False)
        if stix_file.version.startswith('1.'):
            if version.startswith('2.'):
                content = stix_file.get_elevate_21()
                doc['content'] = content
                doc['version'] = '2.1'
        elif stix_file.version == '2.0':
            if version == '2.1':
                content = stix_file.get_elevate_21()
                doc['content'] = content
                doc['version'] = '2.1'
            elif version.startswith('1.'):
                content = stix_file.get_slide_12()
                doc['content'] = content
                doc['version'] = '1.2'
        elif stix_file.version == '2.1':
            if version.startswith('1.'):
                content = stix_file.get_slide_12()
                doc['content'] = content
                doc['version'] = '1.2'
        return JsonResponse(doc, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)


def _get_stix_file_document(stix_file):
    return get_return_dictionary_from_stix_file_document(
        stix_file, content=True)


# GET /api/v1/sns/comments
@csrf_exempt
def comments(request):
    try:
        # GET 以外はエラー
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 引数取得
        original_package_id = get_comments_original_package_id(request)
        if original_package_id is None:
            print('/api/v1/sns/comments package_id is None.')
            return HttpResponseNotFound()
        comments_list = []
        # original_package_id を related_packages リスト要素に含み sns_type が comment の stix_fileを返却
        for stix_file in StixFiles.objects(Q(related_packages=original_package_id) & Q(sns_type=StixFiles.STIP_SNS_TYPE_COMMENT)):
            comments_list.append(get_return_dictionary_from_stix_file_document(stix_file))
        return JsonResponse(comments_list, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)

# GET /api/v1/sns/likers
@csrf_exempt
def likers(request):
    try:
        # GET 以外はエラー
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 引数取得
        original_package_id = get_comments_original_package_id(request)
        if original_package_id is None:
            print('/api/v1/sns/likers package_id is None.')
            return HttpResponseNotFound()
        liker_dict = {}
        # original_package_id を related_packages リスト要素に含む stix_fileを返却
        for stix_file in StixFiles.objects(Q(related_packages=original_package_id) & Q(sns_type=StixFiles.STIP_SNS_TYPE_LIKE)):
            liker = stix_file.get_unique_name()
            if liker is not None:
                if liker in liker_dict:
                    liker_dict[liker] += 1
                else:
                    liker_dict[liker] = 1

        # original_package_id を related_packages リスト要素に含む stix_fileを返却
        for stix_file in StixFiles.objects(Q(related_packages=original_package_id) & Q(sns_type=StixFiles.STIP_SNS_TYPE_UNLIKE)):
            unliker = stix_file.get_unique_name()
            if unliker is not None:
                if unliker in liker_dict:
                    liker_dict[unliker] -= 1
                else:
                    liker_dict[unliker] = -1
        likers = []
        for liker, value in liker_dict.items():
            if value == 1:
                likers.append(liker)
        return JsonResponse(likers, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)

# GET /api/v1/sns/share_misp
@csrf_exempt
def share_misp(request):
    try:
        # GET 以外はエラー
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 引数取得
        package_id = get_package_id_from_get_argument(request)
        mc = MispUploadAdapterControl()
        j = mc.upload_misp(package_id)
        event_id = j['Event']['id']
        misp_conf = MispAdapter.get()
        tmp_url = misp_conf.url
        if tmp_url[-1] != '/':
            tmp_url += '/'
        url = '%sevents/view/%s' % (tmp_url, event_id)
        r = {}
        r['url'] = url
        return JsonResponse(r, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)

# GET /api/v1/sns/query
@csrf_exempt
def query(request):
    try:
        # GET 以外はエラー
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        # 引数取得
        size = get_feeds_size(request)  # 指定なし時は size = -1
        query_string = get_query_query_string(request)
        # query_string  未指定時は空リスト返却
        if query_string is None:
            r = {}
            r['feeds'] = []
            return JsonResponse(r, safe=False)

        # 返却条件は SNS に返却　かつ　version 2.0 以外
        QQ = Q(is_post_sns__ne=False) & Q(version__ne='2.0')

        # 空白スペース区切りで分割
        query_strings = query_string.split(' ')
        # 空白スペース区切りで検索文字列が指定されていない場合(検索対象: 投稿/タイトル/ユーザ名/スクリーン名/タグ)(タグ以外は大文字小文字区別せず)
        if len(query_strings) == 1:
            if check_symbols(query_strings[0]) and tag.is_tag(query_strings[0]):
                QQ &= (Q(sns_tags__in=query_strings))
            else:
                QQ &= (Q(package_name__icontains=query_strings[0]) | Q(post__icontains=query_strings[0]) | Q(sns_user_name__icontains=query_strings[0]) | Q(sns_screen_name__icontains=query_strings[0]))
        # 空白スペース区切りの場合(検索対象: 投稿/タイトル/ユーザ名/スクリーン名/タグ)(タグ以外は大文字小文字区別せず)
        else:
            f_flag = True
            for q in query_strings:
                if f_flag:
                    if check_symbols(q) and tag.is_tag(q):
                        query = Q(sns_tags__in=[q])
                    else:
                        query = Q(package_name__icontains=q) | Q(post__icontains=q) | Q(sns_user_name__icontains=q) | Q(sns_screen_name__icontains=q)
                    f_flag = False
                else:
                    if check_symbols(q) and tag.is_tag(q):
                        query &= Q(sns_tags__in=[q])
                    else:
                        query &= Q(package_name__icontains=q) | Q(post__icontains=q) | Q(sns_user_name__icontains=q) | Q(sns_screen_name__icontains=q)
            QQ &= (query)
        stix_files = set([])
        # Query
        for stix_file in StixFiles.objects(QQ).order_by('-produced').timeout(False):
            stix_files.add(stix_file)

        # ObservableCache から query_string を含む StixFile の set を作成
        for observable_cache in ObservableCaches.objects.filter(Q(value__icontains=query_string)):
            stix_file = StixFiles.objects.get(package_id=observable_cache.package_id)
            stix_files.add(stix_file)

        # 時間でソートする
        stix_files = sorted(list(stix_files), key=lambda s: s.produced, reverse=True)

        # サイズ指定がある場合は上位から指定sizeを取得
        if size != -1:
            stix_files = stix_files[:size]

        # 返却データ作成
        feeds_list = []
        for stix_file in stix_files:
            feeds_list.append(get_return_dictionary_from_stix_file_document(stix_file, content=content))
        r = {}
        r['feeds'] = feeds_list
        return JsonResponse(r, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)


# S-TIP SNS の STIX から User Name を返却する
def get_stip_sns_username(stix_package):
    try:
        for marking in stix_package.stix_header.handling:
            if isinstance(marking, MarkingSpecification):
                marking_structure = marking.marking_structures[0]
                if isinstance(marking_structure, SimpleMarkingStructure):
                    statement = marking_structure.statement
                    if statement.startswith(STIP_SNS_USER_NAME_PREFIX):
                        return statement[len(STIP_SNS_USER_NAME_PREFIX):]
    except BaseException:
        return None


# S-TIP SNS の Like STIX であれば Liker アカウントを返却
# 未対象時は None 返却
def get_liker(stix_package):
    if not is_stip_sns_stix(stix_package):
        return None
    # Titile が Like to で始まっているもの
    if not stix_package.stix_header.title.startswith(STIP_SNS_LIKE_TITLE_PREFIX):
        return None
    return get_stip_sns_username(stix_package)


# S-TIP SNS の Like STIX であれば Unliker アカウントを返却
# 未対象時は None 返却
def get_unliker(stix_package):
    if not is_stip_sns_stix(stix_package):
        return False
    if not stix_package.stix_header.title.startswith(STIP_SNS_UNLIKE_TITLE_PREFIX):
        return None
    return get_stip_sns_username(stix_package)


# S-TIP SNS の Comment STIX か
def is_stip_sns_comment_stix(stix_package):
    if not is_stip_sns_stix(stix_package):
        return False
    # Titile が Comment to で始まっているもの
    return stix_package.stix_header.title.startswith(STIP_SNS_COMMENT_TITLE_PREFIX)


# S-TIP SNS の STIX か
def is_stip_sns_stix(stix_package):
    try:
        for tool in stix_package.stix_header.information_source.tools:
            if (tool.name == const.SNS_TOOL_NAME) and (tool.vendor == const.SNS_TOOL_VENDOR):
                return True
        return False
    except BaseException:
        return False


def check_symbols(word):
    delimiter_string = string.punctuation.translate(str.maketrans({'#':'', '_':''})) + string.whitespace
    word_list = re.split('([' + delimiter_string + '])', word)
    if len(word_list) == 1:
        return True
    else:
        return False

