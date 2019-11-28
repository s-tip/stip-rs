import urllib.parse
from pymisp.api import PyMISP
from pymisp.tools.stix import load_stix
from stix.core.stix_package import STIXPackage
from ctirs.core.mongo.documents import MispAdapter
from ctirs.core.mongo.documents_stix import StixFiles, System
from stix.extensions.marking.tlp import TLPMarkingStructure

class MispUploadAdapterControl(object):
    #シングルトン
    __instance = None
    
    def __new__(cls,*args,**kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance
    
    def __init__(self):
        misp_conf = MispAdapter.get()
        url = misp_conf.url
        scheme = urllib.parse.urlparse(url).scheme
        host = urllib.parse.urlparse(url).hostname
        url = '%s://%s/%s' % (scheme,host,'events')
        self.py_misp = PyMISP(url=url,key=misp_conf.apikey,ssl=False,proxies=System.get_request_proxies())
        return

    #package_id から　stix を抽出し、misp import 形式に変換し upload する
    def upload_misp(self,package_id):
        stix_file = StixFiles.objects.get(package_id=package_id)
        stix_package = STIXPackage.from_xml(stix_file.content)
        misp_event = load_stix(stix_package)
        tag = self.get_tlp_tag(stix_package)
        if tag is not None:
            misp_event.add_tag(tag)
        resp = self.py_misp.add_event(misp_event)
        if ('Event' in resp) == True:
            return resp
        else:
            raise Exception(str(resp['errors']))

    #stix_pacakge から TLP 取得して TAG の形式にして返却
    #TLP が存在しない場合は None 返却
    def get_tlp_tag(self,stix_package):
        try:
            for marking in stix_package.stix_header.handling.marking:
                marking_structure = marking.marking_structures[0]
                if isinstance(marking_structure, TLPMarkingStructure) == True:
                    tlp = marking_structure.color
                    return 'TLP:%s' % (tlp.upper())
            return None
        except:
            return None
