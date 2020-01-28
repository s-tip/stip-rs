import bleach
import datetime
import pytz
import os
import base64
from . import rs
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from ctirs.models import Group
from ctirs.models import STIPUser
from ctirs.models import SNSConfig
from stix.core.stix_package import STIXPackage
from stix.extensions.marking.ais import AISMarkingStructure
from stix.extensions.marking.tlp import TLPMarkingStructure
from stix.extensions.marking.simple_marking import SimpleMarkingStructure
from stix.data_marking import MarkingSpecification
from stix.common.structured_text import StructuredText
import stip.common.const as const


@python_2_unicode_compatible
class AttachFile(models.Model):
    file_name = models.TextField(max_length=1024)
    file_path = models.FilePathField(max_length=1024, default=None, null=True)
    package_id = models.TextField(max_length=1024)

    class Meta:
        db_table = 'stip_sns_attachfile'

    def __str__(self):
        return self.file_name

    def get_file_path(self):
        return self.package_id


@python_2_unicode_compatible
class Feed(models.Model):
    STIP_SNS_USER_NAME_PREFIX = const.STIP_SNS_USER_NAME_KEY + ': '
    STIP_SNS_SCREEN_NAME_PREFIX = const.STIP_SNS_SCREEN_NAME_KEY + ': '
    STIP_SNS_AFFILIATION_PREFIX = const.STIP_SNS_AFFILIATION_KEY + ': '
    STIP_SNS_REGION_CODE_PREFIX = const.STIP_SNS_REGION_CODE_KEY + ': '
    STIP_SNS_CI_PREFIX = const.STIP_SNS_CI_KEY + ': '
    STIP_SNS_REFERRED_URL_PREFIX = const.STIP_SNS_REFERRED_URL_KEY + ': '
    STIP_SNS_STIX2_PACKAGE_ID_PREFIX = const.STIP_SNS_STIX2_PACKAGE_ID_KEY + ': '

    package_id = models.CharField(max_length=128, default='', primary_key=True)
    user = models.ForeignKey(STIPUser)
    date = models.DateTimeField(null=True)
    post = models.TextField(max_length=1024)
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    files = models.ManyToManyField(AttachFile)
    title = models.TextField(max_length=1024, default=None, null=True)
    stix_file_path = models.FilePathField(max_length=1024, default=None, null=True)
    tlp = models.CharField(max_length=10, choices=const.TLP_CHOICES, default='AMBER')
    sharing_range_type = models.CharField(max_length=10, choices=const.SHARING_RANGE_CHOICES, default=const.SHARING_RANGE_TYPE_KEY_ALL)
    sharing_people = models.ManyToManyField(STIPUser, related_name='feed_sharing_people')
    sharing_group = models.ForeignKey(Group, default=None, null=True)
    filename_pk = models.CharField(max_length=128, default='undefined')
    screen_name = models.CharField(max_length=128, default='')
    screen_affiliation = models.CharField(max_length=50, default='')
    screen_instance = models.CharField(max_length=128, default='', null=True)
    is_valid_user = models.BooleanField(default='True')
    region_code = models.CharField(max_length=128, default='')
    country_code = models.TextField(max_length=8, default=None, null=True)
    administrative_code = models.TextField(max_length=8, default=None, null=True)
    ci = models.CharField(max_length=128, default='', null=True)
    referred_url = models.TextField(max_length=1024, default=None, null=True)
    stix2_package_id = models.CharField(max_length=128, default='', null=True)
    tmp_sharing_people = []
    build_cache_flag = False

    class Meta:
        verbose_name = _('Feed')
        verbose_name_plural = _('Feeds')
        ordering = ('-date',)
        db_table = 'stip_sns_feed'

    def linkfy_post(self):
        if isinstance(self.post, StructuredText):
            v = self.post.value
        else:
            v = self.post
        return bleach.linkify(v)

    def __str__(self):
        return self.post

    @staticmethod
    # 起動時に読み込み、Cacheを構築する
    def build_cache(api_user):
        packages_from_rs = rs.get_feeds_from_rs(
            api_user,
            index=0,
            size=-1)
        for package_from_rs in packages_from_rs:
            # RS 復帰の json を元に Feed 構築する
            Feed.get_feeds_from_package_from_rs(api_user, package_from_rs)

    @staticmethod
    # sharing_rangeによるフィルタを行ったquerysetを返却する
    def get_filter_query_set(feeds, request_user, feeds_=None):
        if feeds_ is None:
            return []

        l = []
        for feed_ in feeds_:
            # 自分の投稿ならリスト追加
            if request_user is not None:
                if request_user == feed_.user:
                    l.append(feed_)
                    continue
            # sharing_range_typeがallなら追加
            if feed_.sharing_range_type == const.SHARING_RANGE_TYPE_KEY_ALL:
                l.append(feed_)
                continue
            elif feed_.sharing_range_type == const.SHARING_RANGE_TYPE_KEY_GROUP:
                # sharing_group に ログインユーザが含まれていたら追加
                if request_user is not None:
                    # filter は Profile の user 検索ではなく STIPUser で行う
                    if len(feed_.sharing_group.members.filter(username=request_user)) == 1:
                        l.append(feed_)
                        continue
            elif feed_.sharing_range_type == const.SHARING_RANGE_TYPE_KEY_PEOPLE:
                # sharing_people に ログインユーザが含まれていたら追加
                if request_user is not None:
                    if request_user in feed_.sharing_people.all():
                        l.append(feed_)
                        continue
        return l

    @staticmethod
    # 指定の package_id を元に RS から STIX を取得し Feedを構築する
    def get_feeds_from_package_id(api_user, package_id):
        package_from_rs = rs.get_package_info_from_package_id(api_user, package_id)
        return Feed.get_feeds_from_package_from_rs(api_user, package_from_rs)

    @staticmethod
    # stix_package が S-TIP SNS 産？
    def is_stip_sns_stix_package(stix_package):
        try:
            for tool in stix_package.stix_header.information_source.tools:
                if (tool.name == const.SNS_TOOL_NAME) and (tool.vendor == const.SNS_TOOL_VENDOR):
                    return True
            return False
        except BaseException:
            return False

    @staticmethod
    def get_attach_stix_dir_path(stix_id):
        # ATTACH_FILE_DIR/{{attach_file_id}}/nameで保存する
        dir_name = rs.convert_package_id_to_filename(stix_id)
        return const.ATTACH_FILE_DIR + dir_name

    @staticmethod
    def get_attach_file_name(stix_id):
        af = AttachFile.objects.get(package_id=stix_id)
        return af.file_name

    @staticmethod
    def get_attach_file_path(stix_id):
        attachment_stix_dir = Feed.get_attach_stix_dir_path(stix_id)
        file_name = Feed.get_attach_file_name(stix_id)
        return attachment_stix_dir + os.sep + file_name

    @staticmethod
    def get_cached_file_path(feed_file_name_id):
        return const.STIX_CACHE_DIR + os.sep + feed_file_name_id

    @staticmethod
    # stix_id が SNS 作成のアタッチメント情報を含まない場合は None を返却する
    def get_attach_file(api_user, stix_id):
        attachment_stix_dir = Feed.get_attach_stix_dir_path(stix_id)
        if os.path.exists(attachment_stix_dir):
            # ここのファイル名とファイルパスを返却する　
            try:
                # 1dir 1file なので最初の要素をファイル名とする
                attach_file = AttachFile()
                attach_file.file_name = Feed.get_attach_file_name(stix_id)
                attach_file.package_id = stix_id
                attach_file.save()
                return attach_file
            except IndexError:
                # dir はあるが fileが存在しない場合に発生する
                # 処理は続行する
                pass
        else:
            # dir が存在しないので作成
            os.mkdir(attachment_stix_dir)

        attachement_cached_stix_file_path = rs.get_stix_file_path(api_user, stix_id)
        try:
            # Attachement STIX Package parse
            attachement_stix_package = STIXPackage.from_xml(attachement_cached_stix_file_path)
            # marking から file_name, content 取得
            file_name = None
            content = None
            try:
                markings = attachement_stix_package.stix_header.handling.marking
            except AttributeError:
                return None

            for marking in markings:
                marking_structure = marking.marking_structures[0]
                if isinstance(marking_structure, SimpleMarkingStructure):
                    statement = marking_structure.statement
                    if statement.startswith(const.MARKING_STRUCTURE_STIP_ATTACHEMENT_FILENAME_PREFIX):
                        file_name = statement[len(const.MARKING_STRUCTURE_STIP_ATTACHEMENT_FILENAME_PREFIX + ': '):]
                    elif statement.startswith(const.MARKING_STRUCTURE_STIP_ATTACHEMENT_CONTENT_PREFIX):
                        content_str = statement[len(const.MARKING_STRUCTURE_STIP_ATTACHEMENT_CONTENT_PREFIX + ': '):]
                        # content は base64 で decode する
                        content = base64.b64decode(content_str)
            if (file_name is None) or (content is None):
                return None
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

        # ファイル保存
        file_path = attachment_stix_dir + os.sep + file_name
        with open(file_path, 'wb') as fp:
            fp.write(content)
        attach_file = AttachFile()
        attach_file.file_name = file_name
        attach_file.package_id = stix_id
        attach_file.save()
        return attach_file

    @staticmethod
    # string から datetime 型を取得する
    def get_datetime_from_string(s):
        try:
            return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.utc)
        except ValueError:
            return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)

    class StipInformationFromStix:
        def __init__(self):
            self.user_name = None
            self.screen_name = None
            self.affiliation = None
            self.instance = None
            self.is_sns = False
            self.region_code = None
            self.ci = None
            self.referred_url = None
            self.country_code = None
            self.administrative_code = None
            self.stix2_package_id = None

    # stix_package の user_name取得
    @staticmethod
    def get_stip_from_stix_package(stix_package):
        bean = Feed.StipInformationFromStix()
        bean.is_sns = Feed.is_stip_sns_stix_package(stix_package)
        try:
            for marking in stix_package.stix_header.handling:
                if isinstance(marking, MarkingSpecification):
                    marking_structure = marking.marking_structures[0]
                    if isinstance(marking_structure, SimpleMarkingStructure):
                        statement = marking_structure.statement
                        if statement.startswith(Feed.STIP_SNS_USER_NAME_PREFIX):
                            bean.user_name = statement[len(Feed.STIP_SNS_USER_NAME_PREFIX):]
                        if statement.startswith(Feed.STIP_SNS_SCREEN_NAME_PREFIX):
                            bean.screen_name = statement[len(Feed.STIP_SNS_SCREEN_NAME_PREFIX):]
                        if statement.startswith(Feed.STIP_SNS_AFFILIATION_PREFIX):
                            bean.affiliation = statement[len(Feed.STIP_SNS_AFFILIATION_PREFIX):]
                        if statement.startswith(Feed.STIP_SNS_REGION_CODE_PREFIX):
                            bean.region_code = statement[len(Feed.STIP_SNS_REGION_CODE_PREFIX):]
                        if statement.startswith(Feed.STIP_SNS_CI_PREFIX):
                            bean.ci = statement[len(Feed.STIP_SNS_CI_PREFIX):]
                        if statement.startswith(Feed.STIP_SNS_REFERRED_URL_PREFIX):
                            bean.referred_url = statement[len(Feed.STIP_SNS_REFERRED_URL_PREFIX):]
                        if statement.startswith(Feed.STIP_SNS_STIX2_PACKAGE_ID_PREFIX):
                            bean.stix2_package_id = statement[len(Feed.STIP_SNS_STIX2_PACKAGE_ID_PREFIX):]
                    # AISMarkingStructure から country_code と administrative_area を取得する
                    elif isinstance(marking_structure, AISMarkingStructure):
                        information_source = marking.information_source
                        identity = information_source.identity
                        specification = identity.specification
                        addresses = specification.addresses
                        address = addresses[0]
                        # country_code
                        country = address.country
                        name_elements = country.name_elements
                        name_element = name_elements[0]
                        country_code = name_element.name_code
                        bean.country_code = country_code
                        # administrative_area
                        administrative_area = address.administrative_area
                        name_elements = administrative_area.name_elements
                        name_element = name_elements[0]
                        administrative_code = name_element.name_code
                        bean.administrative_code = administrative_code

        except BaseException:
            pass
        try:
            bean.instance = stix_package.stix_header.information_source.identity.name
        except BaseException:
            pass
        return bean

    @staticmethod
    def set_screen_value_from_local_db(feed, bean):
        # 上書きロジックは stix と同一とする
        Feed.set_screen_value_from_stix(feed, bean)

    @staticmethod
    def set_screen_value_from_stix(feed, bean):
        stip_user = feed.user
        # STIX の情報から取得するが存在しない場合は db 格納値を用いる
        if bean.screen_name is not None and len(bean.screen_name) != 0:
            feed.screen_name = bean.screen_name
        else:
            feed.screen_name = stip_user.screen_name

        if bean.affiliation is not None and len(bean.affiliation) != 0:
            feed.screen_affiliation = bean.affiliation
        else:
            feed.screen_affiliation = stip_user.affiliation if stip_user.affiliation is not None else ''

        if bean.instance is not None and len(bean.instance) != 0:
            feed.screen_instance = bean.instance
        else:
            feed.screen_instance = ''

        if bean.country_code is not None and len(bean.country_code) != 0:
            feed.country_code = bean.country_code
        else:
            feed.country_code = stip_user.country_code

        if bean.administrative_code is not None and len(bean.administrative_code) != 0:
            feed.administrative_code = bean.administrative_code
        else:
            feed.administrative_code = stip_user.administrative_code
        return

    @staticmethod
    # N/A アカウントを取得する
    def get_na_account():
        return STIPUser.objects.get(username=const.SNS_NA_ACCOUNT)

    # cache 作成
    @staticmethod
    def create_feeds_record(api_user, package_id, uploader_id, produced_str):
        # RS から取得した STIX から stix_package 取得する
        stix_file_path = rs.get_stix_file_path(api_user, package_id)
        stix_package = STIXPackage.from_xml(stix_file_path, encoding='utf-8')

        # Feed情報を STIX,RS の API から取得する
        feed = Feed()
        feed.package_id = package_id
        feed.filename_pk = rs.convert_package_id_to_filename(package_id)

        # STIX から表示情報を取得する
        bean = Feed.get_stip_from_stix_package(stix_package)
        if bean.is_sns:
            # SNS 産 STIX である
            if bean.instance == SNSConfig.get_sns_identity_name():
                # 現在稼働中インスタンスと同一
                try:
                    # STIX 定義の username が存在する
                    feed.user = STIPUser.objects.get(username=bean.user_name)
                    # 表示はローカル DB から取得する
                    Feed.set_screen_value_from_local_db(feed, bean)
                except BaseException:
                    # STIX 定義の username が存在しない → N/A アカウント
                    feed.user = Feed.get_na_account()
                    # 表示はSTIX File から取得する
                    Feed.set_screen_value_from_stix(feed, bean)
                    # すでにユーザーが削除されている
                    feed.is_valid_user = False
            else:
                # 現在稼働中インスタンスと異なる
                try:
                    # インスタンス名と同じアカウント
                    feed.user = STIPUser.objects.get(username=bean.instance)
                    # 表示はSTIX File から取得する
                    Feed.set_screen_value_from_stix(feed, bean)
                except BaseException:
                    # インスタンス名と同じアカウントが存在しない → N/A アカウント
                    feed.user = Feed.get_na_account()
                    # 表示はSTIX File から取得する
                    Feed.set_screen_value_from_stix(feed, bean)
        else:
            # SNS 産 STIX ではない
            if bean.instance is not None:
                # instance がある
                instance_user_name = bean.instance.replace(' ', '')
                try:
                    # インスタンス名と同じアカウント
                    feed.user = STIPUser.objects.get(username=instance_user_name)
                    # 表示はローカル DB から取得する
                    Feed.set_screen_value_from_local_db(feed, bean)
                except BaseException:
                    # インスタンス名と同じアカウントが存在しない → N/A アカウント
                    feed.user = Feed.get_na_account()
                    # 表示は bean.instance [bean.instance]
                    feed.screen_name = bean.instance
                    feed.screen_instance = bean.instance
            else:
                # instance がない
                # N/A アカウント
                feed.user = Feed.get_na_account()
                # 表示はローカル DB(N/Aアカウント) から取得する
                Feed.set_screen_value_from_local_db(feed, bean)

        feed.date = Feed.get_datetime_from_string(produced_str)
        feed.post = stix_package.stix_header.description
        if feed.post is None:
            feed.post = ''

        # Attachement Files 情報取得
        if Feed.is_stip_sns_stix_package(stix_package):
            # S-TIP SNS 作成 STIX
            if stix_package.related_packages is not None:
                # 一度 feed をsave()する
                feed.save()
                # Related_packages は SNS STIX 以外の可能性もある
                for related_package in stix_package.related_packages:
                    # attachement は attachdirにいれるべきその時のファイル名は attachment_stix_idであるべき
                    attach_file = Feed.get_attach_file(api_user, related_package.item.id_)
                    # attach_file が None の場合は Attach File ではない
                    if attach_file is None:
                        continue
                    feed.files.add(attach_file)
                feed.save()

        feed.title = stix_package.stix_header.title
        feed.stix_file_path = stix_file_path
        try:
            uploader_stipuser = STIPUser.objects.get(id=uploader_id)
            feed.tlp = Feed.get_tlp_from_stix_header(stix_package.stix_header, uploader_stipuser.tlp)
            if feed.tlp is None:
                # 取得ができなかった場合は ユーザーアカウントの default TLP
                feed.tlp = uploader_stipuser.tlp
        except BaseException:
            # uploader_profile が存在しない場合は default TLP の AMBER
            feed.tlp = 'AMBER'
        sharing_range_info = Feed.get_sharing_range_from_stix_header(stix_package.stix_header)
        if isinstance(sharing_range_info, list):
            # sharing_range_info の中は STIPUser list
            feed.sharing_range_type = const.SHARING_RANGE_TYPE_KEY_PEOPLE
            feed.save()
            for stip_user in sharing_range_info:
                feed.sharing_people.add(stip_user)
        elif isinstance(sharing_range_info, Group):
            feed.sharing_range_type = const.SHARING_RANGE_TYPE_KEY_GROUP
            feed.sharing_group = sharing_range_info
        else:
            feed.sharing_range_type = const.SHARING_RANGE_TYPE_KEY_ALL
        # feed.package_id = package_id
        if bean.region_code is not None:
            feed.region_code = bean.region_code
        else:
            if feed.user.region is not None:
                feed.region_code = feed.user.region.code
            else:
                feed.region_code = ''
        if bean.ci is not None:
            feed.ci = bean.ci
        else:
            feed.ci = feed.user.ci
        if bean.referred_url is not None:
            feed.referred_url = bean.referred_url
        if bean.stix2_package_id is not None:
            feed.stix2_package_id = bean.stix2_package_id
        feed.save()
        return feed

    # rs の API の復帰値の json から Feedを取得する
    @staticmethod
    def get_feeds_from_package_from_rs(api_user, package_from_rs):
        package_id = package_from_rs['package_id']
        uploader_id = package_from_rs['uploader']
        produced_str = package_from_rs['produced']

        try:
            # cache にあれば採用する
            feed = Feed.objects.get(package_id=package_id)
            # STIX の instance がこの稼働している instance と同じであるかチェック
            if feed.screen_instance is not None:
                if feed.screen_instance == SNSConfig.get_sns_identity_name():
                    # feed.user の現在の affiliation/screen_name/ci/region_codeを使用する
                    feed.screen_name = feed.user.screen_name
                    feed.screen_affiliation = feed.user.affiliation
                    feed.ci = feed.user.ci
                    if feed.user.region is not None:
                        feed.region_code = feed.user.region.code
        except Feed.DoesNotExist as e:
            # cache 作成
            feed = Feed.create_feeds_record(api_user, package_id, uploader_id, produced_str)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
        return feed

    @staticmethod
    def add_like_comment_info(api_user, feed):
        # like, comment の情報は　リアルタイム更新のため都度取得する
        # likes 数を RS から取得
        likers = rs.get_likers_from_rs(api_user, feed.package_id)
        feed.likes = len(likers)

        # like status 取得
        mylike = '%s %s' % (SNSConfig.get_sns_identity_name(), api_user)
        feed.like = mylike in likers

        # comment 数を RS から取得
        feed.comments = len(rs.get_comment_from_rs(api_user, feed.package_id))
        # feed.save()
        return feed

    @staticmethod
    # RS に query をかける
    def query(
            api_user=None,
            query_string=''):
        feeds_ = []
        # RS に queryする
        packages_from_rs = rs.query(api_user, query_string)
        for package_from_rs in packages_from_rs:
            feed = Feed.get_feeds_from_package_from_rs(api_user, package_from_rs)
            feeds_.append(feed)
        return feeds_

    @staticmethod
    def get_feeds(
            api_user=None,
            last_reload=None,  # last_reload 指定の場合はこの時間を最新として、それより古い投稿を探す (時間ピッタリは含まない)
            last_feed_datetime=None,  # last_feed_datetime 指定の場合は、この時間を起点とし、新しい投稿を探す (時間ピッタリは含まない)
            range_small_datetime=None,  # 期間範囲指定の小さい方(古い方)。この時間を含む
            range_big_datetime=None,  # 期間範囲指定の大きい方(新しい方)。この時間を含む
            index=0,
            size=-1,
            user_id=None):

        # Feed cache 作成 (起動時初回のみ cache 作成を行う)
        if not Feed.build_cache_flag:
            Feed.build_cache(api_user)
            Feed.build_cache_flag = True

        # rs から取得
        if last_feed_datetime is None:
            # start_time を最新として古い投稿を取得
            packages_from_rs = rs.get_feeds_from_rs(
                api_user,
                start_time=last_reload,
                user_id=user_id,
                range_small_datetime=range_small_datetime,
                range_big_datetime=range_big_datetime,
                index=index,
                size=size)
        else:
            # last_feed_datetime より新しい投稿を取得
            packages_from_rs = rs.get_feeds_from_rs(
                api_user,
                last_feed_datetime=last_feed_datetime,
                user_id=user_id,
                range_small_datetime=range_small_datetime,
                range_big_datetime=range_big_datetime,
                index=index,
                size=size)

        feeds_ = []
        for package_from_rs in packages_from_rs:
            # RS 復帰の json を元に Feed 構築する
            feed = Feed.get_feeds_from_package_from_rs(api_user, package_from_rs)
            # 条件を満たした feed を追加
            feeds_.append(feed)
        return Feed.get_filter_query_set(None, api_user, feeds_=feeds_)

    # stix_header から 標準 の TLP を返却する。該当箇所がない場合はdefault_tlpを返却
    @staticmethod
    def get_tlp_from_stix_header(stix_header, default_tlp='AMBER'):
        try:
            for marking in stix_header.handling.marking:
                marking_strucutre = marking.marking_structures[0]
                if isinstance(marking_strucutre, TLPMarkingStructure):
                    return marking_strucutre.color
        except BaseException:
            pass
        return default_tlp

    # stix_header から sharing_rangeを返却
    # group 指定の場合はGroupインスタンス
    # people 指定の場合は文字列のリスト
    # それ以外の場合はNoneを返却する
    @staticmethod
    def get_sharing_range_from_stix_header(stix_header):
        SHARING_RANGE_PREFIX = 'Sharing Range:'
        SHARING_RANGE_ALL_VALUE = 'Sharing Range: CIC Community'
        SHARING_RANGE_GROUP_PREFIX = 'Sharing Range: Group: '
        SHARING_RANGE_PEOPLE_PREFIX = 'Sharing Range: People: '
        try:
            for marking in stix_header.handling.marking:
                marking_structure = marking.marking_structures[0]
                if isinstance(marking_structure, SimpleMarkingStructure):
                    statement = marking_structure.statement
                    if not statement.startswith(SHARING_RANGE_PREFIX):
                        continue
                    if statement == SHARING_RANGE_ALL_VALUE:
                        # Sharing Range指定 が ALL
                        return None
                    if statement.startswith(SHARING_RANGE_GROUP_PREFIX):
                        # Sharing Range指定 が Group
                        group_name = statement[len(SHARING_RANGE_GROUP_PREFIX):]
                        group = Group.objects.get(en_name=group_name)
                        return group
                    if statement.startswith(SHARING_RANGE_PEOPLE_PREFIX):
                        # Sharing Range指定 が People
                        people_str = statement[len(SHARING_RANGE_GROUP_PREFIX):]
                        people_list = []
                        for p_str in people_str.split(','):
                            people = STIPUser.objects.get(username=p_str.strip())
                            people_list.append(people)
                        return people_list

        except BaseException:
            pass
        # 指定がない。None
        return None

    @staticmethod
    def get_feeds_after(last_feed_datetime, api_user=None, user_id=None):
        feeds_ = Feed.get_feeds(last_feed_datetime=last_feed_datetime, api_user=api_user, user_id=user_id)
        return Feed.get_filter_query_set(None, api_user, feeds_=feeds_)
