import bleach
import datetime
import pytz
import os
import base64
import shutil
import json
import traceback
from . import rs
from django.db import models
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


class Feed(models.Model):
    STIP_SNS_USER_NAME_PREFIX = const.STIP_SNS_USER_NAME_KEY + ': '
    STIP_SNS_SCREEN_NAME_PREFIX = const.STIP_SNS_SCREEN_NAME_KEY + ': '
    STIP_SNS_AFFILIATION_PREFIX = const.STIP_SNS_AFFILIATION_KEY + ': '
    STIP_SNS_REGION_CODE_PREFIX = const.STIP_SNS_REGION_CODE_KEY + ': '
    STIP_SNS_CI_PREFIX = const.STIP_SNS_CI_KEY + ': '
    STIP_SNS_REFERRED_URL_PREFIX = const.STIP_SNS_REFERRED_URL_KEY + ': '
    STIP_SNS_STIX2_PACKAGE_ID_PREFIX = const.STIP_SNS_STIX2_PACKAGE_ID_KEY + ': '

    package_id = models.CharField(max_length=128, primary_key=True)
    user = models.ForeignKey(STIPUser, on_delete=models.CASCADE)
    date = models.DateTimeField(null=True)
    post = models.TextField(max_length=1024)
    post_org = models.TextField(max_length=1024, default='')
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    files = models.ManyToManyField(AttachFile)
    title = models.TextField(max_length=1024, default=None, null=True)
    stix_file_path = models.FilePathField(max_length=1024, default=None, null=True)
    tlp = models.CharField(max_length=10, choices=const.TLP_CHOICES, default='AMBER')
    sharing_range_type = models.CharField(max_length=10, choices=const.SHARING_RANGE_CHOICES, default=const.SHARING_RANGE_TYPE_KEY_ALL)
    sharing_people = models.ManyToManyField(STIPUser, related_name='feed_sharing_people')
    sharing_group = models.ForeignKey(Group, default=None, null=True, on_delete=models.CASCADE)
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
    stix_version = models.CharField(max_length=8, default='1.2', null=True)
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
    def build_cache(api_user):
        packages_from_rs = rs.get_feeds_from_rs(
            api_user,
            index=0,
            size=-1)
        for package_from_rs in packages_from_rs:
            Feed.get_feeds_from_package_from_rs(api_user, package_from_rs)

    @staticmethod
    def get_filter_query_set(feeds, request_user, feeds_=None):
        if feeds_ is None:
            return []

        list_ = []
        for feed_ in feeds_:
            if request_user is not None:
                if request_user == feed_.user:
                    list_.append(feed_)
                    continue
            if feed_.sharing_range_type == const.SHARING_RANGE_TYPE_KEY_ALL:
                list_.append(feed_)
                continue
            elif feed_.sharing_range_type == const.SHARING_RANGE_TYPE_KEY_GROUP:
                if request_user is not None:
                    if len(feed_.sharing_group.members.filter(username=request_user)) == 1:
                        list_.append(feed_)
                        continue
            elif feed_.sharing_range_type == const.SHARING_RANGE_TYPE_KEY_PEOPLE:
                if request_user is not None:
                    if request_user in feed_.sharing_people.all():
                        list_.append(feed_)
                        continue
        return list_

    @staticmethod
    def get_feeds_from_package_id(api_user, package_id):
        package_from_rs = rs.get_package_info_from_package_id(api_user, package_id)
        return Feed.get_feeds_from_package_from_rs(api_user, package_from_rs)

    @staticmethod
    def is_stip_sns_stix_package_v2(bundle):
        if 'objects' not in bundle:
            return False, None
        try:
            count = 0
            stip_sns = None
            for o_ in bundle['objects']:
                if o_['type'] == const.STIP_STIX2_X_STIP_SNS_TYPE:
                    stip_sns = o_
                    count += 1
            if count == 1:
                return True, stip_sns
            else:
                return False, None
        except BaseException:
            return False, None

    @staticmethod
    def is_stip_sns_stix_package_v1(stix_package):
        try:
            for tool in stix_package.stix_header.information_source.tools:
                if (tool.name == const.SNS_TOOL_NAME) and (tool.vendor == const.SNS_TOOL_VENDOR):
                    return True
            return False
        except BaseException:
            return False

    @staticmethod
    def get_attach_stix_dir_path(stix_id):
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
    def get_attach_file(api_user, stix_id, version):
        attachment_stix_dir = Feed.get_attach_stix_dir_path(stix_id)
        if os.path.exists(attachment_stix_dir):
            try:
                attach_file = AttachFile()
                attach_file.file_name = Feed.get_attach_file_name(stix_id)
                attach_file.package_id = stix_id
                attach_file.save()
                return attach_file
            except IndexError:
                pass
        else:
            os.mkdir(attachment_stix_dir)

        attachement_cached_stix_file_path = rs.get_stix_file_path(api_user, stix_id)
        try:
            if version.startswith('v1'):
                attachement_stix_package = STIXPackage.from_xml(attachement_cached_stix_file_path)
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
                            content = base64.b64decode(content_str)
                if (file_name is None) or (content is None):
                    return None
            elif version.startswith('v2'):
                with open(attachement_cached_stix_file_path, 'r', encoding='utf-8') as fp:
                    attachment_bundle = json.load(fp)
                file_name = None
                content = None
                for o_ in attachment_bundle['objects']:
                    if o_['type'] != const. STIP_STIX2_X_STIP_SNS_TYPE:
                        continue
                    if o_[const.STIP_STIX2_PROP_TYPE] != const.STIP_STIX2_SNS_POST_TYPE_ATTACHMENT:
                        continue
                    stip_sns_attachment = o_[const.STIP_STIX2_PROP_ATTACHMENT]
                    content_str = stip_sns_attachment[const.STIP_STIX2_SNS_ATTACHMENT_CONTENT_KEY]
                    content = base64.b64decode(content_str)
                    file_name = stip_sns_attachment[const.STIP_STIX2_SNS_ATTACHMENT_FILENAME_KEY]
                    break
                if (file_name is None) or (content is None):
                    return None
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

        file_path = attachment_stix_dir + os.sep + file_name
        file_path = file_path.encode('utf-8')
        with open(file_path, 'wb') as fp:
            fp.write(content)
        attach_file = AttachFile()
        attach_file.file_name = file_name
        attach_file.package_id = stix_id
        attach_file.save()
        return attach_file

    @staticmethod
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
            self.tool = None
            self.is_sns = False
            self.region_code = None
            self.ci = None
            self.referred_url = None
            self.country_code = None
            self.administrative_code = None
            self.stix2_package_id = None
            self.sharing_range = None

    @staticmethod
    def get_stip_from_stix_package_v2(bundle):
        bean = Feed.StipInformationFromStix()
        bean.is_sns, stip_sns = Feed.is_stip_sns_stix_package_v2(bundle)

        if stip_sns:
            if const.STIP_STIX2_PROP_AUTHOR in stip_sns:
                sns_author = stip_sns[const.STIP_STIX2_PROP_AUTHOR]
                if const.STIP_STIX2_SNS_AUTHOR_USER_NAME_KEY in sns_author:
                    bean.user_name = sns_author[const.STIP_STIX2_SNS_AUTHOR_USER_NAME_KEY]
                if const.STIP_STIX2_SNS_AUTHOR_SCREEN_NAME_KEY in sns_author:
                    bean.screen_name = sns_author[const.STIP_STIX2_SNS_AUTHOR_SCREEN_NAME_KEY]
                if const.STIP_STIX2_SNS_AUTHOR_AFFILIATION_KEY in sns_author:
                    bean.affiliation = sns_author[const.STIP_STIX2_SNS_AUTHOR_AFFILIATION_KEY]
                if const.STIP_STIX2_SNS_AUTHOR_REGION_CODE_KEY in sns_author:
                    bean.region_code = sns_author[const.STIP_STIX2_SNS_AUTHOR_REGION_CODE_KEY]
                    bean.administrative_area = sns_author[const.STIP_STIX2_SNS_AUTHOR_REGION_CODE_KEY]
                if const.STIP_STIX2_SNS_AUTHOR_COUNTRY_CODE_KEY in sns_author:
                    bean.country_code = sns_author[const.STIP_STIX2_SNS_AUTHOR_COUNTRY_CODE_KEY]
                if const.STIP_STIX2_SNS_AUTHOR_CI_KEY in sns_author:
                    bean.ci = sns_author[const.STIP_STIX2_SNS_AUTHOR_CI_KEY]
            if const.STIP_STIX2_PROP_POST in stip_sns:
                sns_post = stip_sns[const.STIP_STIX2_PROP_POST]
                if const.STIP_STIX2_SNS_POST_REFERRED_URL_KEY in sns_post:
                    if len(sns_post[const.STIP_STIX2_SNS_POST_REFERRED_URL_KEY]) != 0:
                        bean.referred_url = sns_post[const.STIP_STIX2_SNS_POST_REFERRED_URL_KEY]
                if const.STIP_STIX2_SNS_POST_SHARING_RANGE_KEY in sns_post:
                    bean.sharing_range = sns_post[const.STIP_STIX2_SNS_POST_SHARING_RANGE_KEY]
            if const.STIP_STIX2_PROP_IDENTITY in stip_sns:
                bean.instance = stip_sns[const.STIP_STIX2_PROP_IDENTITY]
        return bean, stip_sns

    @staticmethod
    def get_stip_from_stix_package_v1(stix_package):
        bean = Feed.StipInformationFromStix()
        bean.is_sns = Feed.is_stip_sns_stix_package_v1(stix_package)
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
                    elif isinstance(marking_structure, AISMarkingStructure):
                        information_source = marking.information_source
                        identity = information_source.identity
                        specification = identity.specification
                        addresses = specification.addresses
                        address = addresses[0]
                        country = address.country
                        name_elements = country.name_elements
                        name_element = name_elements[0]
                        country_code = name_element.name_code
                        bean.country_code = country_code
                        administrative_area = address.administrative_area
                        name_elements = administrative_area.name_elements
                        name_element = name_elements[0]
                        administrative_code = name_element.name_code
                        bean.administrative_code = administrative_code

        except BaseException:
            pass

        information_source = stix_package.stix_header.information_source
        try:
            bean.instance = information_source.identity.name
            return bean
        except AttributeError:
            pass

        if not hasattr(information_source, 'contributing_sources'):
            return bean

        contributing_sources = information_source.contributing_sources
        if not contributing_sources:
            return bean
        for cs in contributing_sources:
            if hasattr(cs, 'identity') and hasattr(cs, 'tools'):
                bean.instance = None
                bean.tool = None
                try:
                    bean.instance = cs.identity.specification.party_name.organisation_names[0].name_elements[0].value
                except Exception:
                    traceback.print_exc()
                    pass
                try:
                    bean.tool = cs.tools[0].metadata[0].value
                except Exception:
                    traceback.print_exc()
                    pass
                break
        return bean

    @staticmethod
    def set_screen_value_from_local_db(feed, bean):
        Feed.set_screen_value_from_stix(feed, bean)

    @staticmethod
    def set_screen_value_from_stix(feed, bean):
        stip_user = feed.user
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
    def get_na_account():
        return STIPUser.objects.get(username=const.SNS_NA_ACCOUNT)

    @staticmethod
    def create_feeds_record(api_user, package_id, uploader_id, produced_str, version):
        if version.startswith('1.'):
            return Feed.create_feeds_record_v1(
                api_user, package_id,
                uploader_id, produced_str, version)
        if version.startswith('2.'):
            return Feed.create_feeds_record_v2(
                api_user, package_id,
                uploader_id, produced_str, version)

    @staticmethod
    def get_reports_and_identities(bundle):
        reports = []
        identities = []
        for o_ in bundle['objects']:
            try:
                if o_['type'] == 'report':
                    reports.append(o_)
                elif o_['type'] == 'identity':
                    identities.append(o_)
            except KeyError:
                None
        return reports, identities

    @staticmethod
    def create_feeds_record_v2(api_user, package_id, uploader_id, produced_str, version, feed=None):
        stix_file_path = rs.get_stix_file_path(api_user, package_id)
        with open(stix_file_path, 'r', encoding='utf-8') as fp:
            bundle = json.load(fp)
        if 'objects' not in bundle:
            return None
        if not feed:
            feed = Feed()
        feed.stix_version = version
        package_id = bundle['id']
        feed.package_id = package_id
        feed.filename_pk = package_id

        bean, stip_sns = Feed.get_stip_from_stix_package_v2(bundle)

        if bean.is_sns:
            if bean.instance == SNSConfig.get_sns_identity_name():
                try:
                    feed.user = STIPUser.objects.get(username=bean.user_name)
                    Feed.set_screen_value_from_local_db(feed, bean)
                except BaseException:
                    feed.user = Feed.get_na_account()
                    Feed.set_screen_value_from_stix(feed, bean)
                    feed.is_valid_user = False
            else:
                try:
                    feed.user = STIPUser.objects.get(username=bean.instance)
                    Feed.set_screen_value_from_stix(feed, bean)
                except BaseException:
                    feed.user = Feed.get_na_account()
                    Feed.set_screen_value_from_stix(feed, bean)
        else:
            reports, identities = Feed.get_reports_and_identities(bundle)

            is_found = False
            if len(identities) > 0:
                for identity in identities:
                    if 'name' in identity:
                        try:
                            feed.user = STIPUser.objects.get(username=identity['name'])
                            is_found = True
                            Feed.set_screen_value_from_local_db(feed, bean)
                            break
                        except STIPUser.DoesNotExist:
                            pass
            if not is_found:
                feed.user = Feed.get_na_account()
                Feed.set_screen_value_from_local_db(feed, bean)
                feed.screen_instance = bean.instance

        feed.date = Feed.get_datetime_from_string(produced_str)

        if stip_sns:
            if 'description' in stip_sns:
                feed.post_org = feed.post = stip_sns['description']
            else:
                feed.post_org = feed.post = ''
            if 'name' in stip_sns:
                feed.title = stip_sns['name']
            else:
                feed.title = ''
            if const.STIP_STIX2_PROP_POST in stip_sns:
                sns_post = stip_sns[const.STIP_STIX2_PROP_POST]
                feed.tlp = sns_post['tlp']
                sharing_range = sns_post[const.STIP_STIX2_SNS_POST_SHARING_RANGE_KEY]
                if sharing_range.startswith('Group:'):
                    group_name = sharing_range.split(':')[1].strip()
                    sharing_range_info = Group.objects.get(
                        en_name=group_name)
                elif sharing_range.startswith('People:'):
                    people_list = []
                    accounts = sharing_range.split(':')[1].strip()
                    for account in accounts.split(','):
                        try:
                            people = STIPUser.objects.get(
                                username=account.strip())
                            people_list.append(people)
                        except STIPUser.DoesNotExist:
                            pass
                        sharing_range_info = people_list
                else:
                    sharing_range_info = None
            else:
                feed.tlp = None
                sharing_range_info = None
        else:
            feed.post_org = feed.post = None
            for report in reports:
                if 'description' in report:
                    feed.post_org = feed.post = report['description']
                    break
            if not feed.post_org:
                feed.post_org = 'Post, %s' % (feed.package_id)
            if not feed.post:
                feed.post = 'Post, %s' % (feed.package_id)
            feed.title = None
            for report in reports:
                if 'name' in report:
                    feed.title = report['name']
                    break
            if not feed.title:
                feed.title = package_id
            feed.tlp = None
            sharing_range_info = None

        if stip_sns:
            if const.STIP_STIX2_PROP_ATTACHMENTS in stip_sns:
                attach_refs = stip_sns[const.STIP_STIX2_PROP_ATTACHMENTS]
            elif const.STIP_STIX2_PROP_ATTACHMENT_REFS in stip_sns:
                attach_refs = stip_sns[const.STIP_STIX2_PROP_ATTACHMENT_REFS]
            else:
                attach_refs = []
            if len(attach_refs) != 0:
                for attach in attach_refs:
                    feed.save()
                    attach_bundle_id = attach['bundle']
                    attach_file = Feed.get_attach_file(
                        api_user,
                        attach_bundle_id,
                        'v2')
                    if attach_file:
                        feed.files.add(attach_file)
                feed.save()
        feed.stix_file_path = stix_file_path

        if not feed.tlp:
            feed.tlp = feed.user.tlp

        if isinstance(sharing_range_info, list):
            feed.sharing_range_type = const.SHARING_RANGE_TYPE_KEY_PEOPLE
            feed.save()
            for stip_user in sharing_range_info:
                feed.sharing_people.add(stip_user)
        elif isinstance(sharing_range_info, Group):
            feed.sharing_range_type = const.SHARING_RANGE_TYPE_KEY_GROUP
            feed.sharing_group = sharing_range_info
        else:
            feed.sharing_range_type = const.SHARING_RANGE_TYPE_KEY_ALL

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

    @staticmethod
    def create_feeds_record_v1(api_user, package_id, uploader_id, produced_str, version):
        stix_file_path = rs.get_stix_file_path(api_user, package_id)
        stix_package = STIXPackage.from_xml(stix_file_path)

        feed = Feed()
        feed.stix_version = version
        feed.package_id = package_id
        feed.filename_pk = rs.convert_package_id_to_filename(package_id)

        bean = Feed.get_stip_from_stix_package_v1(stix_package)
        if bean.is_sns:
            if bean.instance == SNSConfig.get_sns_identity_name():
                try:
                    feed.user = STIPUser.objects.get(username=bean.user_name)
                    Feed.set_screen_value_from_local_db(feed, bean)
                except BaseException:
                    feed.user = Feed.get_na_account()
                    Feed.set_screen_value_from_stix(feed, bean)
                    feed.is_valid_user = False
            else:
                try:
                    feed.user = STIPUser.objects.get(username=bean.instance)
                    Feed.set_screen_value_from_stix(feed, bean)
                except BaseException:
                    feed.user = Feed.get_na_account()
                    Feed.set_screen_value_from_stix(feed, bean)
        else:
            def _get_match_stip_user(username):
                try:
                    username = username.replace(' ', '')
                    return STIPUser.objects.get(username=username)
                except STIPUser.DoesNotExist:
                    return None
                except Exception as e:
                    raise e

            def _get_match_stip_user_from_bean(bean):
                ret_instance = None
                ret_tool = None
                if bean.instance:
                    ret_instance = bean.instance
                    stip_user = _get_match_stip_user(bean.instance)
                    if stip_user:
                        return stip_user, bean.instance
                if bean.tool:
                    ret_tool = bean.tool
                    stip_user = _get_match_stip_user(bean.tool)
                    if stip_user:
                        return stip_user, bean.tool
                if ret_instance:
                    return None, ret_instance
                else:
                    return None, ret_tool

            feed_user, screen_instance = _get_match_stip_user_from_bean(bean)
            if feed_user:
                feed.user = feed_user
                Feed.set_screen_value_from_local_db(feed, bean)
                feed.screen_instance = screen_instance
            else:
                feed.user = Feed.get_na_account()
                if screen_instance:
                    feed.screen_name = screen_instance
                    feed.screen_instance = screen_instance
                else:
                    Feed.set_screen_value_from_local_db(feed, bean)

        feed.date = Feed.get_datetime_from_string(produced_str)
        feed.post_org = feed.post = stix_package.stix_header.description
        if not feed.post_org:
            feed.post_org = ''
        if not feed.post:
            feed.post = ''

        if Feed.is_stip_sns_stix_package_v1(stix_package):
            if stix_package.related_packages is not None:
                feed.save()
                for related_package in stix_package.related_packages:
                    attach_file = Feed.get_attach_file(
                        api_user,
                        related_package.item.id_,
                        'v1')
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
                feed.tlp = uploader_stipuser.tlp
        except BaseException:
            feed.tlp = 'AMBER'
        sharing_range_info = Feed.get_sharing_range_from_stix_header(stix_package.stix_header)
        if isinstance(sharing_range_info, list):
            feed.sharing_range_type = const.SHARING_RANGE_TYPE_KEY_PEOPLE
            feed.save()
            for stip_user in sharing_range_info:
                feed.sharing_people.add(stip_user)
        elif isinstance(sharing_range_info, Group):
            feed.sharing_range_type = const.SHARING_RANGE_TYPE_KEY_GROUP
            feed.sharing_group = sharing_range_info
        else:
            feed.sharing_range_type = const.SHARING_RANGE_TYPE_KEY_ALL
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

    @staticmethod
    def get_feeds_from_package_from_rs(api_user, package_from_rs):
        package_id = package_from_rs['package_id']
        uploader_id = package_from_rs['uploader']
        produced_str = package_from_rs['produced']
        version = package_from_rs['version']

        try:
            feed = Feed.objects.get(package_id=package_id)
            if feed.screen_instance is not None:
                if feed.screen_instance == SNSConfig.get_sns_identity_name():
                    feed.screen_name = feed.user.screen_name
                    feed.screen_affiliation = feed.user.affiliation
                    feed.ci = feed.user.ci
                    if feed.user.region is not None:
                        feed.region_code = feed.user.region.code
        except Feed.DoesNotExist:
            feed = Feed.create_feeds_record(
                api_user,
                package_id,
                uploader_id,
                produced_str,
                version)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
        return feed

    @staticmethod
    def add_like_comment_info(api_user, feed):
        likers = rs.get_likers_from_rs(api_user, feed.package_id)
        feed.likes = len(likers)

        mylike = '%s %s' % (SNSConfig.get_sns_identity_name(), api_user)
        feed.like = mylike in likers

        feed.comments = len(rs.get_comment_from_rs(api_user, feed.package_id))
        return feed

    @staticmethod
    def query(
            api_user=None,
            query_string='',
            size=-1):
        feeds_ = []
        packages_from_rs = rs.query(api_user, query_string, size)
        for package_from_rs in packages_from_rs:
            feed = Feed.get_feeds_from_package_from_rs(api_user, package_from_rs)
            if feed:
                feeds_.append(feed)
        return feeds_

    @staticmethod
    def get_feeds(
            api_user=None,
            last_reload=None,
            last_feed_datetime=None,
            range_small_datetime=None,
            range_big_datetime=None,
            query_string=None,
            index=0,
            size=-1,
            user_id=None):

        if not Feed.build_cache_flag:
            Feed.build_cache(api_user)
            Feed.build_cache_flag = True

        if last_feed_datetime is None:
            packages_from_rs = rs.get_feeds_from_rs(
                api_user,
                start_time=last_reload,
                user_id=user_id,
                range_small_datetime=range_small_datetime,
                range_big_datetime=range_big_datetime,
                query_string=query_string,
                index=index,
                size=size)
        else:
            packages_from_rs = rs.get_feeds_from_rs(
                api_user,
                last_feed_datetime=last_feed_datetime,
                user_id=user_id,
                range_small_datetime=range_small_datetime,
                range_big_datetime=range_big_datetime,
                query_string=query_string,
                index=index,
                size=size)

        feeds_ = []
        for package_from_rs in packages_from_rs:
            feed = Feed.get_feeds_from_package_from_rs(api_user, package_from_rs)
            if feed:
                feeds_.append(feed)
        return Feed.get_filter_query_set(None, api_user, feeds_=feeds_)

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
                        return None
                    if statement.startswith(SHARING_RANGE_GROUP_PREFIX):
                        group_name = statement[len(SHARING_RANGE_GROUP_PREFIX):]
                        group = Group.objects.get(en_name=group_name)
                        return group
                    if statement.startswith(SHARING_RANGE_PEOPLE_PREFIX):
                        people_str = statement[len(SHARING_RANGE_GROUP_PREFIX):]
                        people_list = []
                        for p_str in people_str.split(','):
                            people = STIPUser.objects.get(username=p_str.strip())
                            people_list.append(people)
                        return people_list
        except BaseException:
            pass
        return None

    @staticmethod
    def get_feeds_after(last_feed_datetime, api_user=None, user_id=None):
        feeds_ = Feed.get_feeds(
            last_feed_datetime=last_feed_datetime,
            api_user=api_user,
            user_id=user_id)
        return Feed.get_filter_query_set(None, api_user, feeds_=feeds_)

    @staticmethod
    def delete_record_related_packages(package_id=None):
        try:
            feeds_ = Feed.objects.filter(package_id=package_id)
            attach_package_ids = []
            if feeds_:
                for feed_ in feeds_:
                    for file_ in feed_.files.all():
                        attach_package_ids.append(file_.package_id)
                        from ctirs.core.mongo.documents_stix import StixFiles
                        StixFiles.delete_by_package_id(file_.package_id)
                        file_.delete()
            for attach_package_id in attach_package_ids:
                attach_dir = Feed.get_attach_stix_dir_path(attach_package_id)
                if os.path.isdir(attach_dir):
                    shutil.rmtree(attach_dir)
            Feed.objects.filter(package_id=package_id).delete()
            return
        except Exception as e:
            print(e)
