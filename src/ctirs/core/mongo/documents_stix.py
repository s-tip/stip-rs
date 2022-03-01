import stix2
import json
import pytz
import datetime
import stix2slider
import tempfile
import copy
import stip.common.const as const
from stix2slider.options import initialize_options as sl_init
try:
    from stix2elevator import elevate_file as ELEVATE
except ImportError:
    from stix2elevator import elevate as ELEVATE
from stix2elevator.options import initialize_options as el_init
from stix2elevator.options import set_option_value
from stix2elevator.stix_stepper import step_file
from mongoengine import fields, CASCADE, DoesNotExist
from mongoengine.document import Document
from mongoengine.errors import NotUniqueError
from stix.core.stix_package import STIXPackage
from cybox.objects.file_object import File
from cybox.objects.domain_name_object import DomainName
from cybox.objects.uri_object import URI
from cybox.objects.address_object import Address
from cybox.objects.mutex_object import Mutex
from cybox.objects.network_connection_object import NetworkConnection
from ctirs.core.mongo.documents import Communities, Vias, InformationSources
from ctirs.models.rs.models import System
from ctirs.models.sns.feeds.models import Feed
from ctirs.core.mongo.documents_taxii21_objects import StixObject as TXS21_SO
from ctirs.core.mongo.documents_taxii21_objects import get_modified_from_object, StixManifest
from stip.common.tld import TLD
from stip.common.x_stip_sns import StipSns  # noqa
from stip.common.label import sanitize_id


DESCRIPTION_LENGTH = 10240


def stix2_str_to_datetime(s):
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc)
    except ValueError:
        return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)


class StixFiles(Document):
    NS_S_TIP_NAME = 's-tip'

    VERSION_CHOICES = (
        ('1.1.1', '1.1.1'),
        ('1.2', '1.1.1'),
        ('2.0', '2.0'),
        ('2.1', '2.1'),
    )

    STIP_SNS_TYPE_ORIGIN = 'origin'
    STIP_SNS_TYPE_V2_POST = const.STIP_STIX2_SNS_POST_TYPE_POST
    STIP_SNS_TYPE_LIKE = 'like'
    STIP_SNS_TYPE_UNLIKE = 'unlike'
    STIP_SNS_TYPE_COMMENT = 'comment'
    STIP_SNS_TYPE_ATTACH = 'attach'
    STIP_SNS_TYPE_V2_ATTACH = const.STIP_STIX2_SNS_POST_TYPE_ATTACHMENT
    STIP_SNS_TYPE_NOT = 'not'
    STIP_SNS_TYPE_UNDEFINED = 'undefined'

    SNS_TYPE_CHOICES = (
        (STIP_SNS_TYPE_ORIGIN, STIP_SNS_TYPE_ORIGIN),
        (STIP_SNS_TYPE_LIKE, STIP_SNS_TYPE_LIKE),
        (STIP_SNS_TYPE_UNLIKE, STIP_SNS_TYPE_UNLIKE),
        (STIP_SNS_TYPE_COMMENT, STIP_SNS_TYPE_COMMENT),
        (STIP_SNS_TYPE_ATTACH, STIP_SNS_TYPE_ATTACH),
        (STIP_SNS_TYPE_NOT, STIP_SNS_TYPE_NOT),
        (STIP_SNS_TYPE_UNDEFINED, STIP_SNS_TYPE_UNDEFINED),
        (STIP_SNS_TYPE_V2_POST, STIP_SNS_TYPE_V2_POST),
        (STIP_SNS_TYPE_V2_ATTACH, STIP_SNS_TYPE_V2_ATTACH),
    )

    version = fields.StringField(max_length=32, choices=VERSION_CHOICES)
    package_id = fields.StringField(max_length=100, unique=True)
    input_community = fields.ReferenceField(Communities)
    package_name = fields.StringField(max_length=1000, default='')
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    produced = fields.DateTimeField(default=None)
    via = fields.ReferenceField(Vias)
    origin_path = fields.StringField(max_length=1024)
    content = fields.FileField(collection_name='stix')
    generation = fields.ListField()
    comment = fields.StringField(max_length=10240, default='')
    is_post_sns = fields.BooleanField(default=True)
    is_created_by_sns = fields.BooleanField(default=False)
    related_packages = fields.ListField(default=None)
    sns_critical_infrastructure = fields.StringField(max_length=128, default='')
    sns_screen_name = fields.StringField(max_length=128, default='')
    sns_user_name = fields.StringField(max_length=128, default='')
    sns_affiliation = fields.StringField(max_length=128, default='')
    sns_sharing_range = fields.StringField(max_length=128, default='')
    sns_region_code = fields.StringField(max_length=128, default='')
    sns_instance = fields.StringField(max_length=128, default='')
    sns_type = fields.StringField(max_length=16, choices=SNS_TYPE_CHOICES, default=STIP_SNS_TYPE_UNDEFINED)
    information_source = fields.ReferenceField(InformationSources, default=None)
    post = fields.StringField(default=None)
    taxii2_stix_objects = fields.ListField(fields.ReferenceField(TXS21_SO, dbref=True))
    sns_tags = fields.ListField(default=[])
    sns_lower_tags = fields.ListField(default=[])

    meta = {
        'indexes': [
            ('#package_id'),
        ]
    }

    class PackageBean(object):
        def __init__(self):
            self.package_id = ''
            self.version = ''
            self.produced = ''
            self.is_post_sns = True
            self.is_created_by_sns = False
            self.related_packages = None
            self.package_name = ''
            self.sns_critical_infrastructure = ''
            self.sns_screen_name = ''
            self.sns_user_name = ''
            self.sns_affiliation = ''
            self.sns_sharing_range = ''
            self.sns_region_code = ''
            self.sns_instance = ''
            self.sns_type = StixFiles.STIP_SNS_TYPE_UNDEFINED
            self.description = ''

    @classmethod
    def rebuild_cache(cls):
        StixIndicators.drop_collection()
        StixObservables.drop_collection()
        StixCampaigns.drop_collection()
        StixIncidents.drop_collection()
        StixThreatActors.drop_collection()
        StixExploitTargets.drop_collection()
        StixCoursesOfAction.drop_collection()
        StixTTPs.drop_collection()
        ObservableCaches.drop_collection()
        LabelCaches.drop_collection()
        Tags.drop_collection()
        ExploitTargetCaches.drop_collection()
        IndicatorV2Caches.drop_collection()
        SimilarScoreCache.drop_collection()

        StixAttackPatterns.drop_collection()
        StixCampaignsV2.drop_collection()
        StixCoursesOfActionV2.drop_collection()
        StixIdentities.drop_collection()
        StixIntrusionSets.drop_collection()
        StixLocations.drop_collection()
        StixMalwares.drop_collection()
        StixNotes.drop_collection()
        StixOpinions.drop_collection()
        StixReports.drop_collection()
        StixThreatActorsV2.drop_collection()
        StixTools.drop_collection()
        StixVulnerabilities.drop_collection()
        StixRelationships.drop_collection()
        StixSightings.drop_collection()
        StixLanguageContents.drop_collection()
        StixOthers.drop_collection()
        StixGroupings.drop_collection()
        StixInfrastructures.drop_collection()
        StixMalwareAnalyses.drop_collection()

        TXS21_SO.drop_collection()
        StixManifest.drop_collection()

        for stix in StixFiles.objects.all().timeout(False):
            stix.split_child_nodes()
            if stix.produced is None:
                stix_package = STIXPackage.from_xml(stix.origin_path)
                if stix_package.timestamp:
                    stix.produced = stix_package.timestamp
                else:
                    stix.produced = stix.created
                stix.save()
        return

    def is_stix_v2(self):
        return self.version.startswith('2.')

    @classmethod
    def create(cls,
               package_bean,
               input_community,
               content,
               via,
               ):
        now = datetime.datetime.now(pytz.utc)
        document = StixFiles()
        document.version = package_bean.version
        document.input_community = input_community
        document.package_id = package_bean.package_id
        document.via = via
        document.content.put(content)
        document.created = document.modified = now
        if package_bean.package_name and len(package_bean.package_name) > 0:
            document.package_name = package_bean.package_name
        else:
            document.package_name = package_bean.package_id
        document.generation.append(document.content.grid_id)
        if package_bean.produced is None:
            document.produced = document.created
        else:
            document.produced = package_bean.produced
        document.is_post_sns = package_bean.is_post_sns
        document.is_created_by_sns = package_bean.is_created_by_sns
        document.related_packages = package_bean.related_packages
        document.sns_critical_infrastructure = package_bean.sns_critical_infrastructure
        document.sns_screen_name = package_bean.sns_screen_name
        document.sns_user_name = package_bean.sns_user_name
        document.sns_affiliation = package_bean.sns_affiliation
        document.sns_sharing_range = package_bean.sns_sharing_range
        document.sns_region_code = package_bean.sns_region_code
        document.sns_instance = package_bean.sns_instance
        document.sns_type = package_bean.sns_type
        document.post = package_bean.description
        document.save()
        document.set_information_source()
        return document

    def delete_by_stix_file(self):
        for so in self.taxii2_stix_objects:
            so.delete(self)
        self.delete()
        return

    @classmethod
    def delete_by_id(cls, id_):
        o = StixFiles.objects.get(id=id_)
        o.delete_by_stix_file()

        Feed.delete_record_related_packages(o.package_id)
        return o.origin_path

    @classmethod
    def delete_by_package_id(cls, package_id):
        o = StixFiles.objects.get(package_id=package_id)
        o.delete_by_stix_file()

        Feed.delete_record_related_packages(o.package_id)
        return o.origin_path

    @classmethod
    def delete_by_related_packages(cls, package_id):
        origin_path_list = []
        remove_package_ids = []

        o = StixFiles.objects.get(package_id=package_id)
        related_packages = o.related_packages
        if related_packages:
            for related_package in related_packages:
                related_o = StixFiles.objects.get(package_id=related_package)
                related_o.delete()
                origin_path_list.append(related_o.origin_path)
                remove_package_ids.append(related_package)

        remove_related_packages = []
        objs = StixFiles.objects.filter(related_packages=[package_id])
        for obj in objs:
            remove_related_packages.append(obj.package_id)
            origin_path_list.append(obj.origin_path)
            remove_package_ids.append(obj.package_id)
        objs.delete()

        o.delete()
        origin_path_list.append(o.origin_path)
        remove_package_ids.append(package_id)

        if related_packages:
            for related_package in related_packages:
                Feed.delete_record_related_packages(related_package)

        if remove_related_packages:
            for remove_related_package in remove_related_packages:
                Feed.delete_record_related_packages(remove_related_package)

        Feed.delete_record_related_packages(package_id)
        return origin_path_list, remove_package_ids

    def get_unique_name(self):
        if self.sns_instance is None:
            return self.sns_user_name
        return '%s %s' % (self.sns_instance, self.sns_user_name)

    def get_stix_package(self):
        if self.origin_path is None:
            return None
        try:
            return STIXPackage.from_xml(self.origin_path)
        except BaseException:
            return None

    def split_child_nodes(self):
        stix_package = self.get_stix_package()
        if stix_package:
            self.split_child_nodes_stix_1_x(stix_package)
        else:
            self.split_child_nodes_stix_2_x()
        return

    def split_child_nodes_stix_2_x(self):
        try:
            f = open(self.origin_path, 'r', encoding='utf-8')
            j = json.load(f)
            if 'objects' not in j:
                self.save()
                f.close()
                return
            objects = j['objects']
            self.taxii2_stix_objects = []
            for object_ in objects:
                type_ = object_['type']
                if type_ == 'marking-definition':
                    continue
                if type_ != 'x-stip-sns':
                    if 'labels' in object_:
                        LabelCaches.create(object_, self)
                        Tags.append_by_object(object_)
                        self.sns_tags.extend(object_['labels'])
                        self.sns_tags = list(set(self.sns_tags))
                        self.sns_lower_tags = list(set(map(str.lower, self.sns_tags)))
                if type_ == 'attack-pattern':
                    StixAttackPatterns.create(object_, self)
                elif type_ == 'campaign':
                    StixCampaignsV2.create(object_, self)
                elif type_ == 'course-of-action':
                    StixCoursesOfActionV2.create(object_, self)
                elif type_ == 'identity':
                    StixIdentities.create(object_, self)
                elif type_ == 'indicator':
                    StixIndicators.create_2_x(object_, self)
                elif type_ == 'intrusion-set':
                    StixIntrusionSets.create(object_, self)
                elif type_ == 'location':
                    StixLocations.create(object_, self)
                elif type_ == 'malware':
                    StixMalwares.create(object_, self)
                elif type_ == 'note':
                    StixNotes.create(object_, self)
                elif type_ == 'observed-data':
                    StixObservables.create_2_x(object_, self)
                elif type_ == 'opinion':
                    StixOpinions.create(object_, self)
                elif type_ == 'report':
                    StixReports.create(object_, self)
                elif type_ == 'threat-actor':
                    StixThreatActorsV2.create(object_, self)
                elif type_ == 'tool':
                    StixTools.create(object_, self)
                elif type_ == 'vulnerability':
                    StixVulnerabilities.create(object_, self)
                elif type_ == 'relationship':
                    StixRelationships.create(object_, self)
                elif type_ == 'sighting':
                    StixSightings.create(object_, self)
                elif type_ == 'language-content':
                    StixLanguageContents.create(object_, self)
                elif type_ == 'grouping':
                    StixGroupings.create(object_, self)
                elif type_ == 'infrastructure':
                    StixInfrastructures.create(object_, self)
                elif type_ == 'malware-analysis':
                    StixMalwareAnalyses.create(object_, self)
                else:
                    StixOthers.create(object_, self)

                media_types = ["application/stix+json;version=2.1"]
                object_id = object_['id']
                modified = get_modified_from_object(object_)
                try:
                    txs21_so = TXS21_SO.objects.get(object_id=object_id, modified=modified)
                    txs21_so.append_stix_file(self)
                except DoesNotExist:
                    txs21_so = TXS21_SO.create(object_, media_types, self)
                self.taxii2_stix_objects.append(txs21_so)
            self.save()
            f.close()
        except Exception:
            import traceback
            traceback.print_exc()
            return None

    def split_child_nodes_stix_1_x(self, stix_package):
        indicators = stix_package.indicators
        if indicators:
            for indicator in indicators:
                if indicator:
                    try:
                        StixIndicators.create(indicator, self)
                    except NotUniqueError:
                        pass

        observables = stix_package.observables
        if observables:
            for observable in observables:
                if observable:
                    try:
                        StixObservables.create(observable, self)
                    except NotUniqueError:
                        pass

        campaigns = stix_package.campaigns
        if campaigns:
            for campaign in campaigns:
                if campaign:
                    try:
                        StixCampaigns.create(campaign, self)
                    except NotUniqueError:
                        pass

        incidents = stix_package.incidents
        if incidents:
            for incident in incidents:
                if incident:
                    try:
                        StixIncidents.create(incident, self)
                    except NotUniqueError:
                        pass

        threat_actors = stix_package.threat_actors
        if threat_actors:
            for threat_actor in threat_actors:
                if threat_actor:
                    try:
                        StixThreatActors.create(threat_actor, self)
                    except NotUniqueError:
                        pass

        exploit_targets = stix_package.exploit_targets
        if exploit_targets:
            for exploit_target in exploit_targets:
                if exploit_target:
                    try:
                        StixExploitTargets.create(exploit_target, self)
                    except NotUniqueError:
                        pass

        courses_of_action = stix_package.courses_of_action
        if courses_of_action:
            for course_of_action in courses_of_action:
                if course_of_action:
                    try:
                        StixCoursesOfAction.create(course_of_action, self)
                    except NotUniqueError:
                        pass

        ttps = stix_package.ttps
        if ttps:
            for ttp in ttps.ttp:
                if ttp:
                    try:
                        StixTTPs.create(ttp, self)
                    except NotUniqueError:
                        pass

    def get_rest_api_document_info(self, required_comment=False):
        d = {}
        d['id'] = str(self.id)
        d['version'] = self.version
        d['package_id'] = self.package_id
        d['package_name'] = self.package_name
        d['created'] = self.get_datetime_string(self.created)
        d['modified'] = self.get_datetime_string(self.modified)
        d['produced'] = self.get_datetime_string(self.produced)
        try:
            d['input_community'] = self.input_community.name
        except DoesNotExist:
            d['input_community'] = ''
        if required_comment:
            d['comment'] = self.comment
        return d

    def get_rest_api_package_name_info(self):
        d = {}
        d['package_id'] = self.package_id
        d['package_name'] = self.package_name
        return d

    def get_rest_api_document_content(self):
        return {'content': self.content.read().decode('utf-8')}

    def get_webhook_document(self):
        return self.get_rest_api_document_info()

    def get_datetime_string(self, d):
        return str(d)

    def get_slide_12(self):
        if self.version.startswith('2.'):
            stix2slider.convert_stix._ID_NAMESPACE = self.NS_S_TIP_NAME
            sl_init()
            return stix2slider.slide_file(self.origin_path)
        return None

    def get_elevate_20(self):
        if self.version.startswith('1.'):
            el_init()
            return ELEVATE(self.origin_path)
        return None

    def get_elevate_21(self):
        if self.version.startswith('1.'):
            el_init()
            set_option_value('spec_version', '2.1')
            return ELEVATE(self.origin_path)
        if self.version == '2.0':
            return step_file(self.origin_path)
        return None

    def set_information_source(self):
        if self.sns_instance is None:
            return
        if len(self.sns_instance) == 0:
            return
        information_source_name = self.sns_instance
        try:
            information_source = InformationSources.objects.get(name=information_source_name)
        except BaseException:
            information_source = InformationSources.create(information_source_name)
        self.information_source = information_source
        self.save()

    def to_dict(self):
        d = {
            'version': self.version,
            'package_id': self.package_id,
            'input_community': self.input_community.name,
            'package_name': self.package_name,
            'created': self.created,
            'modified': self.modified,
            'produced': self.produced,
            'comment': self.comment,
        }
        return d


class LabelCaches(Document):
    label = fields.StringField(max_length=1024)
    node_id = fields.StringField(max_length=100)
    package_id = fields.StringField(max_length=1024)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return
        if 'labels' not in object_:
            return
        for label in object_['labels']:
            if len(label) == 0:
                return
            document = LabelCaches()
            document.stix_file = stix_file
            document.label = label
            document.package_id = stix_file.package_id
            document.node_id = '%s--%s' % (sanitize_id(label), object_['id'])
            document.save()
        return document


class IndicatorV2Caches(Document):
    indicator_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    pattern = fields.StringField(max_length=10240)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)
    package_name = fields.StringField(max_length=1024)
    package_id = fields.StringField(max_length=100)
    node_id = fields.StringField(max_length=100)

    @classmethod
    def create(cls, indicator, stix_file, node_id):
        if indicator is None:
            return
        document = IndicatorV2Caches()
        if ('id' in indicator):
            document.indicator_id = indicator['id']
        if ('name' in indicator):
            document.title = indicator['name']
        if ('description' in indicator):
            document.description = indicator['description']
        if ('pattern' in indicator):
            document.pattern = indicator['pattern']
        document.object_ = indicator
        document.stix_file = stix_file
        document.package_name = stix_file.package_name
        document.package_id = stix_file.package_id
        document.node_id = node_id
        document.save()
        return document


class Stix2Base(Document):
    type_ = fields.StringField(max_length=16)
    spec_version = fields.StringField(max_length=16)
    object_id_ = fields.StringField(max_length=100)
    created_by_ref = fields.StringField(max_length=100)
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    revoked = fields.BooleanField(default=False)
    labels = fields.ListField()
    confidence = fields.IntField()
    lang = fields.StringField(max_length=100)
    external_references = fields.ListField()
    object_marking_refs = fields.ListField()
    granular_markings = fields.ListField()

    object_ = fields.DictField()
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)
    package_name = fields.StringField(max_length=1024)
    package_id = fields.StringField(max_length=100)

    meta = {
        'allow_inheritance': True,
        'abstract': True,
        'indexes': [
            ('$object_id_')
        ]
    }

    @classmethod
    def get_lists_or_string(cls, value):
        list_ = []
        if isinstance(value, list):
            for item in value:
                list_.append(item)
        else:
            list_.append(value)
        return list_

    @classmethod
    def create(cls, document, object_, stix_file):
        if ('id' in object_):
            document.object_id_ = object_['id']
        if ('spec_version' in object_):
            document.spec_version = object_['spec_version']
        if ('created_by_ref' in object_):
            document.created_by_ref = object_['created_by_ref']
        if ('created' in object_):
            document.created = stix2_str_to_datetime(object_['created'])
        if ('modified' in object_):
            document.modified = stix2_str_to_datetime(object_['modified'])
        if ('revoked' in object_):
            document.revoked = object_['revoked']
        if ('labels' in object_):
            document.labels = Stix2Base.get_lists_or_string(object_['labels'])
        if ('confidence' in object_):
            document.confidence = object_['confidence']
        if ('lang' in object_):
            document.lang = object_['lang']
        if ('external_references' in object_):
            document.external_references = Stix2Base.get_lists_or_string(object_['external_references'])
        if ('object_marking_refs' in object_):
            document.object_marking_refs = Stix2Base.get_lists_or_string(object_['object_marking_refs'])
        if ('granular_markings' in object_):
            document.granular_markings = Stix2Base.get_lists_or_string(object_['granular_markings'])
        document.object_ = object_
        document.stix_file = stix_file
        document.package_name = stix_file.package_name
        document.package_id = stix_file.package_id
        return document

    @staticmethod
    def newest(objects):
        return objects.order_by('-modified')[0]

    @staticmethod
    def newest_find(object_id):
        if object_id.startswith('attack-pattern--'):
            return Stix2Base.newest(StixAttackPatterns.objects(object_id_=object_id))
        if object_id.startswith('campaign--'):
            return Stix2Base.newest(StixCampaignsV2.objects(object_id_=object_id))
        if object_id.startswith('course-of-action--'):
            return Stix2Base.newest(StixCoursesOfActionV2.objects(object_id_=object_id))
        if object_id.startswith('grouping--'):
            return Stix2Base.newest(StixGroupings.objects(object_id_=object_id))
        if object_id.startswith('identity--'):
            return Stix2Base.newest(StixIdentities.objects(object_id_=object_id))
        if object_id.startswith('indicator--'):
            return Stix2Base.newest(StixIndicatorsV2.objects(object_id_=object_id))
        if object_id.startswith('infrastructure--'):
            return Stix2Base.newest(StixInfrastructures.objects(object_id_=object_id))
        if object_id.startswith('intrusion-set--'):
            return Stix2Base.newest(StixIntrusionSets.objects(object_id_=object_id))
        if object_id.startswith('location--'):
            return Stix2Base.newest(StixLocations.objects(object_id_=object_id))
        if object_id.startswith('malware--'):
            return Stix2Base.newest(StixMalwares.objects(object_id_=object_id))
        if object_id.startswith('malware-analysis--'):
            return Stix2Base.newest(StixMalwareAnalyses.objects(object_id_=object_id))
        if object_id.startswith('note--'):
            return Stix2Base.newest(StixNotes.objects(object_id_=object_id))
        if object_id.startswith('observed-data--'):
            return Stix2Base.newest(StixObservedData.objects(object_id_=object_id))
        if object_id.startswith('opinion--'):
            return Stix2Base.newest(StixOpinions.objects(object_id_=object_id))
        if object_id.startswith('report--'):
            return Stix2Base.newest(StixReports.objects(object_id_=object_id))
        if object_id.startswith('threat-actor--'):
            return Stix2Base.newest(StixThreatActorsV2.objects(object_id_=object_id))
        if object_id.startswith('tool--'):
            return Stix2Base.newest(StixTools.objects(object_id_=object_id))
        if object_id.startswith('vulnerability--'):
            return Stix2Base.newest(StixVulnerabilities.objects(object_id_=object_id))
        return Stix2Base.newest(StixOthers.objects(object_id_=object_id))

    @staticmethod
    def change_modified_timestamp_dict(o_):
        d = copy.deepcopy(o_.object_)
        d['modified'] = datetime.datetime.now(pytz.utc)
        return d

    @staticmethod
    def get_revoked_dict(o_):
        d = Stix2Base.change_modified_timestamp_dict(o_)
        d['revoked'] = True
        return d

    @staticmethod
    def get_modified_dict(before, after):
        SKIP_PROP = ['id', 'type', 'created', 'modified', 'spec_version', 'created_by_ref']
        d = Stix2Base.change_modified_timestamp_dict(before)
        for k in after:
            if k in SKIP_PROP:
                continue
            d[k] = after[k]
        return d


class StixAttackPatterns(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    kill_chain_phases = fields.ListField()

    meta = {
        'collection': 'stix_attack_patterns',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixAttackPatterns()
        document = super(StixAttackPatterns, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('kill_chain_phases' in object_):
            document.kill_chain_phases = Stix2Base.get_lists_or_string(object_['kill_chain_phases'])
        document.save()
        return document


class StixCampaignsV2(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    aliases = fields.ListField()
    first_seen = fields.DateTimeField()
    last_seen = fields.DateTimeField()
    objective = fields.StringField(max_length=10240)

    meta = {
        'collection': 'stix_campaigns_v2'
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixCampaignsV2()
        document = super(StixCampaignsV2, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('aliases' in object_):
            document.aliases = Stix2Base.get_lists_or_string(object_['aliases'])
        if ('first_seen' in object_):
            document.first_seen = stix2_str_to_datetime(object_['first_seen'])
        if ('last_seen' in object_):
            document.last_seen = stix2_str_to_datetime(object_['last_seen'])
        if ('objective' in object_):
            document.objective = object_['objective']
        document.save()
        return document


class StixCoursesOfActionV2(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    action = fields.StringField(max_length=10240)

    meta = {
        'collection': 'stix_courses_of_action_v2'
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixCoursesOfActionV2()
        document = super(StixCoursesOfActionV2, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        document.save()
        return document


class StixIdentities(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    identity_class = fields.StringField(max_length=1024)
    sectors = fields.ListField()
    contact_information = fields.StringField(max_length=1024)

    meta = {
        'collection': 'stix_identities',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixIdentities()
        document = super(StixIdentities, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('identity_class' in object_):
            document.identity_class = object_['identity_class']
        if ('contact_information' in object_):
            document.contact_information = object_['contact_information']
        if ('sectors' in object_):
            document.sectors = Stix2Base.get_lists_or_string(object_['sectors'])
        document.save()
        return document


class StixIndicatorsV2(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    pattern = fields.StringField(max_length=10240)
    valid_from = fields.DateTimeField()
    valid_until = fields.DateTimeField()
    kill_chain_phases = fields.ListField()

    meta = {
        'collection': 'stix_indicators_v2'
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixIndicatorsV2()
        document = super(StixIndicatorsV2, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('pattern' in object_):
            document.pattern = object_['pattern']
        if ('valid_from' in object_):
            document.valid_from = stix2_str_to_datetime(object_['valid_from'])
        if ('valid_until' in object_):
            document.valid_until = stix2_str_to_datetime(object_['valid_until'])
        if ('kill_chain_phases' in object_):
            document.kill_chain_phases = Stix2Base.get_lists_or_string(object_['kill_chain_phases'])
        document.save()
        return document


class StixIntrusionSets(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    aliases = fields.ListField()
    first_seen = fields.DateTimeField()
    last_seen = fields.DateTimeField()
    goals = fields.ListField()
    resource_level = fields.StringField(max_length=1024)
    primary_motivation = fields.StringField(max_length=1024)
    secondary_motivations = fields.ListField()

    meta = {
        'collection': 'stix_intrusion_sets',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixIntrusionSets()
        document = super(StixIntrusionSets, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('aliases' in object_):
            document.aliases = Stix2Base.get_lists_or_string(object_['aliases'])
        if ('first_seen' in object_):
            document.first_seen = stix2_str_to_datetime(object_['first_seen'])
        if ('last_seen' in object_):
            document.last_seen = stix2_str_to_datetime(object_['last_seen'])
        if ('goals' in object_):
            document.goals = Stix2Base.get_lists_or_string(object_['goals'])
        if ('resource_level' in object_):
            document.resource_level = object_['resource_level']
        if ('primary_motivation' in object_):
            document.primary_motivation = object_['primary_motivation']
        if ('secondary_motivations' in object_):
            document.secondary_motivations = Stix2Base.get_lists_or_string(object_['secondary_motivations'])
        document.save()
        return document


class StixLocations(Stix2Base):
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    latitude = fields.FloatField()
    longitude = fields.FloatField()
    precision = fields.FloatField()
    region = fields.StringField(max_length=1024)
    country = fields.StringField(max_length=1024)
    administrative_area = fields.StringField(max_length=1024)
    city = fields.StringField(max_length=1024)
    code = fields.StringField(max_length=1024)
    postal_code = fields.StringField(max_length=1024)

    meta = {
        'collection': 'stix_locations',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixLocations()
        document = super(StixLocations, cls).create(document, object_, stix_file)
        if ('description' in object_):
            document.description = object_['description']
        if ('latitude' in object_):
            document.latitude = float(object_['latitude'])
        if ('longitude' in object_):
            document.longitude = float(object_['longitude'])
        if ('precision' in object_):
            document.precision = float(object_['precision'])
        if ('region' in object_):
            document.region = object_['region']
        if ('country' in object_):
            document.country = object_['country']
        if ('administrative_area' in object_):
            document.administrative_area = object_['administrative_area']
        if ('city' in object_):
            document.city = object_['city']
        if ('code' in object_):
            document.code = object_['code']
        if ('postal_code' in object_):
            document.postal_code = object_['postal_code']
        document.save()
        return document


class StixMalwares(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    kill_chain_phases = fields.ListField()

    meta = {
        'collection': 'stix_malwares',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixMalwares()
        document = super(StixMalwares, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('kill_chain_phases' in object_):
            document.kill_chain_phases = Stix2Base.get_lists_or_string(object_['kill_chain_phases'])
        document.save()
        return document


class StixNotes(Stix2Base):
    abstract = fields.StringField(max_length=1024)
    content = fields.StringField(max_length=10240)
    authors = fields.ListField()
    object_refs = fields.ListField()

    meta = {
        'collection': 'stix_notes',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixNotes()
        document = super(StixNotes, cls).create(document, object_, stix_file)
        if ('abstract' in object_):
            document.abstract = object_['abstract']
        if ('content' in object_):
            document.content = object_['content']
        if ('authors' in object_):
            document.authors = Stix2Base.get_lists_or_string(object_['authors'])
        if ('object_refs' in object_):
            document.object_refs = Stix2Base.get_lists_or_string(object_['object_refs'])
        document.save()
        return document


class StixGroupings(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    context = fields.StringField(max_length=10240)
    object_refs = fields.ListField()

    meta = {
        'collection': 'stix_groupings',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixGroupings()
        document = super(StixGroupings, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('context' in object_):
            document.context = object_['context']
        if ('object_refs' in object_):
            document.object_refs = Stix2Base.get_lists_or_string(object_['object_refs'])
        document.save()
        return document


class StixInfrastructures(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    infrastructure_types = fields.ListField()
    aliases = fields.ListField()
    kill_chain_phases = fields.ListField()
    first_seen = fields.DateTimeField()
    last_seen = fields.DateTimeField()

    meta = {
        'collection': 'stix_infrastructures',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixInfrastructures()
        document = super(StixInfrastructures, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('infrastructure_types' in object_):
            document.infrastructure_types = Stix2Base.get_lists_or_string(object_['infrastructure_types'])
        if ('aliases' in object_):
            document.aliases = Stix2Base.get_lists_or_string(object_['aliases'])
        if ('kill_chain_phases' in object_):
            document.kill_chain_phases = Stix2Base.get_lists_or_string(object_['kill_chain_phases'])
        if ('first_seen' in object_):
            document.first_seen = object_['first_seen']
        if ('last_seen' in object_):
            document.last_seen = object_['last_seen']
        if ('context' in object_):
            document.context = object_['context']
        if ('object_refs' in object_):
            document.object_refs = Stix2Base.get_lists_or_string(object_['object_refs'])
        document.save()
        return document


class StixMalwareAnalyses(Stix2Base):
    product = fields.StringField(max_length=1024)
    version = fields.StringField(max_length=10240)
    host_vm_ref = fields.StringField(max_length=10240)
    installed_software_refs = fields.ListField()
    configuration_version = fields.StringField(max_length=10240)
    modules = fields.ListField()
    analysis_engine_version = fields.StringField(max_length=10240)
    analysis_definition_version = fields.StringField(max_length=10240)
    submitted = fields.DateTimeField()
    analysis_started = fields.DateTimeField()
    analysis_ended = fields.DateTimeField()
    result_name = fields.StringField(max_length=10240)
    result = fields.StringField(max_length=10240)
    analysis_sco_refs = fields.ListField()
    sample_ref = fields.StringField(max_length=10240)

    meta = {
        'collection': 'stix_malware_analyses',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixMalwareAnalyses()
        document = super(StixMalwareAnalyses, cls).create(document, object_, stix_file)
        if ('product' in object_):
            document.product = object_['product']
        if ('version' in object_):
            document.version = object_['version']
        if ('host_vm_ref' in object_):
            document.host_vm_ref = object_['host_vm_ref']
        if ('installed_software_refs' in object_):
            document.installed_software_refs = Stix2Base.get_lists_or_string(object_['installed_software_refs'])
        if ('configuration_version' in object_):
            document.configuration_version = object_['configuration_version']
        if ('modules' in object_):
            document.modules = Stix2Base.get_lists_or_string(object_['modules'])
        if ('analysis_engine_version' in object_):
            document.analysis_engine_version = object_['analysis_engine_version']
        if ('analysis_definition_version' in object_):
            document.analysis_definition_version = object_['analysis_definition_version']
        if ('submitted' in object_):
            document.submitted = object_['submitted']
        if ('analysis_started' in object_):
            document.analysis_started = object_['analysis_started']
        if ('analysis_ended' in object_):
            document.analysis_ended = object_['analysis_ended']
        if ('result_name' in object_):
            document.result_name = object_['result_name']
        if ('result' in object_):
            document.result = object_['result']
        if ('analysis_sco_refs' in object_):
            document.analysis_sco_refs = Stix2Base.get_lists_or_string(object_['analysis_sco_refs'])
        if ('sample_ref' in object_):
            document.sample_ref = object_['sample_ref']
        document.save()
        return document


class StixObservedData(Stix2Base):
    first_observed = fields.DateTimeField(default=datetime.datetime.now)
    last_observed = fields.DateTimeField(default=datetime.datetime.now)
    number_observed = fields.IntField()
    objects_ = fields.DictField()

    meta = {
        'collection': 'stix_observed_data'
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixObservedData()
        document = super(StixObservedData, cls).create(document, object_, stix_file)
        if ('first_observed' in object_):
            document.first_observed = stix2_str_to_datetime(object_['first_observed'])
        if ('last_observed' in object_):
            document.last_observed = stix2_str_to_datetime(object_['last_observed'])
        if ('number_observed' in object_):
            document.number_observed = object_['number_observed']
        if ('objects' in object_):
            document.objects_ = object_['objects']
        document.save()
        return document


class StixOpinions(Stix2Base):
    explanation = fields.StringField(max_length=10240)
    authors = fields.ListField()
    object_refs = fields.ListField()
    opinion = fields.StringField(max_length=10240)

    meta = {
        'collection': 'stix_opinions'
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixOpinions()
        document = super(StixOpinions, cls).create(document, object_, stix_file)
        if ('explanation' in object_):
            document.explanation = object_['explanation']
        if ('authors' in object_):
            document.authors = Stix2Base.get_lists_or_string(object_['authors'])
        if ('object_refs' in object_):
            document.object_refs = Stix2Base.get_lists_or_string(object_['object_refs'])
        if ('opinion' in object_):
            document.opinion = object_['opinion']
        document.save()
        return document


class StixReports(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    published = fields.DateTimeField()
    object_refs = fields.ListField()

    meta = {
        'collection': 'stix_reports'
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixReports()
        document = super(StixReports, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('published' in object_):
            document.published = stix2_str_to_datetime(object_['published'])
        if ('object_refs' in object_):
            document.object_refs = Stix2Base.get_lists_or_string(object_['object_refs'])
        document.save()
        return document


class StixThreatActorsV2(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    aliases = fields.ListField()
    roles = fields.ListField()
    goals = fields.ListField()
    sophistication = fields.StringField(max_length=1024)
    resource_level = fields.StringField(max_length=1024)
    primary_motivation = fields.StringField(max_length=1024)
    secondary_motivations = fields.ListField()
    personal_motivations = fields.ListField()

    meta = {
        'collection': 'stix_threat_actors_v2'
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixThreatActorsV2()
        document = super(StixThreatActorsV2, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('aliases' in object_):
            document.aliases = Stix2Base.get_lists_or_string(object_['aliases'])
        if ('roles' in object_):
            document.roles = Stix2Base.get_lists_or_string(object_['roles'])
        if ('goals' in object_):
            document.goals = Stix2Base.get_lists_or_string(object_['goals'])
        if ('sophistication' in object_):
            document.sophistication = object_['sophistication']
        if ('resource_level' in object_):
            document.resource_level = object_['resource_level']
        if ('primary_motivation' in object_):
            document.primary_motivation = object_['primary_motivation']
        if ('secondary_motivations' in object_):
            document.secondary_motivations = Stix2Base.get_lists_or_string(object_['secondary_motivations'])
        if ('personal_motivations' in object_):
            document.personal_motivations = Stix2Base.get_lists_or_string(object_['personal_motivations'])
        document.save()
        return document


class StixTools(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    kill_chain_phases = fields.ListField()
    tool_version = fields.StringField(max_length=1024)

    meta = {
        'collection': 'stix_tools',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixTools()
        document = super(StixTools, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('kill_chain_phases' in object_):
            document.kill_chain_phases = Stix2Base.get_lists_or_string(object_['kill_chain_phases'])
        if ('tool_version' in object_):
            document.tool_version = object_['tool_version']
        document.save()
        return document


class StixVulnerabilities(Stix2Base):
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)

    cves = fields.ListField()

    meta = {
        'collection': 'stix_vulnerabilities'
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixVulnerabilities()
        document = super(StixVulnerabilities, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        if ('external_references' in object_):
            cves = []
            for external_reference in object_['external_references']:
                if 'source_name' in external_reference:
                    if external_reference['source_name'] == 'cve':
                        if ('external_id' in external_reference):
                            cves.append(external_reference['external_id'])
            document.cves = cves
        document.save()
        ExploitTargetCaches.create_2_x(document)
        return document


class StixRelationships(Stix2Base):
    relationship_type = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    source_ref = fields.StringField(max_length=1024)
    target_ref = fields.StringField(max_length=1024)

    meta = {
        'collection': 'stix_relationships'
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixRelationships()
        document = super(StixRelationships, cls).create(document, object_, stix_file)
        if ('relationship_type' in object_):
            document.relationship_type = object_['relationship_type']
        if ('description' in object_):
            document.description = object_['description']
        if ('source_ref' in object_):
            document.source_ref = object_['source_ref']
        if ('target_ref' in object_):
            document.target_ref = object_['target_ref']
        document.save()
        return document


class StixSightings(Stix2Base):
    first_seen = fields.DateTimeField()
    last_seen = fields.DateTimeField()
    count = fields.IntField()
    sighting_of_ref = fields.StringField(max_length=100)
    observed_data_refs = fields.ListField()
    where_sighted_refs = fields.ListField()
    summary = fields.BooleanField(default=False)

    meta = {
        'collection': 'stix_sightings'
    }

    @classmethod
    def create_by_observed_id(cls, first_seen, last_seen, count, observed_data_id, uploader):
        SIGHTING_IDENTITY_NAME = 'Fujitsu System Integration Laboratories.'
        SIGHTING_IDENTITY_IDENTITY_CLASS = 'organization'
        stix_file_path = None
        try:
            sighting_identity = stix2.Identity(
                name=SIGHTING_IDENTITY_NAME,
                identity_class=SIGHTING_IDENTITY_IDENTITY_CLASS,
            )
            if count != 0:
                sighting = stix2.Sighting(
                    first_seen=first_seen,
                    last_seen=last_seen,
                    count=count,
                    created_by_ref=sighting_identity,
                    sighting_of_ref=observed_data_id)
            else:
                sighting = stix2.Sighting(
                    first_seen=first_seen,
                    last_seen=last_seen,
                    created_by_ref=sighting_identity,
                    sighting_of_ref=observed_data_id)
            observed_data_document = next(StixObservedData.objects.filter(object_id_=observed_data_id).order_by('modified').limit(1))
            observed_data = stix2.parse(json.dumps(observed_data_document.object_))

            observed_data_identity = None
            if hasattr(observed_data, 'created_by_ref'):
                try:
                    identity_document = next(StixIdentities.objects.filter(identity_id=observed_data.created_by_ref).order_by('modified').limit(1))
                    observed_data_identity = stix2.parse(json.dumps(identity_document.object_))
                except BaseException:
                    pass

            if observed_data_identity:
                bundle = stix2.Bundle(observed_data, sighting, observed_data_identity, sighting_identity)
            else:
                bundle = stix2.Bundle(observed_data, sighting, sighting_identity)

            from ctirs.core.stix.regist import regist
            _, stix_file_path = tempfile.mkstemp(suffix='.json')
            content = bundle.serialize(indent=4)
            with open(stix_file_path, 'w', encoding='utf-8') as fp:
                fp.write(content)
            community = Communities.get_not_assign_community()
            via = Vias.get_not_assign_via(uploader=uploader.id)
            regist(stix_file_path, community, via)
            return sighting.id, json.loads(content)

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixSightings()
        document = super(StixSightings, cls).create(document, object_, stix_file)
        if ('first_seen' in object_):
            document.first_seen = object_['first_seen']
        if ('last_seen' in object_):
            document.last_seen = object_['last_seen']
        if ('count' in object_):
            document.count = object_['count']
        if ('summary' in object_):
            document.summary = object_['summary']
        if ('sighting_of_ref' in object_):
            document.sighting_of_ref = object_['sighting_of_ref']
        if ('where_sighted_refs' in object_):
            document.where_sighted_refs = object_['where_sighted_refs']
        if ('observed_data_refs' in object_):
            document.observed_data_refs = object_['observed_data_refs']
        document.save()
        return document


class StixLanguageContents(Stix2Base):
    object_ref = fields.StringField(max_length=1024)
    object_modified = fields.DateTimeField(default=datetime.datetime.now)
    contents = fields.DictField()
    meta = {
        'collection': 'stix_language_contents',
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        document = StixLanguageContents()
        document = super(StixLanguageContents, cls).create(document, object_, stix_file)
        if ('object_ref' in object_):
            document.object_ref = object_['object_ref']
        if ('object_modified' in object_):
            document.object_modified = stix2_str_to_datetime(object_['object_modified'])
        if ('contents' in object_):
            document.contents = object_['contents']
        document.save()
        return document


class StixOthers(Stix2Base):
    meta = {
        'collection': 'stix_others'
    }

    @classmethod
    def create(cls, object_, stix_file):
        if object_ is None:
            return None
        if object_['type'] == 'x-stip-sns':
            if object_['x_stip_sns_type'] != 'post':
                return None
        document = StixOthers()
        document = super(StixOthers, cls).create(document, object_, stix_file)
        if ('name' in object_):
            document.name = object_['name']
        if ('description' in object_):
            document.description = object_['description']
        document.save()
        return document


class StixIndicators(Document):
    indicator_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)
    v2_indicator = fields.ReferenceField(StixIndicatorsV2, reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#indicator_id'),
        ]
    }

    @classmethod
    def create(cls, indicator, stix_file):
        document = StixIndicators()
        document.indicator_id = indicator.id_
        document.title = indicator.title
        if indicator.description:
            document.description = indicator.description.value
        document.object_ = indicator.to_dict()
        document.stix_file = stix_file
        if indicator.timestamp:
            document.created = indicator.timestamp
            document.modified = indicator.timestamp
        document.save()
        ObservableCaches.create(indicator.observable, stix_file, indicator.id_)
        return

    @classmethod
    def create_2_x(cls, indicator, stix_file):
        v2_indicator = StixIndicatorsV2.create(indicator, stix_file)
        document = StixIndicators()
        if ('id' in indicator):
            document.indicator_id = indicator['id']
        if ('name' in indicator):
            document.title = indicator['name']
        if ('description' in indicator):
            document.description = indicator['description']
        if ('created' in indicator):
            try:
                d = stix2_str_to_datetime(indicator['created'])
                document.created = d
            except BaseException:
                None
        if ('modified' in indicator):
            try:
                d = stix2_str_to_datetime(indicator['modified'])
                document.modified = d
            except BaseException:
                None
        document.object_ = indicator
        document.stix_file = stix_file
        document.v2_indicator = v2_indicator
        document.save()
        IndicatorV2Caches.create(indicator, stix_file, indicator['id'])
        return


class StixObservables(Document):
    observable_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)
    v2_observed_data = fields.ReferenceField(StixObservedData, reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#observable_id'),
        ]
    }

    @classmethod
    def create(cls, observable, stix_file):
        document = StixObservables()
        document.observable_id = observable.id_
        document.title = observable.title
        if observable.description:
            document.description = observable.description.value
        try:
            document.object_ = observable.object_.to_dict()
        except AttributeError:
            document.object_ = None
        document.stix_file = stix_file
        document.save()
        if document.object_:
            ObservableCaches.create(observable, stix_file, observable.id_)
        return

    @classmethod
    def create_2_x(cls, observable, stix_file):
        v2_observed_data = StixObservedData.create(observable, stix_file)
        document = StixObservables()
        if ('id' in observable):
            document.observable_id = observable['id']
            document.title = observable['id']
            document.description = observable['id']
        document.object_ = observable
        if ('created' in observable):
            try:
                d = stix2_str_to_datetime(observable['created'])
                document.created = d
            except BaseException:
                None
        if ('modified' in observable):
            try:
                d = stix2_str_to_datetime(observable['modified'])
                document.modified = d
            except BaseException:
                None
        document.stix_file = stix_file
        document.v2_observed_data = v2_observed_data
        document.save()

        ObservableCaches.create_2_x(observable, stix_file, observable['id'])
        return


class StixCampaigns(Document):
    campaign_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#campaign_id'),
        ]
    }

    @classmethod
    def create(cls, campaign, stix_file):
        document = StixCampaigns()
        document.campaign_id = campaign.id_
        document.title = campaign.title
        if campaign.description:
            document.description = campaign.description.value
        document.object_ = campaign.to_dict()
        document.stix_file = stix_file
        document.save()
        return


class StixIncidents(Document):
    incident_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#incident_id'),
        ]
    }

    @classmethod
    def create(cls, incident, stix_file):
        document = StixIncidents()
        document.incident_id = incident.id_
        document.title = incident.title
        if incident.description:
            document.description = incident.description.value
        document.object_ = incident.to_dict()
        document.stix_file = stix_file
        document.save()
        return


class StixThreatActors(Document):
    ta_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#ta_id'),
        ]
    }

    @classmethod
    def create(cls, ta, stix_file):
        document = StixThreatActors()
        document.ta_id = ta.id_
        document.title = ta.title
        if ta.description:
            document.description = ta.description.value
        document.object_ = ta.to_dict()
        document.stix_file = stix_file
        document.save()
        return


class StixExploitTargets(Document):
    et_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)
    cve_ids = fields.ListField()

    meta = {
        'indexes': [
            ('#et_id'),
        ]
    }

    @classmethod
    def create(cls, et, stix_file):
        document = StixExploitTargets()
        document.et_id = et.id_
        document.title = et.title
        if et.description:
            document.description = et.description.value
        document.object_ = et.to_dict()
        if et.vulnerabilities:
            for vulnerability in et.vulnerabilities:
                try:
                    document.cve_ids.append(vulnerability.cve_id)
                except BaseException:
                    pass
        document.stix_file = stix_file
        document.save()
        ExploitTargetCaches.create(et, stix_file, et.id_)
        return


class StixCoursesOfAction(Document):
    coa_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#coa_id'),
        ]
    }

    @classmethod
    def create(cls, coa, stix_file):
        document = StixCoursesOfAction()
        document.coa_id = coa.id_
        document.title = coa.title
        if coa.description:
            document.description = coa.description.value
        document.object_ = coa.to_dict()
        document.stix_file = stix_file
        document.save()
        return


class StixTTPs(Document):
    ttp_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)

    meta = {
        'collection': 'stix_ttps',
        'indexes': [
            ('#ttp_id'),
        ]
    }

    @classmethod
    def create(cls, ttp, stix_file):
        document = StixTTPs()
        document.ttp_id = ttp.id_
        document.title = ttp.title
        if ttp.description:
            document.description = ttp.description.value
        document.object_ = ttp.to_dict()
        document.stix_file = stix_file
        document.save()
        if ttp.exploit_targets:
            for et in ttp.exploit_targets:
                ExploitTargetCaches.create(et.item, stix_file, ttp.id_)
        return


class ExploitTargetCaches(Document):
    TYPE_CHOICES = (
        ('cve_id', 'cve_id'),
    )
    type = fields.StringField(max_length=16, choices=TYPE_CHOICES)
    et_id = fields.StringField(max_length=100, unique=True)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)
    package_name = fields.StringField(max_length=1024)
    package_id = fields.StringField(max_length=100)
    node_id = fields.StringField(max_length=100)
    value = fields.StringField(max_length=1024)

    meta = {
        'indexes': [
            ('#et_id'),
        ]
    }

    @classmethod
    def create(cls, et, stix_file, node_id):
        if 'vulnerabilities' not in dir(et):
            return
        if et.vulnerabilities is None:
            return
        for vulnerability in et.vulnerabilities:
            if vulnerability.cve_id is None:
                continue
            document = ExploitTargetCaches()
            document.type = 'cve_id'
            document.et_id = et.id_
            document.title = et.title
            if et.description:
                document.description = et.description.value
            document.value = vulnerability.cve_id
            document.stix_file = stix_file
            document.package_name = stix_file.package_name
            document.package_id = stix_file.package_id
            document.node_id = node_id
            document.save()
        return

    @classmethod
    def create_2_x(cls, stix_vulnerability):
        if stix_vulnerability.cves is None:
            return
        if len(stix_vulnerability.cves) == 0:
            return
        for cve in stix_vulnerability.cves:
            node_id = '%s-%s' % (stix_vulnerability.object_id_, cve)
            document = ExploitTargetCaches()
            document.type = 'cve_id'
            document.et_id = node_id
            document.title = stix_vulnerability.name
            if stix_vulnerability.description:
                document.description = stix_vulnerability.description
            document.value = cve
            document.stix_file = stix_vulnerability.stix_file
            document.package_name = stix_vulnerability.package_name
            document.package_id = stix_vulnerability.package_id
            document.node_id = node_id
            document.save()
        return


class ObservableCaches(Document):
    TYPE_CHOICES = (
        ('uri', 'uri'),
        ('domain_name', 'domain_name'),
        ('md5', 'md5'),
        ('sha1', 'sha1'),
        ('sha256', 'sha256'),
        ('sha512', 'sha512'),
        ('ipv4', 'ipv4'),
        ('email', 'email'),
        ('mutex', 'mutex'),
    )

    meta = {
        'indexes': [
            ('package_id', 'type', 'ipv4_1_3'),
            ('package_id', 'type', 'domain_tld', 'domain_last'),
        ]
    }

    type = fields.StringField(max_length=16, choices=TYPE_CHOICES)
    observable_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    value = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=DESCRIPTION_LENGTH)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles, reverse_delete_rule=CASCADE)
    package_name = fields.StringField(max_length=1024)
    package_id = fields.StringField(max_length=100)
    node_id = fields.StringField(max_length=100)
    ipv4_1_3 = fields.StringField(max_length=12, null=True)
    ipv4_4 = fields.IntField(default=-1)
    domain_tld = fields.StringField(max_length=50, null=True)
    domain_last = fields.StringField(max_length=1024, null=True)
    domain_without_tld = fields.StringField(max_length=1024, null=True)
    first_observed = fields.StringField(default=None, null=True)
    last_observed = fields.StringField(default=None, null=True)
    number_observed = fields.IntField(default=1)

    @classmethod
    def get_stix_package(cls, stix_file):
        if stix_file is None:
            return None
        if stix_file.origin_path is None:
            return None
        return STIXPackage.from_xml(stix_file.origin_path)

    @classmethod
    def create_2_x(cls, observable, stix_file, node_id):
        if observable is None:
            return
        if 'objects' not in observable:
            return
        for object_key, object_value in observable['objects'].items():
            object_type = object_value['type']
            if object_type == 'file':
                if ('hashes' in object_value):
                    hashes = object_value['hashes']
                    if ('MD5' in hashes):
                        ObservableCaches.create_2_x_per_data(observable, object_value, stix_file, node_id, object_key, 'md5', hashes['MD5'])
                    if ('SHA-1' in hashes):
                        ObservableCaches.create_2_x_per_data(observable, object_value, stix_file, node_id, object_key, 'sha1', hashes['SHA-1'])
                    if ('SHA-256' in hashes):
                        ObservableCaches.create_2_x_per_data(observable, object_value, stix_file, node_id, object_key, 'sha256', hashes['SHA-256'])
                    if ('SHA-512' in hashes):
                        ObservableCaches.create_2_x_per_data(observable, object_value, stix_file, node_id, object_key, 'sha512', hashes['SHA-512'])
            elif object_type == 'ipv4-addr':
                ObservableCaches.create_2_x_per_data(observable, object_value, stix_file, node_id, object_key, 'ipv4', object_value['value'])
            elif object_type == 'domain-name':
                ObservableCaches.create_2_x_per_data(observable, object_value, stix_file, node_id, object_key, 'domain_name', object_value['value'])
            elif object_type == 'url':
                ObservableCaches.create_2_x_per_data(observable, object_value, stix_file, node_id, object_key, 'uri', object_value['value'])
            else:
                pass
        return

    @classmethod
    def create_2_x_per_data(cls, observable, object_, stix_file, node_id, object_key, type_, value):
        document = ObservableCaches()
        object_node_id = '%s_%s' % (node_id, object_key)
        document.observable_id = node_id
        document.title = object_node_id
        document.description = object_node_id
        document.stix_file = stix_file
        document.package_name = stix_file.package_name
        document.package_id = stix_file.package_id
        document.node_id = object_node_id
        document.object_ = object_
        if type_ == 'ipv4':
            document.ipv4_1_3, document.ipv4_4 = cls.split_ipv4_value(value)
        if type_ == 'domain_name':
            rs_system = System.objects.get()
            tld = TLD(rs_system.public_suffix_list_file_path)
            document.domain_without_tld, document.domain_tld = tld.split_domain(value)
            if document.domain_without_tld:
                document.domain_last = document.domain_without_tld.split('.')[-1]
        document.type = type_
        document.value = value
        document.number_observed = observable['number_observed']
        document.first_observed = observable['first_observed']
        document.last_observed = observable['last_observed']
        document.save()
        return

    @classmethod
    def create(cls, observable, stix_file, node_id):
        if observable is None:
            return
        document = ObservableCaches()
        document.observable_id = observable.id_
        document.title = observable.title
        if observable.description:
            document.description = observable.description.value
        object_ = observable.object_
        if object_:
            document.object_ = object_.to_dict()
            properties = object_.properties
            if properties:
                if isinstance(properties, File):
                    if properties.md5:
                        document.type = 'md5'
                        document.value = str(properties.md5)
                    elif properties.sha1:
                        document.type = 'sha1'
                        document.value = str(properties.sha1)
                    elif properties.sha256:
                        document.type = 'sha256'
                        document.value = str(properties.sha256)
                    elif properties.sha512:
                        document.type = 'sha512'
                        document.value = str(properties.sha512)
                    else:
                        print('File else')
                        return
                    if document.value is None:
                        print('Hashvalue is None')
                        return
                elif isinstance(properties, DomainName):
                    document.type = 'domain_name'
                    document.value = properties.value.value
                    if document.value is None:
                        print('Domain is None')
                        return
                    rs_system = System.objects.get()
                    tld = TLD(rs_system.public_suffix_list_file_path)
                    document.domain_without_tld, document.domain_tld = tld.split_domain(properties.value.value)
                    if document.domain_without_tld:
                        document.domain_last = document.domain_without_tld.split('.')[-1]
                elif isinstance(properties, URI):
                    if properties.type_ == 'URL':
                        document.type = 'uri'
                        document.value = properties.value.value
                    elif properties.type_ is None:
                        document.type = 'uri'
                        document.value = properties.value.value
                    else:
                        print('URI else')
                        return
                    if document.value is None:
                        print('URI is None')
                        return
                    if isinstance(document.value, list):
                        print('URI is list')
                        return
                elif isinstance(properties, Address):
                    type_, value = cls.create_address_object(properties)
                    if type_ is None:
                        print('Address else')
                        return
                    document.type = type_
                    document.value = value
                    if document.value is None:
                        print('Address is None')
                        return
                    if type_ == 'ipv4':
                        try:
                            document.ipv4_1_3, document.ipv4_4 = cls.split_ipv4_value(value)
                        except Exception:
                            return
                elif isinstance(properties, Mutex):
                    document.type = 'mutex'
                    document.value = properties.name.value
                    if document.value is None:
                        print('Mutex is None')
                        return
                elif isinstance(properties, NetworkConnection):
                    socket = properties.destination_socket_address
                    type_, value = cls.create_from_socket_object(socket)
                    document.type = type_
                    document.value = value
                    if document.value is None:
                        print('IPAddress is None')
                        return
                    if type_ == 'ipv4':
                        try:
                            document.ipv4_1_3, document.ipv4_4 = cls.split_ipv4_value(value)
                        except Exception:
                            return
                else:
                    return
            else:
                return
        else:
            return
        document.stix_file = stix_file
        document.package_name = stix_file.package_name
        document.package_id = stix_file.package_id
        document.node_id = node_id
        document.save()

    @classmethod
    def split_ipv4_value(cls, ipv4):
        octets = ipv4.split('.')
        ipv4_1_3 = ('.'.join(octets[0:3]) + '.')
        ipv4_4 = int(octets[3])
        return (ipv4_1_3, ipv4_4)

    @classmethod
    def create_from_socket_object(cls, socket):
        if socket:
            return cls.create_address_object(socket.ip_address)
        else:
            return (None, None)

    @classmethod
    def create_address_object(cls, address):
        type_ = None
        value = None
        if address.category == 'ipv4-addr':
            type_ = 'ipv4'
            value = address.address_value.value
        elif address.category == 'e-mail':
            type_ = 'email'
            value = address.address_value.value
        else:
            print('Address else')
        return (type_, value)

    @classmethod
    def find_md5(cls, md5):
        return ObservableCaches.objects.filter(type='md5', value=md5)

    @classmethod
    def find_sha1(cls, sha1):
        return ObservableCaches.objects.filter(type='sha1', value=sha1)

    @classmethod
    def find_sha256(cls, sha256):
        return ObservableCaches.objects.filter(type='sha256', value=sha256)

    @classmethod
    def find_sha512(cls, sha512):
        return ObservableCaches.objects.filter(type='sha512', value=sha512)

    @classmethod
    def find_domain_name(cls, domain_name):
        return ObservableCaches.objects.filter(type='domain_name', value=domain_name)

    @classmethod
    def find_uri(cls, uri):
        return ObservableCaches.objects.filter(type='uri', value=uri)

    @classmethod
    def find_ipv4(cls, ipv4):
        return ObservableCaches.objects.filter(type='ipv4', value=ipv4)


class SimilarScoreCache(Document):
    IPV4_SCORE_CACHE_TYPE = 'ipv4'
    DOMAIN_SCORE_CACHE_TYPE = 'domain_type'
    SCORE_CASHE_TAYPE = (
        (IPV4_SCORE_CACHE_TYPE, IPV4_SCORE_CACHE_TYPE),
        (DOMAIN_SCORE_CACHE_TYPE, DOMAIN_SCORE_CACHE_TYPE)
    )

    meta = {
        'indexes': [
            ('type', 'start_cache', 'end_cache')
        ]
    }

    @classmethod
    def create(cls, type_, start_cache, end_cache, edge_type):
        document = SimilarScoreCache()
        document.type = type_
        document.start_cache = start_cache
        document.end_cache = end_cache
        document.edge_type = edge_type
        document.save()

    type = fields.StringField(max_length=32, choices=SCORE_CASHE_TAYPE)
    start_cache = fields.ReferenceField(ObservableCaches, reverse_delete_rule=CASCADE)
    end_cache = fields.ReferenceField(ObservableCaches, reverse_delete_rule=CASCADE)
    edge_type = fields.StringField(max_length=32)


class Tags(Document):
    tag = fields.StringField(max_length=100, unique=True)
    object_ids = fields.ListField()

    @classmethod
    def create(cls, tag, object_ids):
        document = Tags()
        document.tag = tag
        document.object_ids = object_ids
        document.save()
        return

    @classmethod
    def append(cls, tag, object_id):
        try:
            document = Tags.objects.get(tag=tag)
        except DoesNotExist:
            document = Tags()
            document.tag = tag
            document.object_ids = [object_id]
            document.save()
            return
        ids = document.object_ids
        ids.append(object_id)
        ids = sorted(set(ids), key=ids.index)
        document.object_ids = ids
        document.save()
        return

    @classmethod
    def append_by_object(cls, object_):
        for label in object_['labels']:
            Tags.append(label, object_['id'])
