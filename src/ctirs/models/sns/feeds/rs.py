import os
import stip.common.const as const
import requests
import urllib3
from ctirs.models.sns.config.models import SNSConfig
from pytz import timezone
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)


# CTIM-RSに登録する
def regist_ctim_rs(api_user, package_name, stix_file_path, community_name=None):
    with open(stix_file_path, 'r', encoding='utf-8') as fp:
        files = {
            'stix': fp,
        }
        headers = _get_ctirs_api_http_headers(api_user)
        if not community_name:
            community_name = SNSConfig.get_rs_community_name()
        payload = {
            'community_name': community_name,
            'package_name': package_name,
        }

        requests.post(
            SNSConfig.get_rs_regist_stix_url(),
            headers=headers,
            files=files,
            data=payload,
            verify=False)
    return


# CTIM-RSからmatchingを取得する
def get_matching_from_rs(api_user, id_):
    url = '%s' % (SNSConfig.get_rs_get_matching_url())
    headers = _get_ctirs_api_http_headers(api_user)
    params = {
        'package_id': id_,
        'exact': True,
    }
    rsp = requests.get(
        url,
        headers=headers,
        params=params,
        verify=False)
    return rsp.json()['data']


# CTIM-RSのwebapi用のhttp header
def _get_ctirs_api_http_headers(api_user):
    # username,api_key は api_userごとの値を使用する
    return {
        'apikey': api_user.api_key,
        'username': api_user.username.encode(),
    }


# package_idからファイル名に変更
# : がファイル名に使えないため -- に変更する
def convert_package_id_to_filename(package_id):
    return package_id.replace(':', '--')


# ファイル名からpacakge_idに変更
def convert_filename_to_package_id(filename):
    return filename.replace('--', ':')


# package_id に該当するファイルが cache dir に存在する場合はそのファイルパスを
# 存在しない場合は RS から取得して cache_dir に格納してそのファイルパスを返却する
def get_stix_file_path(api_user, package_id):
    # cache のファイルパスを作成する
    file_name = convert_package_id_to_filename(package_id)
    # file_path = django_settings.STIX_CACHE_DIR + file_name
    file_path = const.STIX_CACHE_DIR + file_name
    # cache に存在するかチェックする
    if not os.path.exists(file_path):
        # 存在しない場合は RS から 取得してファイルキャッシュに格納する
        content = get_content_from_rs(api_user, package_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as fp:
                fp.write(content)
        except BaseException:
            try:
                # エラー時は削除する
                os.remove(file_path)
            except BaseException:
                pass
    return file_path


# datetime 型から RS 引数フォーマットの日時文字列に変更する
# 例 : 2018-02-22 08:54:47.187184
def get_dtstr_from_datetime(dt):
    return dt.astimezone(timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S.%f')


########
# SNS 用
# 投稿用 STIX リストを時間順に取得
# def get_feeds_from_rs(api_user,start_time=None,last_feed_datetime=None,user_id=None):
def get_feeds_from_rs(
        api_user,
        start_time=None,
        last_feed_datetime=None,
        user_id=None,
        range_small_datetime=None,  # 期間範囲指定の小さい方(古い方)。この時間を含む
        range_big_datetime=None,  # 期間範囲指定の大きい方(新しい方)。この時間を含む
        query_string=None,
        index=0,
        size=-1):
    # start_time は aware な datetime
    url = '%s' % (SNSConfig.get_rs_get_feeds_url())
    headers = _get_ctirs_api_http_headers(api_user)
    params = {}
    # start_time 指定があった場合は設定する
    if start_time is not None:
        # 2018-02-22 08:54:47.187184 のようなフォーマットをGMTでおくる
        params['start_time'] = get_dtstr_from_datetime(start_time)
    # last_feed_datetime 指定があった場合は設定する
    if last_feed_datetime is not None:
        # 2018-02-22 08:54:47.187184 のようなフォーマットをGMTでおくる
        params['last_feed'] = get_dtstr_from_datetime(last_feed_datetime)
    # range_small_datetime 指定があった場合は設定する
    if range_small_datetime is not None:
        # 2018-02-22 08:54:47.187184 のようなフォーマットをGMTでおくる
        params['range_small_datetime'] = get_dtstr_from_datetime(range_small_datetime)
    # range_big_datetime 指定があった場合は設定する
    if range_big_datetime is not None:
        # 2018-02-22 08:54:47.187184 のようなフォーマットをGMTでおくる
        params['range_big_datetime'] = get_dtstr_from_datetime(range_big_datetime)
    # query_string 指定があった場合は設定する
    if query_string is not None:
        params['query_string'] = query_string

    # index, size 追加
    params['index'] = str(index)
    params['size'] = str(size)
    # user_id 指定があった場合は設定する
    if user_id is not None:
        params['user_id'] = user_id
    params['instance'] = SNSConfig.get_sns_identity_name()
    rsp = requests.get(
        url,
        headers=headers,
        params=params,
        verify=False)
    return rsp.json()['feeds']


# SNS 用
# 検索
def query(
        api_user,
        query_string,
        size=-1):
    url = '%s' % (SNSConfig.get_rs_query_url())
    headers = _get_ctirs_api_http_headers(api_user)
    params = {}
    # index, size 追加
    params['query_string'] = query_string
    params['size'] = str(size)
    rsp = requests.get(
        url,
        headers=headers,
        params=params,
        verify=False)
    return rsp.json()['feeds']


# 投稿用 STIX を取得
def get_content_from_rs(api_user, package_id, version=None):
    # /api/v1/sns/content をコールし、 content のみを返却する
    j = get_package_info_from_package_id(api_user, package_id, version)
    return j['content']


def get_package_info_from_package_id(api_user, package_id, version=None):
    url = '%s' % (SNSConfig.get_rs_get_content_url())
    params = {}
    params['package_id'] = package_id
    if version:
        params['version'] = version
    headers = _get_ctirs_api_http_headers(api_user)
    rsp = requests.get(
        url,
        headers=headers,
        params=params,
        verify=False)
    if rsp.status_code != 200:
        raise Exception('Error occured: status=%d' % (rsp.status_code))
    return rsp.json()


# 関連 STIX (Like, Unlike, Comment) 取得
def get_related_packages_from_rs(api_user, package_id):
    url = '%s' % (SNSConfig.get_rs_get_related_packages_url())
    params = {}
    params['package_id'] = package_id
    headers = _get_ctirs_api_http_headers(api_user)
    rsp = requests.get(
        url,
        headers=headers,
        params=params,
        verify=False)
    return rsp.json()


# comments 取得
def get_comment_from_rs(api_user, package_id):
    url = '%s' % (SNSConfig.get_rs_get_comments_url())
    params = {}
    params['package_id'] = package_id
    headers = _get_ctirs_api_http_headers(api_user)
    rsp = requests.get(
        url,
        headers=headers,
        params=params,
        verify=False)
    return rsp.json()


# likers 取得
def get_likers_from_rs(api_user, package_id):
    url = '%s' % (SNSConfig.get_rs_get_likers_url())
    params = {}
    params['package_id'] = package_id
    headers = _get_ctirs_api_http_headers(api_user)
    rsp = requests.get(
        url,
        headers=headers,
        params=params,
        verify=False)
    return rsp.json()


# MISP 共有
def share_misp(api_user, package_id):
    url = '%s' % (SNSConfig.get_rs_get_share_misp_url())
    params = {}
    params['package_id'] = package_id
    headers = _get_ctirs_api_http_headers(api_user)
    rsp = requests.get(
        url,
        headers=headers,
        params=params,
        verify=False)
    return rsp.json()


def post_stix_v2_sightings(api_user, observed_data_id, first_seen, last_seen, count):
    data = {}
    headers = _get_ctirs_api_http_headers(api_user)
    if first_seen is not None:
        data['first_seen'] = first_seen
    if last_seen is not None:
        data['last_seen'] = last_seen
    if count is not None:
        data['count'] = count
    url_pattern = '%s' % (SNSConfig.get_rs_post_stix_file_v2_sighting())
    url = url_pattern % (observed_data_id)
    rsp = requests.post(
        url,
        headers=headers,
        data=data,
        verify=False)
    return rsp.json()
