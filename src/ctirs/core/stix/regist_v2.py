import json
import codecs
import datetime
import pytz
import stip.common.const as const
from ctirs.core.mongo.documents_stix import StixFiles, stix2_str_to_datetime
from ctirs.models.sns.feeds.models import Feed


def _get_firstr_object(doc, object_type):
    if 'objects' not in doc:
        return None
    ret_o = None
    count = 0
    for o_ in doc['objects']:
        if 'type' not in o_:
            continue
        if o_['type'] == object_type:
            ret_o = o_
            count += 1
    if count == 1:
        return ret_o
    return None


def _is_produced_by_stip_sns_v2(doc):
    return _get_firstr_object(doc, 'x-stip-sns')


def _get_report_object(doc):
    return _get_firstr_object(doc, 'report')


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
        package_bean.package_id = doc['id']
        if ('spec_version' in doc):
            package_bean.version = doc['spec_version']
        else:
            package_bean.version = '2.1'

        stip_sns = _is_produced_by_stip_sns_v2(doc)
        package_bean.related_packages = None
        produced_str = None
        if stip_sns:
            package_bean.package_name = stip_sns['name']
            package_bean.description = stip_sns['description']
            package_bean.is_created_by_sns = True
            package_bean.sns_type = _get_stip_sns_type_v2(stip_sns)
            if package_bean.sns_type != StixFiles.STIP_SNS_TYPE_V2_POST:
                package_bean.is_post_sns = False
            package_bean.related_packages = []

            if const.STIP_STIX2_PROP_BUNDLE_ID in stip_sns:
                package_bean.related_packages.append(stip_sns[const.STIP_STIX2_PROP_BUNDLE_ID])
            elif const.STIP_STIX2_PROP_OBJECT_REF in stip_sns:
                package_bean.related_packages.append(stip_sns[const.STIP_STIX2_PROP_OBJECT_REF])

            if const.STIP_STIX2_PROP_ATTACHMENTS in stip_sns:
                attach_refs = stip_sns[const.STIP_STIX2_PROP_ATTACHMENTS]
            elif const.STIP_STIX2_PROP_ATTACHMENT_REFS in stip_sns:
                attach_refs = stip_sns[const.STIP_STIX2_PROP_ATTACHMENT_REFS]
            else:
                attach_refs = []
            for ref in attach_refs:
                package_bean.related_packages.append(ref['bundle'])
            if len(package_bean.related_packages) == 0:
                package_bean.related_packages = None
            produced_str = stip_sns['created']
        else:
            package_bean.package_name = None
            package_bean.description = None
            report = _get_report_object(doc)
            if report:
                package_bean.package_name = report['name']
                if 'description' in report:
                    package_bean.description = report['description']
                produced_str = report['created']
            if not package_bean.package_name:
                package_bean.package_name = package_bean.package_id
            if not package_bean.description:
                package_bean.description = 'Post: %s' % (package_bean.package_id)
            package_bean.is_created_by_sns = False
            package_bean.is_post_sns = True
        _set_stix_bean_from_doc_v2(package_bean, doc)
        if produced_str:
            package_bean.produced = stix2_str_to_datetime(produced_str)
        else:
            package_bean.produced = datetime.datetime.now(tz=pytz.utc)
        return package_bean
    except Exception as e:
        raise Exception('Can\'t parse STIX. ' + e.message)
