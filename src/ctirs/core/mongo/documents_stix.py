import stix2
import json
import pytz
import datetime
import stix2slider
import tempfile
from stix2elevator import elevate_string
from stix2elevator.options import initialize_options
from mongoengine import fields,CASCADE, DoesNotExist
from mongoengine.document import Document
from mongoengine.errors import NotUniqueError
from stix.core.stix_package import STIXPackage
from cybox.objects.file_object import File
from cybox.objects.domain_name_object import DomainName
from cybox.objects.uri_object import URI
from cybox.objects.address_object import Address
from cybox.objects.mutex_object import Mutex
from cybox.objects.network_connection_object import NetworkConnection
from ctirs.core.mongo.documents import Communities,Vias,InformationSources
from ctirs.models.rs.models import System
from stip.common.tld import TLD

#STIX2 で使われる時間文字列から datetime に変換する
def stix2_str_to_datetime(s):
    return datetime.datetime.strptime(s,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc)

class StixFiles(Document):
    #STIX 2.0->1.2 変換時の名前空間
    NS_S_TIP_NAME = 's-tip'

    VERSION_CHOICES=(
        ('1.1.1','1.1.1'),
        ('1.2','1.1.1'),
        ('2.0','2.0'),
        ('2.1','2.1'),
    )
    
    #S-TIP SNS 作成の STIX タイプを返却
    STIP_SNS_TYPE_ORIGIN = 'origin'
    STIP_SNS_TYPE_LIKE = 'like'
    STIP_SNS_TYPE_UNLIKE = 'unlike'
    STIP_SNS_TYPE_COMMENT = 'comment'
    STIP_SNS_TYPE_ATTACH = 'attach'
    STIP_SNS_TYPE_NOT = 'not'
    STIP_SNS_TYPE_UNDEFINED = 'undefined'

    SNS_TYPE_CHOICES=(
        (STIP_SNS_TYPE_ORIGIN,STIP_SNS_TYPE_ORIGIN),
        (STIP_SNS_TYPE_LIKE,STIP_SNS_TYPE_LIKE),
        (STIP_SNS_TYPE_UNLIKE,STIP_SNS_TYPE_UNLIKE),
        (STIP_SNS_TYPE_COMMENT,STIP_SNS_TYPE_COMMENT),
        (STIP_SNS_TYPE_ATTACH,STIP_SNS_TYPE_ATTACH),
        (STIP_SNS_TYPE_NOT,STIP_SNS_TYPE_NOT),
        (STIP_SNS_TYPE_UNDEFINED,STIP_SNS_TYPE_UNDEFINED),
    )
    
    version = fields.StringField(max_length=32,choices=VERSION_CHOICES)
    package_id = fields.StringField(max_length=100,unique=True)
    input_community = fields.ReferenceField(Communities)
    package_name = fields.StringField(max_length=1000,default='')
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    produced = fields.DateTimeField(default=None)
    via = fields.ReferenceField(Vias)
    origin_path = fields.StringField(max_length=1024)
    content = fields.FileField(collection_name='stix')
    generation = fields.ListField()
    comment = fields.StringField(max_length=10240,default='')
    is_post_sns = fields.BooleanField(default=True)
    is_created_by_sns = fields.BooleanField(default=False)
    related_packages = fields.ListField(default=None)
    sns_critical_infrastructure = fields.StringField(max_length=128,default='')
    sns_screen_name = fields.StringField(max_length=128,default='')
    sns_user_name = fields.StringField(max_length=128,default='')
    sns_affiliation = fields.StringField(max_length=128,default='')
    sns_sharing_range = fields.StringField(max_length=128,default='')
    sns_region_code = fields.StringField(max_length=128,default='')
    sns_instance = fields.StringField(max_length=128,default='')
    sns_type = fields.StringField(max_length=16,choices=SNS_TYPE_CHOICES,default=STIP_SNS_TYPE_UNDEFINED)
    information_source = fields.ReferenceField(InformationSources,default=None)
    post = fields.StringField(default=None)
        
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
            self.description  = ''

    @classmethod
    def rebuild_cache(cls):
        #drop
        StixIndicators.drop_collection()
        StixObservables.drop_collection()
        StixCampaigns.drop_collection()
        StixIncidents.drop_collection()
        StixThreatActors.drop_collection()
        StixExploitTargets.drop_collection()
        StixCoursesOfAction.drop_collection()
        StixTTPs.drop_collection()
        ObservableCaches.drop_collection()
        ExploitTargetCaches.drop_collection()
        SimilarScoreCache.drop_collection()

        #rebuild
        for stix in StixFiles.objects.all().timeout(False):
            stix.split_child_nodes()
            #produced が指定なしの場合は格納する
            if stix.produced is None:
                stix_package = STIXPackage.from_xml(stix.origin_path)
                #STIX Pacakge のタイムスタンプがあれば採用
                if stix_package.timestamp is not None:
                    stix.produced = stix_package.timestamp
                else:
                    #なければcreatedと同じ
                    stix.produced = stix.created
                stix.save()
        return

    #STIX が v2 であるか判断する
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
        document.content = content
        document.created = document.modified = now
        if document.is_stix_v2() == True:
            #STIX 2.x の場合
            #package_id と同様
            document.package_name = document.package_id
        else:
            #STIX 1.x の場合
            #指定があればpackage_name/なければGridFsのID
            document.package_name = package_bean.package_name if package_bean.package_name is not None else str(document.content.grid_id)
        document.generation.append(document.content.grid_id)
        #producedの指定がある場合はその時間。存在しない場合はcreatedと同様の時間を格納
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
        #information_source を設定する
        document.set_information_source()
        return document

    @classmethod
    def delete_by_id(cls,id_):
        #documentを削除し、origin_pathを返却
        o = StixFiles.objects.get(id=id_)
        o.delete()
        return o.origin_path

    @classmethod
    def delete_by_package_id(cls,package_id):
        #documentを削除し、origin_pathを返却
        o = StixFiles.objects.get(package_id=package_id)
        o.delete()
        return o.origin_path
    
    #Instance名とunique名の複合文字列を返却する
    def get_unique_name(self):
        if self.sns_instance is None:
            return self.sns_user_name
        #半角空白を挟んだ文字列とする
        return '%s %s' % (self.sns_instance,self.sns_user_name)

    def get_stix_package(self):
        if self.origin_path is None:
            return None
        try:
            return STIXPackage.from_xml(self.origin_path)
        except:
            return None

    #子ノード情報分割とキャッシュ作成
    #origin_pathがあることが前提
    def split_child_nodes(self):
        #stix_packageを取得する
        stix_package = self.get_stix_package()
        #None以外の場合は STIX 1.x 系
        if stix_package is not None:
            self.split_child_nodes_stix_1_x(stix_package)
        else:
            self.split_child_nodes_stix_2_x()
        return

    #stix 2.x 系の分解
    def split_child_nodes_stix_2_x(self):
        try:
            f = open(self.origin_path,'r')
            j = json.load(f)
            objects = j['objects']
            for object_ in objects:
                type_ = object_['type']
                #Attack Pattern
                if type_ == 'attack-pattern':
                    StixAttackPatterns.create(object_,self)
                elif type_ == 'campaign':
                    StixCampaignsV2.create(object_,self)
                elif type_ == 'course-of-action':
                    StixCoursesOfActionV2.create(object_,self)
                elif type_ == 'identity':
                    StixIdentities.create(object_,self)
                elif type_ == 'indicator':
                    StixIndicators.create_2_x(object_,self)
                elif type_ == 'intrusion-set':
                    StixIntrusionSets.create(object_,self)
                elif type_ == 'location':
                    StixLocations.create(object_,self)
                elif type_ == 'malware':
                    StixMalwares.create(object_,self)
                elif type_ == 'note':
                    StixNotes.create(object_,self)
                elif type_ == 'observed-data':
                    StixObservables.create_2_x(object_,self)
                elif type_ == 'opinion':
                    StixOpinions.create(object_,self)
                elif type_ == 'report':
                    StixReports.create(object_,self)
                elif type_ == 'threat-actor':
                    StixThreatActorsV2.create(object_,self)
                elif type_ == 'tool':
                    StixTools.create(object_,self)
                elif type_ == 'vulnerability':
                    StixVulnerabilities.create(object_,self)
                elif type_ == 'relationship':
                    StixRelationships.create(object_,self)
                elif type_ == 'sighting':
                    StixSightings.create(object_,self)
                elif type_ == 'language-content':
                    StixLanguageContents.create(object_,self)
                else:
                    StixOthers.create(object_,self)
            f.close()
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    #stix 1.x 系の分解
    def split_child_nodes_stix_1_x(self,stix_package):
        #indicators の中の Observable を追加
        indicators = stix_package.indicators
        if indicators is not None:
            #indicator の 回数だけ繰り返す
            for indicator in indicators:
                if indicator is not None:
                    #StixIndicatorとキャッシュを作成する
                    try:
                        StixIndicators.create(indicator,self)
                    except NotUniqueError:
                        pass

        #Observables の中の Observable を追加
        observables = stix_package.observables
        if observables is not None:
            for observable in observables:
                if observable is not None:
                    try:
                        #StixObservableとキャッシュを作成する
                        StixObservables.create(observable,self)
                    except NotUniqueError:
                        pass

        #Campaigns の中の Campaign を追加
        campaigns = stix_package.campaigns
        if campaigns is not None:
            for campaign in campaigns:
                if campaign is not None:
                    try:
                        #StixCampaignsを作成する
                        StixCampaigns.create(campaign,self)
                    except NotUniqueError:
                        pass

        #Incidents の中の Incident を追加
        incidents = stix_package.incidents
        if incidents is not None:
            for incident in incidents:
                if incident is not None:
                    try:
                        #StixIncidentsを作成する
                        StixIncidents.create(incident,self)
                    except NotUniqueError:
                        pass

        #ThreatActors の中の ThreatActor を追加
        threat_actors = stix_package.threat_actors
        if threat_actors is not None:
            for threat_actor in threat_actors:
                if threat_actor is not None:
                    try:
                        #StixThreatActorsを作成する
                        StixThreatActors.create(threat_actor,self)
                    except NotUniqueError:
                        pass

        #ExpoitTargets の中の ExploitTarget を追加
        exploit_targets = stix_package.exploit_targets
        if exploit_targets is not None:
            for exploit_target in exploit_targets:
                if exploit_target is not None:
                    try:
                        #StixExploitTargetsとキャッシュを作成する
                        StixExploitTargets.create(exploit_target,self)
                    except NotUniqueError:
                        pass

        #CoursesOfactions の中の CoursesOfaction を追加
        courses_of_action = stix_package.courses_of_action
        if courses_of_action is not None:
            for course_of_action in courses_of_action:
                if course_of_action is not None:
                    try:
                        #StixCoursesOfActionを作成する
                        StixCoursesOfAction.create(course_of_action,self)
                    except NotUniqueError:
                        pass

        #TTPs の中の TTP を追加
        ttps = stix_package.ttps
        if ttps is not None:
            for ttp in ttps:
                if ttp is not None:
                    try:
                        #StixTTPsを作成する
                        StixTTPs.create(ttp,self)
                    except NotUniqueError:
                        pass

    #REST APIで返却するjson documentを取得
    def get_rest_api_document_info(self,required_comment=False):
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
        if required_comment == True:
            d['comment'] = self.comment
        return d

    #Pakcage_name_listで返却する名前を取得
    def get_rest_api_package_name_info(self):
        d = {}
        d['package_id'] = self.package_id
        d['package_name'] = self.package_name
        return d

    def get_rest_api_document_content(self):
        return {'content':self.content.read()}
 
    #WebHook返却するjson documentを取得
    def get_webhook_document(self):
        return self.get_rest_api_document_info()
    
    def get_datetime_string(self,d):
        return str(d)
    
    #STIX version 2.0 のドキュメントを 1.x にして中身を返却
    #2.0以外の場合は None を返却
    def get_slide_1_x(self):
        if self.version == "2.0":
            stix2slider.convert_stix._ID_NAMESPACE = self.NS_S_TIP_NAME
            from stix2slider.options import initialize_options
            initialize_options()
            return stix2slider.slide_file(self.origin_path)
        return None

    #STIX version 1.x のドキュメントを 2.0 にして中身を返却
    #1.0以外の場合は None を返却
    def get_elevate_2_x(self):
        if self.version != "2.0":
            src = self.content.read()
            initialize_options()
            return elevate_string(src)
        return None

    #InformationSource を設定する
    def set_information_source(self):
        if self.sns_instance is None:
            return
        if len(self.sns_instance) == 0:
            return
        information_source_name =  self.sns_instance
        try:
            information_source = InformationSources.objects.get(name=information_source_name)
        except:
            information_source = InformationSources.create(information_source_name)
        self.information_source = information_source
        self.save()

    def to_dict(self):
        d = {
            'version'           :   self.version,
            'package_id'        :   self.package_id,
            'input_community'   :   self.input_community.name,
            'package_name'      :   self.package_name,
            'created'           :   self.created,
            'modified'          :   self.modified,
            'produced'          :   self.produced,
            'comment'           :   self.comment,
            }
        return d

#IndicatorsV2Cachees
class IndicatorV2Caches(Document):
    indicator_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    pattern = fields.StringField(max_length=1024)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)
    package_name = fields.StringField(max_length=1024)
    package_id = fields.StringField(max_length=100)
    node_id = fields.StringField(max_length=100)

    @classmethod
    def create(cls,indicator,stix_file,node_id):
        if indicator is None:
            return
        document = IndicatorV2Caches()
        if ('id' in indicator) == True:
            document.indicator_id = indicator['id']
        if ('name' in indicator) == True:
            document.title = indicator['name']
        if ('description' in indicator) == True:
            document.description = indicator['description']
        if ('pattern' in indicator) == True:
            document.pattern = indicator['pattern']
        document.object_ = indicator
        document.stix_file = stix_file
        document.package_name = stix_file.package_name
        document.package_id = stix_file.package_id
        document.node_id = node_id
        document.save()
        return document

####################### STIX 2.x  #######################
class Stix2Base(Document):
    #STIX 2.x 規定の共通プロパティ
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

    #S-TIP 独自共通プロパティ
    object_ = fields.DictField()
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)    
    package_name = fields.StringField(max_length=1024)
    package_id = fields.StringField(max_length=100)
    
    meta = {
        'allow_inheritance' : True,
        'abstract' : True,
        'indexes': [
            ('$object_id_')
        ]
    }

    @classmethod
    def get_lists_or_string(cls,value):
        l = []
        if isinstance(value,list) == True:
            for item in value:
                l.append(item)
        else:
            l.append(value)
        return l

    @classmethod
    def create(cls,document,object_,stix_file):
        if ('id' in object_) == True:
            document.object_id_ = object_['id']
        if ('spec_version' in object_) == True:
            document.spec_version = object_['spec_version']
        if ('created_by_ref' in object_) == True:
            document.created_by_ref = object_['created_by_ref']
        if ('created' in object_) == True:
            document.created = stix2_str_to_datetime(object_['created'])
        if ('modified' in object_) == True:
            document.modified = stix2_str_to_datetime(object_['modified'])
        if ('revoked' in object_) == True:
            document.revoked = object_['revoked']
        if ('labels' in object_) == True:
            document.labels = Stix2Base.get_lists_or_string(object_['labels'])
        if ('confidence' in object_) == True:
            document.confidence = object_['confidence']
        if ('lang' in object_) == True:
            document.lang = object_['lang']
        if ('external_references' in object_) == True:
            document.external_references = Stix2Base.get_lists_or_string(object_['external_references'])
        if ('object_marking_refs' in object_) == True:
            document.object_marking_refs = Stix2Base.get_lists_or_string(object_['object_marking_refs'])
        if ('granular_markings' in object_) == True:
            document.granular_markings = Stix2Base.get_lists_or_string(object_['granular_markings'])
        document.object_ = object_
        document.stix_file = stix_file
        document.package_name = stix_file.package_name
        document.package_id = stix_file.package_id
        return document

#attack-pattern
class StixAttackPatterns(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    kill_chain_phases = fields.ListField()

    meta = {
        'collection' : 'stix_attack_patterns',
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixAttackPatterns()
        document = super(StixAttackPatterns,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('kill_chain_phases' in object_) == True:
            document.kill_chain_phases = Stix2Base.get_lists_or_string(object_['kill_chain_phases'])
        document.save()
        return document

#campaign (STIX 2.0)
class StixCampaignsV2(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    aliases = fields.ListField()
    first_seen = fields.DateTimeField()
    last_seen = fields.DateTimeField()
    objective = fields.StringField(max_length=10240)
    
    meta = {
        'collection' : 'stix_campaigns_v2'
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixCampaignsV2()
        document = super(StixCampaignsV2,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('aliases' in object_) == True:
            document.aliases = Stix2Base.get_lists_or_string(object_['aliases'])
        if ('first_seen' in object_) == True:
            document.first_seen = stix2_str_to_datetime(object_['first_seen'])
        if ('last_seen' in object_) == True:
            document.last_seen = stix2_str_to_datetime(object_['last_seen'])
        if ('objective' in object_) == True:
            document.objective = object_['objective']
        document.save()
        return document

#courses-of-action (STIX 2.0)
class StixCoursesOfActionV2(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    #RESERVED
    action = fields.StringField(max_length=10240)
    
    meta = {
        'collection' : 'stix_courses_of_action_v2'
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixCoursesOfActionV2()
        document = super(StixCoursesOfActionV2,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        document.save()
        return document

#Identity
class StixIdentities(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    identity_class = fields.StringField(max_length=1024)
    sectors = fields.ListField()
    contact_information = fields.StringField(max_length=1024)

    meta = {
        'collection' : 'stix_identities',
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixIdentities()
        document = super(StixIdentities,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('identity_class' in object_) == True:
            document.identity_class = object_['identity_class']
        if ('contact_information' in object_) == True:
            document.contact_information = object_['contact_information']
        if ('sectors' in object_) == True:
            document.sectors = Stix2Base.get_lists_or_string(object_['sectors'])
        document.save()
        return document

#indicator (STIX 2.0)
class StixIndicatorsV2(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    pattern = fields.StringField(max_length=10240)
    valid_from = fields.DateTimeField()
    valid_until = fields.DateTimeField()
    kill_chain_phases = fields.ListField()
    
    meta = {
        'collection' : 'stix_indicators_v2'
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixIndicatorsV2()
        document = super(StixIndicatorsV2,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('pattern' in object_) == True:
            document.pattern = object_['pattern']
        if ('valid_from' in object_) == True:
            document.valid_from = stix2_str_to_datetime(object_['valid_from'])
        if ('valid_until' in object_) == True:
            document.valid_until = stix2_str_to_datetime(object_['valid_until'])
        if ('kill_chain_phases' in object_) == True:
            document.kill_chain_phases = Stix2Base.get_lists_or_string(object_['kill_chain_phases'])
        document.save()
        return document

#intrusion-set
class StixIntrusionSets(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    aliases = fields.ListField()
    first_seen = fields.DateTimeField()
    last_seen = fields.DateTimeField()
    goals = fields.ListField()
    resource_level = fields.StringField(max_length=1024)
    primary_motivation = fields.StringField(max_length=1024)
    secondary_motivations = fields.ListField()

    meta = {
        'collection' : 'stix_intrusion_sets',
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixIntrusionSets()
        document = super(StixIntrusionSets,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('aliases' in object_) == True:
            document.aliases = Stix2Base.get_lists_or_string(object_['aliases'])
        if ('first_seen' in object_) == True:
            document.first_seen = stix2_str_to_datetime(object_['first_seen'])
        if ('last_seen' in object_) == True:
            document.last_seen = stix2_str_to_datetime(object_['last_seen'])
        if ('goals' in object_) == True:
            document.goals = Stix2Base.get_lists_or_string(object_['goals'])
        if ('resource_level' in object_) == True:
            document.resource_level = object_['resource_level']
        if ('primary_motivation' in object_) == True:
            document.primary_motivation = object_['primary_motivation']
        if ('secondary_motivations' in object_) == True:
            document.secondary_motivations = Stix2Base.get_lists_or_string(object_['secondary_motivations'])
        document.save()
        return document

#location
class StixLocations(Stix2Base):
    #STIX 2.1 規定の独自プロパティ
    description = fields.StringField(max_length=10240)
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
        'collection' : 'stix_locations',
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixLocations()
        document = super(StixLocations,cls).create(document,object_,stix_file)
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('latitude' in object_) == True:
            document.latitude = float(object_['latitude'])
        if ('longitude' in object_) == True:
            document.longitude = float(object_['longitude'])
        if ('precision' in object_) == True:
            document.precision = float(object_['precision'])
        if ('region' in object_) == True:
            document.region = object_['region']
        if ('country' in object_) == True:
            document.country = object_['country']
        if ('administrative_area' in object_) == True:
            document.administrative_area = object_['administrative_area']
        if ('city' in object_) == True:
            document.city = object_['city']
        if ('code' in object_) == True:
            document.code = object_['code']
        if ('postal_code' in object_) == True:
            document.postal_code = object_['postal_code']
        document.save()
        return document

#malware
class StixMalwares(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    kill_chain_phases = fields.ListField()

    meta = {
        'collection' : 'stix_malwares',
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixMalwares()
        document = super(StixMalwares,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('kill_chain_phases' in object_) == True:
            document.kill_chain_phases = Stix2Base.get_lists_or_string(object_['kill_chain_phases'])
        document.save()
        return document

#note
class StixNotes(Stix2Base):
    #STIX 2.01規定の独自プロパティ
    abstract = fields.StringField(max_length=1024)
    content = fields.StringField(max_length=10240)
    authors = fields.ListField()
    object_refs = fields.ListField()

    meta = {
        'collection' : 'stix_notes',
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixNotes()
        document = super(StixNotes,cls).create(document,object_,stix_file)
        if ('abstract' in object_) == True:
            document.abstract = object_['abstract']
        if ('content' in object_) == True:
            document.content = object_['content']
        if ('authors' in object_) == True:
            document.authors = Stix2Base.get_lists_or_string(object_['authors'])
        if ('object_refs' in object_) == True:
            document.object_refs = Stix2Base.get_lists_or_string(object_['object_refs'])
        document.save()
        return document

#observed-data
class StixObservedData(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    first_observed = fields.DateTimeField(default=datetime.datetime.now)
    last_observed = fields.DateTimeField(default=datetime.datetime.now)
    number_observed = fields.IntField()
    objects_ = fields.DictField()

    meta = {
        'collection' : 'stix_observed_data'
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixObservedData()
        document = super(StixObservedData,cls).create(document,object_,stix_file)
        if ('first_observed' in object_) == True:
            document.first_observed = stix2_str_to_datetime(object_['first_observed'])
        if ('last_observed' in object_) == True:
            document.last_observed = stix2_str_to_datetime(object_['last_observed'])
        if ('number_observed' in object_) == True:
            document.number_observed = object_['number_observed']
        if ('objects' in object_) == True:
            document.objects_ = object_['objects']
        document.save()
        return document

#opinion
class StixOpinions(Stix2Base):
    #STIX 2.1 規定の独自プロパティ
    explanation = fields.StringField(max_length=10240)
    authors = fields.ListField()
    object_refs = fields.ListField()
    opinion = fields.StringField(max_length=10240)
    
    meta = {
        'collection' : 'stix_opinions'
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixOpinions()
        document = super(StixOpinions,cls).create(document,object_,stix_file)
        if ('explanation' in object_) == True:
            document.explanation = object_['explanation']
        if ('authors' in object_) == True:
            document.authors = Stix2Base.get_lists_or_string(object_['authors'])
        if ('object_refs' in object_) == True:
            document.object_refs = Stix2Base.get_lists_or_string(object_['object_refs'])
        if ('opinion' in object_) == True:
            document.opinion = object_['opinion']
        document.save()
        return document

#report
class StixReports(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    published = fields.DateTimeField()
    object_refs = fields.ListField()
    
    meta = {
        'collection' : 'stix_reports'
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixReports()
        document = super(StixReports,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('published' in object_) == True:
            document.published = stix2_str_to_datetime(object_['published'])
        if ('object_refs' in object_) == True:
            document.object_refs = Stix2Base.get_lists_or_string(object_['object_refs'])
        document.save()
        return document

#threat-actor (STIX 2.0)
class StixThreatActorsV2(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    aliases = fields.ListField()
    roles = fields.ListField()
    goals = fields.ListField()
    sophistication = fields.StringField(max_length=1024)
    resource_level = fields.StringField(max_length=1024)
    primary_motivation = fields.StringField(max_length=1024)
    secondary_motivations = fields.ListField()
    personal_motivations = fields.ListField()
    
    meta = {
        'collection' : 'stix_threat_actors_v2'
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixThreatActorsV2()
        document = super(StixThreatActorsV2,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('aliases' in object_) == True:
            document.aliases = Stix2Base.get_lists_or_string(object_['aliases'])
        if ('roles' in object_) == True:
            document.roles = Stix2Base.get_lists_or_string(object_['roles'])
        if ('goals' in object_) == True:
            document.goals = Stix2Base.get_lists_or_string(object_['goals'])
        if ('sophistication' in object_) == True:
            document.sophistication = object_['sophistication']
        if ('resource_level' in object_) == True:
            document.resource_level = object_['resource_level']
        if ('primary_motivation' in object_) == True:
            document.primary_motivation = object_['primary_motivation']
        if ('secondary_motivations' in object_) == True:
            document.secondary_motivations = Stix2Base.get_lists_or_string(object_['secondary_motivations'])
        if ('personal_motivations' in object_) == True:
            document.personal_motivations = Stix2Base.get_lists_or_string(object_['personal_motivations'])
        document.save()
        return document

#tool
class StixTools(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    kill_chain_phases = fields.ListField()
    tool_version = fields.StringField(max_length=1024)

    meta = {
        'collection' : 'stix_tools',
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixTools()
        document = super(StixTools,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('kill_chain_phases' in object_) == True:
            document.kill_chain_phases = Stix2Base.get_lists_or_string(object_['kill_chain_phases'])
        if ('tool_version' in object_) == True:
            document.tool_version = object_['tool_version']
        document.save()
        return document
    
#Vulnerablity
class StixVulnerabilities(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    name = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)

    #S-TIP 独自共通プロパティ
    cves = fields.ListField()
    
    meta = {
        'collection' : 'stix_vulnerabilities'
    }

    @classmethod
    #cve_id単位で追加する
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixVulnerabilities()
        document = super(StixVulnerabilities,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        #external_references の中から CVE 情報を抽出
        if ('external_references' in object_) == True:
            cves = []
            for external_reference in object_['external_references']:
                if 'source_name' in external_reference:
                    if external_reference['source_name'] == 'cve':
                        if ('external_id' in external_reference) == True:
                            cves.append(external_reference['external_id'])
            document.cves = cves
        document.save()
        #cache 登録する
        ExploitTargetCaches.create_2_x(document)
        return document

#relationship
class StixRelationships(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    relationship_type = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=1024)
    source_ref = fields.StringField(max_length=1024)
    target_ref = fields.StringField(max_length=1024)

    meta = {
        'collection' : 'stix_relationships'
    }

    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixRelationships()
        document = super(StixRelationships,cls).create(document,object_,stix_file)
        if ('relationship_type' in object_) == True:
            document.relationship_type = object_['relationship_type']
        if ('description' in object_) == True:
            document.description = object_['description']
        if ('source_ref' in object_) == True:
            document.source_ref = object_['source_ref']
        if ('target_ref' in object_) == True:
            document.target_ref = object_['target_ref']
        document.save()
        return document
#sighting
class StixSightings(Stix2Base):
    #STIX 2.0 規定の独自プロパティ
    first_seen = fields.DateTimeField()
    last_seen = fields.DateTimeField()
    count = fields.IntField()
    sighting_of_ref = fields.StringField(max_length=100)
    observed_data_refs = fields.ListField()
    where_sighted_refs = fields.ListField()
    summary = fields.BooleanField(default=False)
    
    meta = {
        'collection' : 'stix_sightings'
    }

    @classmethod
    #Observed-data 指定の sighting 情報から作成する
    #STIX File regist 経由ではないので file 情報はない
    def create_by_observed_id(cls,first_seen,last_seen,count,observed_data_id,uploader):
        SIGHTING_IDENTITY_NAME = 'Fujitsu System Integration Laboratories.'
        SIGHTING_IDENTITY_IDENTITY_CLASS = 'organization'
        stix_file_path = None
        try:
            #sighting の identity を追加する
            sighting_identity = stix2.Identity(
                name = SIGHTING_IDENTITY_NAME,
                identity_class = SIGHTING_IDENTITY_IDENTITY_CLASS,
            )
            if count != 0:
                sighting = stix2.Sighting(
                    first_seen=first_seen,
                    last_seen=last_seen,
                    count = count,
                    created_by_ref = sighting_identity,
                    sighting_of_ref=observed_data_id)
            else:
                sighting = stix2.Sighting(
                    first_seen=first_seen,
                    last_seen=last_seen,
                    created_by_ref = sighting_identity,
                    sighting_of_ref=observed_data_id)
            #指定の obserbed_data_id から observable-data,最新の一つを取得する
            observed_data_document = next(StixObservedData.objects.filter(object_id_=observed_data_id).order_by('modified').limit(1))
            observed_data = stix2.parse(json.dumps(observed_data_document.object_))
            
            #observed_data に created_by_ref があれば追加する
            observed_data_identity = None
            if hasattr(observed_data,'created_by_ref'):
                try:
                    #最新の一つを取得する
                    identity_document = next(StixIdentities.objects.filter(identity_id=observed_data.created_by_ref).order_by('modified').limit(1))
                    observed_data_identity = stix2.parse(json.dumps(identity_document.object_))
                except:
                    #identity が見つからない場合はパスする　
                    pass
            
            #bundle 作成
            if observed_data_identity is not None:
                bundle = stix2.Bundle(observed_data,sighting,observed_data_identity,sighting_identity)
            else:
                bundle = stix2.Bundle(observed_data,sighting,sighting_identity)

            from ctirs.core.stix.regist import regist
            #一時ファイルに保存
            _,stix_file_path = tempfile.mkstemp(suffix='.json')
            content = bundle.serialize(indent=4)
            with open(stix_file_path,'w') as fp:
                fp.write(content)
            #bundle を登録
            community = Communities.get_not_assign_community()
            via = Vias.get_not_assign_via(uploader=uploader.id)
            #regist の中で StixSightings を create する
            #regist の中でファイルは削除される
            regist(stix_file_path,community,via)
            return sighting.id, json.loads(content)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
        
    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixSightings()
        document = super(StixSightings,cls).create(document,object_,stix_file)
        if ('first_seen' in object_) == True:
            document.first_seen = object_['first_seen']
        if ('last_seen' in object_) == True:
            document.last_seen = object_['last_seen']
        if ('count' in object_) == True:
            document.count = object_['count']
        if ('summary' in object_) == True:
            document.summary = object_['summary']
        if ('sighting_of_ref' in object_) == True:
            document.sighting_of_ref = object_['sighting_of_ref']
        if ('where_sighted_refs' in object_) == True:
            document.where_sighted_refs = object_['where_sighted_refs']
        if ('observed_data_refs' in object_) == True:
            document.observed_data_refs = object_['observed_data_refs']
        document.save()
        return document

#Language-Content
class StixLanguageContents(Stix2Base):
    #STIX 2.1規定の独自プロパティ
    object_ref = fields.StringField(max_length=1024)
    object_modified = fields.DateTimeField(default=datetime.datetime.now)
    contents = fields.DictField()
    meta = {
        'collection' : 'stix_language_contents',
    }
    @classmethod
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixLanguageContents()
        document = super(StixLanguageContents,cls).create(document,object_,stix_file)
        if ('object_ref' in object_) == True:
            document.object_ref = object_['object_ref']
        if ('object_modified' in object_) == True:
            document.object_modified = stix2_str_to_datetime(object_['object_modified'])
        if ('contents' in object_) == True:
            document.contents = object_['contents']
        document.save()
        return document

#その他
class StixOthers(Stix2Base):
    meta = {
        'collection' : 'stix_others'
    }

    @classmethod
    #cve_id単位で追加する
    def create(cls,object_,stix_file):
        if object_ is None:
            return None
        document = StixOthers()
        document = super(StixOthers,cls).create(document,object_,stix_file)
        if ('name' in object_) == True:
            document.name = object_['name']
        if ('description' in object_) == True:
            document.description = object_['description']
        document.save()
        return document

####################### STIX 1.x  #######################
#StixIndicators
class StixIndicators(Document):
    indicator_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)
    v2_indicator = fields.ReferenceField(StixIndicatorsV2,reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#indicator_id'),
        ]
    }

    @classmethod
    def create(cls,indicator,stix_file):
        document = StixIndicators()
        document.indicator_id = indicator.id_
        document.title = indicator.title
        if indicator.description is not None:
            document.description = indicator.description.value
        document.object_ = indicator.to_dict()
        document.stix_file = stix_file
        #Timestamp指定がある場合はその時間を格納
        if indicator.timestamp is not None:
            document.created = indicator.timestamp
            document.modified = indicator.timestamp
        document.save()
        #ObservableCaches作成
        ObservableCaches.create(indicator.observable,stix_file,indicator.id_)
        return

    @classmethod
    #STIX 2.x 系
    def create_2_x(cls,indicator,stix_file):
        v2_indicator = StixIndicatorsV2.create(indicator,stix_file)
        document = StixIndicators()
        if ('id' in indicator) == True:
            document.indicator_id = indicator['id']
        if ('name' in indicator) == True:
            document.title = indicator['name']
        if ('description' in indicator) == True:
            document.description = indicator['description']
        if ('created' in indicator) == True:
            try:
                d = stix2_str_to_datetime(indicator['created'])
                document.created = d
            except:
                None
        if ('modified' in indicator) == True:
            try:
                d = stix2_str_to_datetime(indicator['modified'])
                document.modified = d
            except:
                None
        document.object_ = indicator
        document.stix_file = stix_file
        document.v2_indicator = v2_indicator
        document.save()
        #IndicatorCaches作成
        IndicatorV2Caches.create(indicator,stix_file,indicator['id'])
        return
    
#StixObservables
class StixObservables(Document):
    observable_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)
    v2_observed_data = fields.ReferenceField(StixObservedData,reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#observable_id'),
        ]
    }

    @classmethod
    def create(cls,observable,stix_file):
        document = StixObservables()
        document.observable_id = observable.id_
        document.title = observable.title
        if observable.description is not None:
            document.description = observable.description.value
        try:
            document.object_ = observable.object_.to_dict()
        except AttributeError:
            document.object_ = None
        document.stix_file = stix_file
        document.save()
        #ObservableCaches作成
        if document.object_ is not None:
            ObservableCaches.create(observable,stix_file,observable.id_)
        return

    @classmethod
    #STIX 2.x 系
    def create_2_x(cls,observable,stix_file):
        v2_observed_data = StixObservedData.create(observable,stix_file)
        document = StixObservables()
        if ('id' in observable) == True:
            document.observable_id = observable['id']
            #document.v2_observable_id = observable['id']
            #STIX 2.x の observed-data には title, descriptionがないので id をいれる
            document.title = observable['id']
            document.description = observable['id']
        document.object_ = observable
        if ('created' in observable) == True:
            try:
                d = stix2_str_to_datetime(observable['created'])
                document.created = d
            except:
                None
        if ('modified' in observable) == True:
            try:
                d = stix2_str_to_datetime(observable['modified'])
                document.modified = d
            except:
                None
        document.stix_file = stix_file
        document.v2_observed_data = v2_observed_data
        document.save()

        #ObservableCaches 作成
        ObservableCaches.create_2_x(observable,stix_file,observable['id'])
        return

#StixCampaigns
class StixCampaigns(Document):
    campaign_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#campaign_id'),
        ]
    }

    @classmethod
    def create(cls,campaign,stix_file):
        document = StixCampaigns()
        document.campaign_id = campaign.id_
        document.title = campaign.title
        if campaign.description is not None:
            document.description = campaign.description.value
        document.object_ = campaign.to_dict()
        document.stix_file = stix_file
        document.save()
        return

#StixIncident
class StixIncidents(Document):
    incident_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#incident_id'),
        ]
    }

    @classmethod
    def create(cls,incident,stix_file):
        document = StixIncidents()
        document.incident_id = incident.id_
        document.title = incident.title
        if incident.description is not None:
            document.description = incident.description.value
        document.object_ = incident.to_dict()
        document.stix_file = stix_file
        document.save()
        return

#StixThreatActors
class StixThreatActors(Document):
    ta_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#ta_id'),
        ]
    }

    @classmethod
    def create(cls,ta,stix_file):
        document = StixThreatActors()
        document.ta_id = ta.id_
        document.title = ta.title
        if ta.description is not None:
            document.description = ta.description.value
        document.object_ = ta.to_dict()
        document.stix_file = stix_file
        document.save()
        return

#StixExploitTargets
class StixExploitTargets(Document):
    et_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)
    cve_ids = fields.ListField()

    meta = {
        'indexes': [
            ('#et_id'),
        ]
    }

    @classmethod
    def create(cls,et,stix_file):
        document = StixExploitTargets()
        document.et_id = et.id_
        document.title = et.title
        if et.description is not None:
            document.description = et.description.value
        document.object_ = et.to_dict()
        if et.vulnerabilities is not None:
            for vulnerability in et.vulnerabilities:
                try:
                    document.cve_ids.append(vulnerability.cve_id)
                except:
                    pass
        document.stix_file = stix_file
        document.save()
        #ExploitTargetCaches作成
        ExploitTargetCaches.create(et,stix_file,et.id_)
        return

#StixCoursesOfAction
class StixCoursesOfAction(Document):
    coa_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)

    meta = {
        'indexes': [
            ('#coa_id'),
        ]
    }

    @classmethod
    def create(cls,coa,stix_file):
        document = StixCoursesOfAction()
        document.coa_id = coa.id_
        document.title = coa.title
        if coa.description is not None:
            document.description = coa.description.value
        document.object_ = coa.to_dict()
        document.stix_file = stix_file
        document.save()
        return

#StixTtps
class StixTTPs(Document):
    ttp_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)
    
    meta = {
        'collection': 'stix_ttps',
        'indexes': [
            ('#ttp_id'),
        ]
    }

    @classmethod
    def create(cls,ttp,stix_file):
        document = StixTTPs()
        document.ttp_id = ttp.id_
        document.title = ttp.title
        if ttp.description is not None:
            document.description = ttp.description.value
        document.object_ = ttp.to_dict()
        document.stix_file = stix_file
        document.save()
        #ExploitTargetCaches作成
        if ttp.exploit_targets is not None:
            for et in ttp.exploit_targets:
                ExploitTargetCaches.create(et.item,stix_file,ttp.id_)
        return

#ExpoitTargetCaches
class ExploitTargetCaches(Document):
    TYPE_CHOICES=(
        ('cve_id','cve_id'),
    )
    type = fields.StringField(max_length=16,choices=TYPE_CHOICES)
    et_id = fields.StringField(max_length=100,unique=True)
    title = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)
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
    #cve_id単位で追加する
    def create(cls,et,stix_file,node_id):
        #vulerabilities がない場合は何もしない
        if 'vulnerabilities' not in dir(et):
            return
        if et.vulnerabilities is None:
            return
        for vulnerability in et.vulnerabilities:
            #CVE情報がなかったら何もしない
            if vulnerability.cve_id is None:
                continue
            document = ExploitTargetCaches()
            document.type = 'cve_id'
            document.et_id = et.id_
            document.title = et.title
            if et.description is not None:
                document.description = et.description.value
            document.value = vulnerability.cve_id
            document.stix_file = stix_file
            document.package_name = stix_file.package_name
            document.package_id = stix_file.package_id
            document.node_id = node_id
            document.save()
        return

    @classmethod
    def create_2_x(cls,stix_vulnerability):
        #cve が含まれていない場合は何もしない
        if stix_vulnerability.cves is None:
            return
        if len(stix_vulnerability.cves) == 0:
            return
        #cves の要素だけ cache 作成する
        for cve in stix_vulnerability.cves:
            #node_id = u'%s-%s' % (stix_vulnerability.vulnerability_id,cve)
            node_id = '%s-%s' % (stix_vulnerability.object_id_,cve)
            document = ExploitTargetCaches()
            document.type = 'cve_id'
            document.et_id = node_id
            document.title = stix_vulnerability.name
            if stix_vulnerability.description is not None:
                document.description = stix_vulnerability.description
            document.value = cve
            document.stix_file = stix_vulnerability.stix_file
            document.package_name = stix_vulnerability.package_name
            document.package_id = stix_vulnerability.package_id
            document.node_id = node_id
            document.save()
        return

#ObseravbleCache
class ObservableCaches(Document):
    TYPE_CHOICES=(
        ('uri','uri'),
        ('domain_name','domain_name'),
        ('md5','md5'),
        ('sha1','sha1'),
        ('sha256','sha256'),
        ('sha512','sha512'),
        ('ipv4','ipv4'),
        ('email','email'),
        ('mutex','mutex'),
    )

    meta = {
        'indexes': [
            ('package_id','type','ipv4_1_3'),
            ('package_id','type','domain_tld','domain_last'),
        ]
    }

    type = fields.StringField(max_length=16,choices=TYPE_CHOICES)
    observable_id = fields.StringField(max_length=100)
    title = fields.StringField(max_length=1024)
    value = fields.StringField(max_length=1024)
    description = fields.StringField(max_length=10240)
    object_ = fields.DictField()
    created = fields.DateTimeField(default=datetime.datetime.now)
    modified = fields.DateTimeField(default=datetime.datetime.now)
    stix_file = fields.ReferenceField(StixFiles,reverse_delete_rule=CASCADE)
    package_name = fields.StringField(max_length=1024)
    package_id = fields.StringField(max_length=100)
    node_id = fields.StringField(max_length=100)
    #IPv4 の場合だけ使用
    ipv4_1_3 = fields.StringField(max_length=12,null=True)
    ipv4_4 = fields.IntField(default=-1)
    #domainの場合だけ使用
    domain_tld = fields.StringField(max_length=50,null=True)
    domain_last = fields.StringField(max_length=1024,null=True)
    domain_without_tld = fields.StringField(max_length=1024,null=True)
    #STIX 2.0 の場合だけ使用
    first_observed = fields.StringField(default=None,null=True)
    last_observed = fields.StringField(default=None,null=True)
    number_observed = fields.IntField(default=1)
    

    @classmethod
    #すでにstix_fileにはorigin_pathが格納されている状態とする
    def get_stix_package(cls,stix_file):
        if stix_file is None:
            return None
        if stix_file.origin_path is None:
            return None
        return STIXPackage.from_xml(stix_file.origin_path)

    @classmethod
    def create_2_x(cls,observable,stix_file,node_id):
        if observable is None:
            return
        for object_key, object_value in observable['objects'].items():
            #種別ごとにチェック
            object_type = object_value['type']
            if object_type == 'file':
                if ('hashes' in object_value) == True:
                    hashes = object_value['hashes']
                    if ('MD5' in hashes) == True:
                        ObservableCaches.create_2_x_per_data(observable,object_value,stix_file,node_id,object_key,'md5',hashes['MD5'])
                    if ('SHA-1' in hashes) == True:
                        ObservableCaches.create_2_x_per_data(observable,object_value,stix_file,node_id,object_key,'sha1',hashes['SHA-1'])
                    if ('SHA-256' in hashes) == True:
                        ObservableCaches.create_2_x_per_data(observable,object_value,stix_file,node_id,object_key,'sha256',hashes['SHA-256'])
                    if ('SHA-512' in hashes) == True:
                        ObservableCaches.create_2_x_per_data(observable,object_value,stix_file,node_id,object_key,'sha512',hashes['SHA-512'])
            elif object_type == 'ipv4-addr':
                ObservableCaches.create_2_x_per_data(observable,object_value,stix_file,node_id,object_key,'ipv4',object_value['value'])
            elif object_type == 'domain-name':
                ObservableCaches.create_2_x_per_data(observable,object_value,stix_file,node_id,object_key,'domain_name',object_value['value'])
            elif object_type == 'url':
                ObservableCaches.create_2_x_per_data(observable,object_value,stix_file,node_id,object_key,'uri',object_value['value'])
            else:
                #他の properties は対象外とする
                #print '他の properties は対象外とする: ' + str(object_type)
                pass
        return

    #type_, value が決定次第格納する
    @classmethod
    def create_2_x_per_data(cls,observable,object_,stix_file,node_id,object_key,type_,value):
        document = ObservableCaches()
        #1 つの Observed-Data に複数の object が入ることがある
        #個々の object_node_id の命名規約は {node_id}_{object_key}
        object_node_id = '%s_%s' % (node_id,object_key)
        document.observable_id = node_id
        #title は node_id と object_key の連結
        document.title = object_node_id
        document.description = object_node_id
        document.stix_file = stix_file
        document.package_name = stix_file.package_name
        document.package_id = stix_file.package_id
        document.node_id = object_node_id
        document.object_ = object_
        #ipアドレスを分割して保存
        if type_ == 'ipv4':
            document.ipv4_1_3 ,document.ipv4_4  = cls.split_ipv4_value(value)
        if type_ == 'domain_name':
            #ドメイン名を分割して保存
            rs_system = System.objects.get()
            tld = TLD(rs_system.public_suffix_list_file_path)
            document.domain_without_tld,document.domain_tld = tld.split_domain(value)
            #さらに xxx.yyy.com の yyyの部分を独立して保存
            if document.domain_without_tld is not None:
                document.domain_last = document.domain_without_tld.split('.')[-1]
        document.type = type_
        document.value = value
        document.number_observed = observable['number_observed']
        document.first_observed = observable['first_observed']
        document.last_observed = observable['last_observed']
        document.save()
        return

    @classmethod
    #observable単位で追加する
    def create(cls,observable,stix_file,node_id):
        if observable is None:
            return
        document = ObservableCaches()
        document.observable_id = observable.id_
        document.title = observable.title
        if observable.description is not None:
            document.description = observable.description.value
        object_ = observable.object_
        if object_ is not None:
            document.object_ = object_.to_dict()
            properties = object_.properties 
            if properties is not None:
                if isinstance(properties,File) == True:
                    if properties.md5 is not None:
                        document.type = 'md5'
                        document.value = str(properties.md5)
                    elif properties.sha1 is not None:
                        document.type = 'sha1'
                        document.value = str(properties.sha1)
                    elif properties.sha256 is not None:
                        document.type = 'sha256'
                        document.value = str(properties.sha256)
                    elif properties.sha512 is not None:
                        document.type = 'sha512'
                        document.value = str(properties.sha512)
                    else:
                        print('File else')
                        return
                    #値が None の場合は対象外
                    if document.value is None:
                        print('Hashvalue is None')
                        return
                elif isinstance(properties,DomainName) == True:
                    document.type = 'domain_name'
                    document.value = properties.value.value
                    if document.value is None:
                        print('Domain is None')
                        return
                    #ドメイン名を分割して保存
                    rs_system = System.objects.get()
                    tld = TLD(rs_system.public_suffix_list_file_path)
                    document.domain_without_tld,document.domain_tld = tld.split_domain(properties.value.value)
                    #さらに xxx.yyy.com の yyyの部分を独立して保存
                    if document.domain_without_tld is not None:
                        document.domain_last = document.domain_without_tld.split('.')[-1]
                elif isinstance(properties,URI) == True:
                    #type が URL だけ対象
                    if properties.type_ == 'URL':
                        document.type = 'uri'
                        document.value = properties.value.value
                    #None のときはURIとみなす
                    elif properties.type_ is None:
                        document.type = 'uri'
                        document.value = properties.value.value
                    else:
                        print('URI else')
                        return
                    #値が None の場合は対象外
                    if document.value is None:
                        print('URI is None')
                        return
                    #値が list の場合は対象外
                    if isinstance(document.value,list) == True:
                        print('URI is list')
                        return
                elif isinstance(properties,Address) == True:
                    #Address Objectから取得する
                    type_,value = cls.create_address_object(properties)
                    if type_ is None:
                        print('Address else')
                        return
                    document.type = type_
                    document.value = value
                    #値が None の場合は対象外
                    if document.value is None:
                        print('Address is None')
                        return
                    #ipアドレスを分割して保存
                    if type_ == 'ipv4':
                        try:
                            document.ipv4_1_3 ,document.ipv4_4  = cls.split_ipv4_value(value)
                        except Exception:
                            #ip address のフォーマットが異なる
                            return
                elif isinstance(properties,Mutex) == True:
                    document.type = 'mutex'
                    document.value = properties.name.value
                    #値が None の場合は対象外
                    if document.value is None:
                        print('Mutex is None')
                        return
                elif isinstance(properties,NetworkConnection) == True:
                    socket = properties.destination_socket_address
                    type_,value = cls.create_from_socket_object(socket)
                    document.type = type_
                    document.value = value
                    #値が None の場合は対象外
                    if document.value is None:
                        print('IPAddress is None')
                        return
                    #ipアドレスを分割して保存
                    if type_ == 'ipv4':
                        try:
                            document.ipv4_1_3 ,document.ipv4_4  = cls.split_ipv4_value(value)
                        except Exception:
                            #ip address のフォーマットが異なる
                            return
                else:
                    #他の properties は対象外とする
                    #print '他の properties は対象外とする'
                    return
            else:
                #properties is None
                #print 'properties is None'
                return
        else:
            #object_ is None
            #print 'object_ is None'
            return
        document.stix_file = stix_file
        document.package_name = stix_file.package_name
        document.package_id = stix_file.package_id
        document.node_id = node_id
        document.save()

    @classmethod
    def split_ipv4_value(cls,ipv4):
        octets = ipv4.split('.')
        ipv4_1_3 =  ('.'.join(octets[0:3]) + '.')
        ipv4_4 = int(octets[3])
        return (ipv4_1_3,ipv4_4)

    #Socket Object から type, value を取得
    @classmethod
    def create_from_socket_object(cls,socket):
        if socket is not None:
            return cls.create_address_object(socket.ip_address)
        else:
            return (None,None)

    #Address Object から type, value を取得
    @classmethod
    def create_address_object(cls,address):
        type_ = None
        value = None
        #category が ipv4-addr だけ対象
        if address.category == 'ipv4-addr':
            type_ = 'ipv4'
            value = address.address_value.value
        elif address.category == 'e-mail':
            type_ = 'email'
            value = address.address_value.value
        else:
            print('Address else')
        return (type_,value)

    @classmethod
    def find_md5(cls,md5):
        return ObservableCaches.objects.filter(type='md5',value=md5)

    @classmethod
    def find_sha1(cls,sha1):
        return ObservableCaches.objects.filter(type='sha1',value=sha1)

    @classmethod
    def find_sha256(cls,sha256):
        return ObservableCaches.objects.filter(type='sha256',value=sha256)

    @classmethod
    def find_sha512(cls,sha512):
        return ObservableCaches.objects.filter(type='sha512',value=sha512)

    @classmethod
    def find_domain_name(cls,domain_name):
        return ObservableCaches.objects.filter(type='domain_name',value=domain_name)

    @classmethod
    def find_uri(cls,uri):
        return ObservableCaches.objects.filter(type='uri',value=uri)

    @classmethod
    def find_ipv4(cls,ipv4):
        return ObservableCaches.objects.filter(type='ipv4',value=ipv4)

class SimilarScoreCache(Document):
    IPV4_SCORE_CACHE_TYPE = 'ipv4'
    DOMAIN_SCORE_CACHE_TYPE = 'domain_type'
    SCORE_CASHE_TAYPE=(
        (IPV4_SCORE_CACHE_TYPE      ,IPV4_SCORE_CACHE_TYPE),
        (DOMAIN_SCORE_CACHE_TYPE    ,DOMAIN_SCORE_CACHE_TYPE)
    )

    meta = {
        'indexes': [
            ('type','start_cache','end_cache')
        ]
    }

    @classmethod
    #observable単位で追加する
    def create(cls,type_,start_cache,end_cache,edge_type):
        document = SimilarScoreCache()
        document.type = type_
        document.start_cache = start_cache
        document.end_cache = end_cache
        document.edge_type = edge_type
        document.save()

    type = fields.StringField(max_length=32,choices=SCORE_CASHE_TAYPE)
    start_cache = fields.ReferenceField(ObservableCaches,reverse_delete_rule=CASCADE)
    end_cache = fields.ReferenceField(ObservableCaches,reverse_delete_rule=CASCADE)
    edge_type =  fields.StringField(max_length=32)
  
'''
#起動時に StixFiles をチェックする
from ctirs.core.stix.regist import get_package_bean, get_sns_user_name_from_instance
for stix_file in StixFiles.objects.all():
    if stix_file.information_source is None:
        #InformationSourceをセットする
        stix_file.set_information_source()
    package_bean = None
    #post がなければ格納する (search 検索のため)
    if stix_file.post is None:
        if package_bean is None:
            package_bean = get_package_bean(stix_file.origin_path)
        stix_file.post = package_bean.description
        stix_file.save()
    #sns_user_name が未定義
    if len(stix_file.sns_user_name) == 0:
        if package_bean is None:
            package_bean = get_package_bean(stix_file.origin_path)
        #instance 名を小文字にして空白を取りのぞいた値が sns_user_name
        #Ex. Alienvalut OTX   -->  alienvaultotx
        stix_file.sns_user_name = get_sns_user_name_from_instance(package_bean.sns_instance)
        stix_file.save()

'''
