# -*- coding: utf-8 -*
import datetime
from pytz import timezone
from xml.etree import ElementTree as ET
from mixbox import idgen
from mixbox.namespaces import Namespace
from cybox.objects.file_object import File
from cybox.objects.uri_object import URI
from cybox.objects.domain_name_object import DomainName
from cybox.objects.address_object import Address
from stix.core import STIXPackage ,STIXHeader
from stix.common import InformationSource, Identity
from stix.indicator import Indicator
from stix.data_marking import Marking, MarkingSpecification
from stix.extensions.marking.tlp import TLPMarkingStructure
from cybox.objects.email_message_object import EmailMessage

tz_utc = timezone('UTC')

class Tag(object):
    TLP_RED = 'RED'
    TLP_AMBER = 'AMBER'
    TLP_GREEN = 'GREEN'
    TLP_WHITE = 'WHITE'

    def __init__(self):
        self.id_ = -1
        self.name = ''
        self.colour = ''
        self.exportable = ''
        self.hide_tag = ''
        self.user_id = -1
        self.tlp = None

    def parse(self,tag):
        for child in tag:
            if child.tag == 'id':
                self.id_ = int(child.text)
            elif child.tag == 'name':
                self.name = child.text
                tlp_value = self.name.lower()
                if tlp_value == 'tlp:red':
                    self.tlp = self.TLP_RED
                elif tlp_value == 'tlp:amber':
                    self.tlp = self.TLP_AMBER
                elif tlp_value == 'tlp:green':
                    self.tlp = self.TLP_GREEN
                elif tlp_value == 'tlp:white':
                    self.tlp = self.TLP_WHITE
            elif child.tag == 'colour':
                self.colour = child.text
            elif child.tag == 'exportable':
                self.exportable = child.text
            elif child.tag == 'hide_tag':
                self.hide_tag = child.text
            elif child.tag == 'user_id':
                self.user_id = int(child.text)

class Attribute(object):
    def __init__(self):
        self.id_ = -1
        self.type_ = ''
        self.category = ''
        self.to_ids = ''
        self.uuid = ''
        self.event_id = ''
        self.distribution = ''
        self.timestamp = ''
        self.dt = None
        self.comment = ''
        self.sharing_group_id = ''
        self.deleted = -1
        self.disable_correlation = ''
        self.object_id = ''
        self.object_relation = ''
        self.value = ''
        self.ShadowAttribute = None

    def parse(self,attribute):
        for child in attribute:
            if child.tag == 'id':
                self.id_ = int(child.text)
            elif child.tag == 'type':
                self.type_ = child.text
            elif child.tag == 'category':
                self.category = child.text
            elif child.tag == 'to_ids':
                self.to_ids = child.text
            elif child.tag == 'uuid':
                self.uuid = child.text
            elif child.tag == 'event_id':
                self.event_id = child.text
            elif child.tag == 'distribution':
                self.distribution = child.text
            elif child.tag == 'timestamp':
                self.timestamp = child.text
                self.dt = datetime.datetime.fromtimestamp(int(self.timestamp),tz=tz_utc)
            elif child.tag == 'comment':
                self.comment = child.text
            elif child.tag == 'sharing_group_id':
                self.sharing_group_id = child.text
            elif child.tag == 'deleted':
                self.deleted = int(child.text)
            elif child.tag == 'disable_correlation':
                self.disable_correlation = child.text
            elif child.tag == 'object_id':
                self.object_id = child.text
            elif child.tag == 'object_relation':
                self.object_relation = child.text
            elif child.tag == 'value':
                self.value = child.text

    def convert(self):
        if self.deleted == 0:
            observable = self.get_observable()
            if observable is not None:
                indicator = Indicator(title=str(self.id_),timestamp=self.dt,description=self.comment)
                indicator.observable = self.get_observable()
            else:
                indicator = None
        else:
            indicator = None
        return indicator

    def get_observable(self):
        if self.type_ == 'md5':
            o_ = File()
            o_.md5 = self.value
        elif self.type_ == 'sha1':
            o_ = File()
            o_.sha1 = self.value
        elif self.type_ == 'sha256':
            o_ = File()
            o_.sha256 = self.value
        elif self.type_ == 'sha512':
            o_ = File()
            o_.sha256 = self.value
        elif self.type_ == 'url':
            o_ = URI(value=self.value,type_=URI.TYPE_URL)
        elif self.type_ == 'hostname':
            o_ = DomainName()
            o_.value = self.value
            o_.type_ = 'FQDN'
        elif self.type_ == 'domain':
            o_ = DomainName()
            o_.value = self.value
            o_.type_ = 'domain'
        elif self.type_ == 'ip-dst':
            o_ = Address(address_value=self.value,category=Address.CAT_IPV4)
            o_.is_destination = True
            o_.is_Source = False
        elif self.type_ == 'email-src':
            o_ = Address(address_value=self.value,category=Address.CAT_EMAIL)
        elif self.type_ == 'email-subject':
            o_ = EmailMessage()
            o_.subject = self.value
        else:
            #print 'skip>>>>: type_: ' + str(self.type_)
            o_ = None
        return o_

    def __str__(self):
        return 'id:' + str(self.id_) + ' / value:' + self.value.encode('utf-8')

class Org(object):
    def __init__(self):
        self.id_ = -1
        self.name = ''
        self.uuid = ''

    def parse(self,org):
        for child in org:
            if child.tag == 'id':
                self.id_ = int(child.text)
            elif child.tag == 'name':
                self.name = child.text
            elif child.tag == 'uuid':
                self.uuid = child.text
    def __str__(self):
        return 'id:' + str(self.id_) + ' / name:' + self.name

class Event(object):
    def __init__(self):
        self.id_ = -1
        self.orgc_id = -1
        self.org_id = -1
        self.date = ''
        self.threat_level_id = ''
        self.info = ''
        self.published = False
        self.uuid = ''
        self.analysis = ''
        self.timestamp = ''
        self.dt = None
        self.distribution = ''
        self.publish_timestamp = ''
        self.sharing_group_id = ''
        self.disable_correlation = ''
        self.attributes = []
        self.orgs = []
        self.orgcs = []
        self.tags = []

    def get_data_from_list_by_id(self,list_,id_):
        for item in list_:
            if item.id_ == id_:
                return item
        return None

    def get_org(self,id_):
        return self.get_data_from_list_by_id(self.orgs,id_)

    def get_orgc(self,id_):
        return self.get_data_from_list_by_id(self.orgcs,id_)

    def parse(self,event):
        for child in event:
            if child.tag == 'id':
                self.id_ = int(child.text)
            elif child.tag == 'orgc_id':
                self.orgc_id = int(child.text)
            elif child.tag == 'org_id':
                self.org_id = int(child.text)
            elif child.tag == 'date':
                self.date = child.text
            elif child.tag == 'threat_level_id':
                self.threat_level_id = child.text
            elif child.tag == 'info':
                self.info = child.text
            elif child.tag == 'published':
                self.published = (child.text == '1')
            elif child.tag == 'uuid':
                self.uuid = child.text
            elif child.tag == 'analysis':
                self.analysis = child.text
            elif child.tag == 'timestamp':
                self.timestamp = child.text
                self.dt = datetime.datetime.fromtimestamp(int(self.timestamp),tz=tz_utc)
            elif child.tag == 'distribution':
                self.distribution = child.text
            elif child.tag == 'publish_timestamp':
                self.publish_timestamp = child.text
            elif child.tag == 'sharing_group_id':
                self.sharing_group_id = child.text
            elif child.tag == 'disable_correlation':
                self.disable_correlation = child.text
            elif child.tag == 'Attribute':
                attribute = Attribute()
                attribute.parse(child)
                self.attributes.append(attribute)
            elif child.tag == 'Org':
                org = Org()
                org.parse(child)
                self.orgs.append(org)
            elif child.tag == 'Orgc':
                org = Org()
                org.parse(child)
                self.orgcs.append(org)
            elif child.tag == 'Tag':
                tag = Tag()
                tag.parse(child)
                self.tags.append(tag)

    def __str__(self):
        s = ''
        s += ('%s: %d\n' % ('Event.id',self.id_))
        s += ('%s: %s\n' % ('Event.info',self.info))
        for attribute in self.attributes:
            s += ('%s: %s\n' % ('Event.attribute',str(attribute)))
        return s
    
class MISP2STIXConverter(object):
    DEFAULT_IDENTITY_NAME = 'default_identity_name'
    DEFAULT_NS_URL = 'http://s-tip.fujitsu.com'
    DEFAULT_NS_NAME = 's-tip'

    def __init__(self,
        identity_name=DEFAULT_IDENTITY_NAME,
        ns_url=DEFAULT_NS_URL,
        ns_name=DEFAULT_NS_NAME,
        ):
        self.identity_name = identity_name
        self.events = []

        ns_ctim_sns = Namespace(ns_url,ns_name,schema_location=None)
        idgen.set_id_namespace(ns_ctim_sns)
        self.generator = idgen._get_generator()

    def parse(self,xml_file_path=None,text=None):
        self.events=[]
        if xml_file_path is not None:
            tree = ET.parse(xml_file_path)
            element = tree.getroot()
        elif text is not None:
            element = ET.fromstring(text)
        else:
            #print 'no element data.'
            return None
        
        for child in element:
            event = Event()
            event.parse(child)
            self.events.append(event)
            
    def get_misp_pacakge_id(self,misp_domain_name,event):
        return'%s:%s_%s-%s' % (self.DEFAULT_NS_NAME,'MISP_import',misp_domain_name,event.uuid)

    def convert(self,published_only=True,misp_domain_name='',**kw_arg):
        self.parse(**kw_arg)
        
        stix_packages = []
        for event in self.events:
            if published_only == True:
                if event.published == False:
                    continue
            #id generator
            package_id = self.get_misp_pacakge_id(misp_domain_name,event)
            stix_package = STIXPackage(timestamp=event.dt,id_=package_id)
            stix_header = STIXHeader()

            #set idengity information
            identity = Identity(name=self.identity_name)
            information_source = InformationSource(identity=identity)
            stix_header.information_source = information_source

            tlp = None
            for tag in event.tags:
                if tag.tlp is not None:
                    tlp = tag.tlp
                    break

            if tlp is not None:
                #TLP for Generic format
                tlp_marking_structure = TLPMarkingStructure()
                tlp_marking_structure.color = tlp
                marking_specification = MarkingSpecification()
                marking_specification.marking_structures = tlp_marking_structure
                marking_specification.controlled_structure = '../../../../descendant-or-self::node() | ../../../../descendant-or-self::node()/@*'

                marking = Marking()
                marking.add_marking(marking_specification)
                stix_header.handling = marking


            stix_header.title = event.info
            stix_header.description = event.info
            stix_header.short_description = event.info
            for attribute in event.attributes:
                stix_package.add_indicator(attribute.convert())
            stix_package.stix_header = stix_header
            stix_packages.append(stix_package)

        return stix_packages

    def __str__(self):
        s = ''
        for event in self.events:
            s += str(event)
        return s
