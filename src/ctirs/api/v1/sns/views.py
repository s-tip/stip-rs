import pytz
import datetime
import re
import string
import json
from mongoengine.errors import DoesNotExist
from mongoengine.queryset.visitor import Q
from django.http import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse, HttpResponseNotFound
from ctirs.api import error
from ctirs.api.v1.decolators import api_key_auth
from ctirs.core.mongo.documents import Vias, MispAdapter
from ctirs.core.mongo.documents_stix import StixFiles, ObservableCaches, Tags
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
SUGGEST_LIMIT = 5
SUGGEST_MIN_LENGTH = 2 


def get_datetime_from_str(s, default=None):
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.utc)
    except BaseException:
        return default


def get_feeds_start_time(request):
    try:
        start_time_str = request.GET['start_time']
    except KeyError:
        start_time_str = None
    if start_time_str is not None:
        start_time = get_datetime_from_str(start_time_str, default=datetime.datetime.now(pytz.utc))
    else:
        start_time = datetime.datetime.now(pytz.utc)
    return start_time


def get_feeds_last_feed(request):
    try:
        last_feed_str = request.GET['last_feed']
    except KeyError:
        last_feed_str = None
    if last_feed_str is not None:
        last_feed = get_datetime_from_str(last_feed_str, default=None)
    else:
        last_feed = None
    return last_feed


def get_feeds_range_big_datetime(request):
    try:
        str_ = request.GET['range_big_datetime']
    except KeyError:
        str_ = None
    if str_ is not None:
        dt = get_datetime_from_str(str_, default=None)
    else:
        dt = None
    return dt


def get_feeds_range_small_datetime(request):
    try:
        str_ = request.GET['range_small_datetime']
    except KeyError:
        str_ = None
    if str_ is not None:
        dt = get_datetime_from_str(str_, default=None)
    else:
        dt = None
    return dt


def get_feeds_content(request):
    try:
        return request.GET['content'].lower() == 'true'
    except KeyError:
        return False
    except ValueError:
        return False


def get_feeds_user_id(request):
    try:
        return int(request.GET['user_id'])
    except KeyError:
        return None
    except ValueError:
        return None


def get_feeds_instance(request):
    try:
        return request.GET['instance']
    except KeyError:
        return None


def get_feeds_index(request):
    return get_int_value(request, 'index')


def get_feeds_size(request):
    return get_int_value(request, 'size')


def get_feeds_filter(request):
    try:
        return json.loads(request.GET['filter'])
    except Exception:
        return None


def get_int_value(request, key, default=0):
    try:
        return int(request.GET[key])
    except KeyError:
        return default
    except ValueError:
        return default


def get_attaches_package_id(request):
    return get_package_id_from_get_argument(request)


def get_comments_original_package_id(request):
    return get_package_id_from_get_argument(request)


def get_content_original_package_id(request):
    return get_package_id_from_get_argument(request)


def get_content_version(request):
    try:
        return request.GET['version']
    except KeyError:
        return None


def get_check_last_datetime(request):
    try:
        last_time_str = request.GET['last_feed_time']
    except KeyError:
        last_time_str = None
    if last_time_str is not None:
        last_time = get_datetime_from_str(last_time_str, default=None)
    else:
        last_time = None
    return last_time


def get_check_user_id(request):
    try:
        return request.GET['user_id']
    except KeyError:
        return None


def get_query_query_string(request):
    try:
        return request.GET['query_string']
    except KeyError:
        return None


def get_package_id_from_get_argument(request):
    try:
        return request.GET['package_id']
    except KeyError:
        return None


def get_return_dictionary_from_stix_file_document(stix_file, content=False):
    d = {}
    d['package_id'] = str(stix_file.package_id)
    d['package_name'] = stix_file.package_name
    d['created'] = str(stix_file.created)
    d['produced'] = str(stix_file.produced)
    d['uploader'] = str(stix_file.via.uploader)
    if content:
        d['content'] = stix_file.content.read().decode('utf-8')
    d['version'] = str(stix_file.version)
    return d


# GET /api/v1/sns/feeds
@csrf_exempt
@api_key_auth
def feeds(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        start_time = get_feeds_start_time(request)
        last_feed = get_feeds_last_feed(request)
        range_big_datetime = get_feeds_range_big_datetime(request)
        range_small_datetime = get_feeds_range_small_datetime(request)
        user_id = get_feeds_user_id(request)
        instance = get_feeds_instance(request)
        content = get_feeds_content(request)
        query_string = request.GET.get(key='query_string', default=None)
        index = get_feeds_index(request)
        size = get_feeds_size(request)
        filter = get_feeds_filter(request)
        if filter is None:
            ignore_accounts = None
            ignore_na = False
        else:
            try:
                ignore_accounts = filter['ignore_accounts']
                if len(ignore_accounts) == 0:
                    ignore_accounts = None
            except KeyError:
                ignore_accounts = None
            try:
                ignore_na = filter['ignore_na']
            except KeyError:
                ignore_na = False

        QQ = Q(is_post_sns__ne=False)
        if last_feed is not None:
            QQ &= Q(produced__gt=last_feed)
        else:
            QQ &= Q(produced__lte=start_time)

        if range_big_datetime is not None:
            QQ &= Q(produced__lte=range_big_datetime)
        if range_small_datetime is not None:
            QQ &= Q(produced__gte=range_small_datetime)

        if query_string is not None:
            query_strings = re.split('[ 　]', query_string)
            if len(query_strings) == 1:
                if check_symbols(query_strings[0]) and tag.is_tag(query_strings[0]):
                    QQ &= Q(sns_lower_tags__in=[query_strings[0].lower()])
                else:
                    QQ &= Q(package_name__icontains=query_strings[0]) | Q(post__icontains=query_strings[0]) | Q(sns_user_name__icontains=query_strings[0]) | Q(sns_screen_name__icontains=query_strings[0])
            else:
                f_flag = True
                for q in query_strings:
                    if f_flag:
                        if check_symbols(q) and tag.is_tag(q):
                            query = Q(sns_lower_tags__in=[q.lower()])
                        else:
                            query = Q(package_name__icontains=q) | Q(post__icontains=q) | Q(sns_user_name__icontains=q) | Q(sns_screen_name__icontains=q)
                        f_flag = False
                    else:
                        if check_symbols(q) and tag.is_tag(q):
                            query &= Q(sns_lower_tags__in=[q.lower()])
                        else:
                            query &= Q(package_name__icontains=q) | Q(post__icontains=q) | Q(sns_user_name__icontains=q) | Q(sns_screen_name__icontains=q)
                QQ &= query

        from ctirs.models.rs.models import STIPUser
        if user_id is not None:
            stip_user = STIPUser.objects.get(id=user_id)
            QQ &= (
                (Q(is_created_by_sns=True) & Q(sns_user_name=stip_user.username) & Q(sns_instance=instance))
                | (Q(is_created_by_sns__ne=True) & Q(sns_user_name=stip_user.username))
            )

        else:
            stip_users = STIPUser.objects.only('id')
            stip_user_list = []
            for stip_user in stip_users:
                if ignore_accounts and len(ignore_accounts):
                    if stip_user.username in ignore_accounts:
                        continue
                stip_user_list.append(stip_user.id)
            stip_users_vias = Vias.objects.filter(uploader__in=stip_user_list)
            QQ &= Q(via__in=stip_users_vias)

        if ignore_accounts:
            QQ &= (Q(sns_user_name__nin=ignore_accounts) & Q(sns_type=StixFiles.STIP_SNS_TYPE_V2_POST))

        if ignore_na:
            QQ &= Q(sns_user_name__ne='')

        feeds_list = []
        stix_files = StixFiles.objects(QQ).order_by('-produced').skip(index).timeout(False)
        if size != -1:
            stix_files = stix_files.limit(size)
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
@api_key_auth
def attaches(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        package_id = get_attaches_package_id(request)
        if package_id is None:
            return HttpResponseNotFound()
        try:
            stix_file = StixFiles.objects.get(package_id=package_id)
            d = get_return_dictionary_from_stix_file_document(stix_file)
            return JsonResponse(d, safe=False)
        except DoesNotExist:
            return HttpResponseNotFound()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)


# GET /api/v1/sns/related_packages
@csrf_exempt
@api_key_auth
def related_packages(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        original_package_id = get_comments_original_package_id(request)
        if original_package_id is None:
            return HttpResponseNotFound()
        related_packages_list = []
        for stix_file in StixFiles.objects(related_packages=original_package_id):
            related_packages_list.append(get_return_dictionary_from_stix_file_document(stix_file))
        return JsonResponse(related_packages_list, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)


# GET /api/v1/sns/content
@csrf_exempt
@api_key_auth
def content(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        package_id = get_content_original_package_id(request)
        version = get_content_version(request)

        if package_id is None:
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
@api_key_auth
def comments(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        original_package_id = get_comments_original_package_id(request)
        if original_package_id is None:
            return HttpResponseNotFound()
        comments_list = []
        for stix_file in StixFiles.objects(Q(related_packages=original_package_id) & Q(sns_type=StixFiles.STIP_SNS_TYPE_COMMENT)):
            comments_list.append(get_return_dictionary_from_stix_file_document(stix_file))
        return JsonResponse(comments_list, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)


# GET /api/v1/sns/likers
@csrf_exempt
@api_key_auth
def likers(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        original_package_id = get_comments_original_package_id(request)
        if original_package_id is None:
            return HttpResponseNotFound()
        liker_dict = {}
        for stix_file in StixFiles.objects(Q(related_packages=original_package_id) & Q(sns_type=StixFiles.STIP_SNS_TYPE_LIKE)):
            liker = stix_file.get_unique_name()
            if liker is not None:
                if liker in liker_dict:
                    liker_dict[liker] += 1
                else:
                    liker_dict[liker] = 1

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
@api_key_auth
def share_misp(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

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
@api_key_auth
def query(request):
    try:
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        size = get_feeds_size(request)
        query_string = get_query_query_string(request)
        if query_string is None:
            r = {}
            r['feeds'] = []
            return JsonResponse(r, safe=False)

        QQ = Q(is_post_sns__ne=False) & Q(version__ne='2.0')

        query_strings = re.split('[ 　]', query_string)
        if len(query_strings) == 1:
            if check_symbols(query_strings[0]) and tag.is_tag(query_strings[0]):
                QQ &= Q(sns_lower_tags__in=[query_strings[0].lower()])
            else:
                QQ &= Q(package_name__icontains=query_strings[0]) | Q(post__icontains=query_strings[0]) | Q(sns_user_name__icontains=query_strings[0]) | Q(sns_screen_name__icontains=query_strings[0])
        else:
            f_flag = True
            for q in query_strings:
                if f_flag:
                    if check_symbols(q) and tag.is_tag(q):
                        query = Q(sns_lower_tags__in=[q.lower()])
                    else:
                        query = Q(package_name__icontains=q) | Q(post__icontains=q) | Q(sns_user_name__icontains=q) | Q(sns_screen_name__icontains=q)
                    f_flag = False
                else:
                    if check_symbols(q) and tag.is_tag(q):
                        query &= Q(sns_lower_tags__in=[q.lower()])
                    else:
                        query &= Q(package_name__icontains=q) | Q(post__icontains=q) | Q(sns_user_name__icontains=q) | Q(sns_screen_name__icontains=q)
            QQ &= query
        stix_files = set([])
        for stix_file in StixFiles.objects(QQ).order_by('-produced').timeout(False):
            stix_files.add(stix_file)

        for observable_cache in ObservableCaches.objects.filter(Q(value__icontains=query_string)):
            stix_file = StixFiles.objects.get(package_id=observable_cache.package_id)
            stix_files.add(stix_file)

        stix_files = sorted(list(stix_files), key=lambda s: s.produced, reverse=True)

        if size != -1:
            stix_files = stix_files[:size]

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


def get_liker(stix_package):
    if not is_stip_sns_stix(stix_package):
        return None
    if not stix_package.stix_header.title.startswith(STIP_SNS_LIKE_TITLE_PREFIX):
        return None
    return get_stip_sns_username(stix_package)


def get_unliker(stix_package):
    if not is_stip_sns_stix(stix_package):
        return False
    if not stix_package.stix_header.title.startswith(STIP_SNS_UNLIKE_TITLE_PREFIX):
        return None
    return get_stip_sns_username(stix_package)


def is_stip_sns_comment_stix(stix_package):
    if not is_stip_sns_stix(stix_package):
        return False
    return stix_package.stix_header.title.startswith(STIP_SNS_COMMENT_TITLE_PREFIX)


def is_stip_sns_stix(stix_package):
    try:
        for tool in stix_package.stix_header.information_source.tools:
            if (tool.name == const.SNS_TOOL_NAME) and (tool.vendor == const.SNS_TOOL_VENDOR):
                return True
        return False
    except BaseException:
        return False


def check_symbols(word):
    delimiter_string = string.punctuation.translate(str.maketrans({'#': '', '_': ''})) + string.whitespace
    word_list = re.split('([' + delimiter_string + '])', word)
    if len(word_list) == 1:
        return True
    else:
        return False


# GET /api/v1/sns/feeds/tags
@csrf_exempt
@api_key_auth
def tags(request):
    try:
        suggest_list = []
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        word = request.GET.get('word')
        if not word or len(word) < SUGGEST_MIN_LENGTH:
            return JsonResponse(suggest_list, safe=False)
        if word[0] != '#':
            return JsonResponse(suggest_list, safe=False)
        tags = Tags.objects.filter(tag__istartswith=word).order_by('tag').limit(SUGGEST_LIMIT)
        for tag in tags:
            suggest_list.append(tag.tag)
        return JsonResponse(suggest_list, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(e)
