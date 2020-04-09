import json
import codecs
import datetime
import pytz
import stip.common.const as const
from ctirs.core.mongo.documents_stix import StixFiles, stix2_str_to_datetime
from ctirs.models.sns.feeds.models import Feed


def _is_produced_by_stip_sns_v2(doc):
    if 'objects' not in doc:
        return None
    stip_sns = None
    count = 0
    for o_ in doc['objects']:
        if 'type' not in o_:
            continue
        if o_['type'] == 'x-stip-sns':
            stip_sns = o_
            count += 1
    if count == 1:
        return stip_sns
    return None


def _get_stip_sns_type_v2(stip_sns):
    return stip_sns[const.STIP_STIX2_PROP_TYPE]


def _set_stix_bean_from_doc_v2(package_bean, doc):
    bean, stip_sns = Feed.get_stip_from_stix_package_v2(doc)
    package_bean.sns_instance = bean.instance
    package_bean.sns_critical_infrastructure = bean.ci
    package_bean.sns_screen_name = bean.screen_name
    package_bean.sns_user_name = bean.user_name
    package_bean.sns_affiliation = bean.affiliation
    package_bean.sns_sharing_range = bean.sharing_range
    package_bean.sns_region_code = bean.region_code
    return


def get_package_bean_v2(stix_file_path):
    try:
        with codecs.open(stix_file_path, 'r', encoding='utf-8') as fp:
            content = fp.read()
        doc = json.loads(content)
        package_bean = StixFiles.PackageBean()
        produced_str = None
        for d in doc['objects']:
            if d['type'] == 'report':
                package_bean.package_name = d['name']
                produced_str = d['created']
        package_bean.package_id = doc['id']
        if ('spec_version' in doc):
            package_bean.version = doc['spec_version']
        else:
            package_bean.version = '2.1'

        if produced_str is not None:
            package_bean.produced = stix2_str_to_datetime(produced_str)
        else:
            package_bean.produced = datetime.datetime.now(tz=pytz.utc)

        stip_sns = _is_produced_by_stip_sns_v2(doc)
        package_bean.related_packages = None
        if stip_sns:
            package_bean.package_name = stip_sns['name']
            package_bean.is_created_by_sns = True
            package_bean.sns_type = _get_stip_sns_type_v2(stip_sns)
            if package_bean.sns_type != StixFiles.STIP_SNS_TYPE_V2_POST:
                package_bean.is_post_sns = False
            if const.STIP_STIX2_PROP_OBJECT_REF in stip_sns:
                package_bean.related_packages = [stip_sns[const.STIP_STIX2_PROP_OBJECT_REF]]
        else:
            package_bean.is_created_by_sns = False
            package_bean.is_post_sns = True
        _set_stix_bean_from_doc_v2(package_bean, doc)
        return package_bean
    except Exception as e:
        raise Exception('Can\'t parse STIX. ' + e.message)
