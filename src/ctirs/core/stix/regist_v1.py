import stip.common.const as const
from stix.extensions.marking.simple_marking import SimpleMarkingStructure
from stix.core.stix_package import STIXPackage
from ctirs.core.mongo.documents_stix import StixFiles
from ctirs.models import SNSConfig


S_TIP_SNS_TOOL_NAME = const.SNS_TOOL_NAME
S_TIP_SNS_TOOL_VENDOR = const.SNS_TOOL_VENDOR
S_TIP_SNS_STATEMENT_ATTACHMENT_CONTENT_PREFIX = 'S-TIP attachement content:'
S_TIP_SNS_STATEMENT_ATTACHMENT_FILENAME_PREFIX = 'S-TIP attachement filename:'
S_TIP_SNS_UNLIKE_TITLE_PREFIX = 'Unlike to '
S_TIP_SNS_LIKE_TITLE_PREFIX = 'Like to '
S_TIP_SNS_COMMENT_TITLE_PREFIX = 'Comment to '
S_TIP_SNS_STATEMENT_CRITICAL_INFRASTRUCTURE_PREFIX = 'Critical Infrastructure: '
S_TIP_SNS_STATEMENT_SCREEN_NAME_PREFIX = 'Screen Name: '
S_TIP_SNS_STATEMENT_USER_NAME_PREFIX = 'User Name: '
S_TIP_SNS_STATEMENT_AFFILIATION_PREFIX = 'Affiliation: '
S_TIP_SNS_STATEMENT_REGION_CODE_PREFIX = 'Region Code: '
S_TIP_SNS_STATEMENT_SHARING_RANGE_PREFIX = 'Sharing Range: '


def _get_stip_sns_type_from_title(title):
    if title.startswith(S_TIP_SNS_UNLIKE_TITLE_PREFIX):
        return StixFiles.STIP_SNS_TYPE_UNLIKE
    if title.startswith(S_TIP_SNS_LIKE_TITLE_PREFIX):
        return StixFiles.STIP_SNS_TYPE_LIKE
    if title.startswith(S_TIP_SNS_COMMENT_TITLE_PREFIX):
        return StixFiles.STIP_SNS_TYPE_COMMENT
    return None


def _get_stip_sns_type_from_marking(markings):
    is_contain_content = False
    is_contain_filename = False
    for marking in markings:
        try:
            marking_structure = marking.marking_structures[0]
            if not isinstance(marking_structure, SimpleMarkingStructure):
                continue
            statement = marking.marking_structures[0].statement
            if statement.startswith(S_TIP_SNS_STATEMENT_ATTACHMENT_CONTENT_PREFIX):
                is_contain_content = True
            if statement.startswith(S_TIP_SNS_STATEMENT_ATTACHMENT_FILENAME_PREFIX):
                is_contain_filename = True
        except BaseException:
            pass
    if is_contain_content and is_contain_filename:
        return StixFiles.STIP_SNS_TYPE_ATTACH
    else:
        return StixFiles.STIP_SNS_TYPE_ORIGIN


def _get_stip_sns_type_v1(doc):
    title = doc.stix_header.title
    if title is not None:
        type_from_title = _get_stip_sns_type_from_title(title)
        if type_from_title is not None:
            return type_from_title

    try:
        markings = doc.stix_header.handling
    except BaseException:
        return StixFiles.STIP_SNS_TYPE_ORIGIN
    return _get_stip_sns_type_from_marking(markings)


def _is_produced_by_stip_sns_v1(doc):
    try:
        S_TIP_SNS_IDENTITY_NAME_PREFIX = SNSConfig.get_sns_identity_name()

        information_source = doc.stix_header.information_source
        identity_name = information_source.identity.name
        if not identity_name.startswith(S_TIP_SNS_IDENTITY_NAME_PREFIX):
            return False
        tool_information = information_source.tools[0]
        if tool_information.name != S_TIP_SNS_TOOL_NAME:
            return False
        if tool_information.vendor != S_TIP_SNS_TOOL_VENDOR:
            return False
        return True
    except BaseException:
        return False


def _get_produced_time_stix_1_x(doc):
    if doc.timestamp:
        return doc.timestamp
    try:
        return doc.stix_header.information_source.time.produced_time.value
    except AttributeError:
        return None


def _set_stix_bean_from_doc_v1(package_bean, doc):
    try:
        package_bean.sns_instance = doc.stix_header.information_source.identity.name
    except BaseException:
        pass

    markings = doc.stix_header.handling
    if markings is None:
        return
    for marking in markings:
        try:
            marking_structure = marking.marking_structures[0]
            if not isinstance(marking_structure, SimpleMarkingStructure):
                continue
            statement = marking.marking_structures[0].statement
            if statement.startswith(S_TIP_SNS_STATEMENT_CRITICAL_INFRASTRUCTURE_PREFIX):
                package_bean.sns_critical_infrastructure = statement[len(S_TIP_SNS_STATEMENT_CRITICAL_INFRASTRUCTURE_PREFIX):]
            if statement.startswith(S_TIP_SNS_STATEMENT_SCREEN_NAME_PREFIX):
                package_bean.sns_screen_name = statement[len(S_TIP_SNS_STATEMENT_SCREEN_NAME_PREFIX):]
            if statement.startswith(S_TIP_SNS_STATEMENT_USER_NAME_PREFIX):
                package_bean.sns_user_name = statement[len(S_TIP_SNS_STATEMENT_USER_NAME_PREFIX):]
            if statement.startswith(S_TIP_SNS_STATEMENT_AFFILIATION_PREFIX):
                package_bean.sns_affiliation = statement[len(S_TIP_SNS_STATEMENT_AFFILIATION_PREFIX):]
            if statement.startswith(S_TIP_SNS_STATEMENT_SHARING_RANGE_PREFIX):
                package_bean.sns_sharing_range = statement[len(S_TIP_SNS_STATEMENT_SHARING_RANGE_PREFIX):]
            if statement.startswith(S_TIP_SNS_STATEMENT_REGION_CODE_PREFIX):
                package_bean.sns_region_code = statement[len(S_TIP_SNS_STATEMENT_REGION_CODE_PREFIX):]
        except BaseException:
            pass
    return


def _get_sns_user_name_from_instance(instance):
    return instance.lower().replace(' ', '')


def get_package_bean_v1(stix_file_path):
    doc = STIXPackage.from_xml(stix_file_path)
    try:
        package_bean = StixFiles.PackageBean()
        package_bean.is_post_sns = True
        package_bean.is_created_by_sns = False
        sns_type = None
        if _is_produced_by_stip_sns_v1(doc):
            package_bean.is_created_by_sns = True
            sns_type = _get_stip_sns_type_v1(doc)
            if sns_type != StixFiles.STIP_SNS_TYPE_ORIGIN:
                package_bean.is_post_sns = False
        try:
            package_bean.related_packages = []
            for related_package in doc.related_packages:
                package_bean.related_packages.append(related_package.item.id_)
        except TypeError:
            package_bean.related_packages = None
        package_bean.package_id = doc.id_
        package_bean.version = doc._version
        package_bean.produced = _get_produced_time_stix_1_x(doc)
        package_bean.package_name = doc.stix_header.title
        package_bean.sns_type = sns_type
        try:
            package_bean.description = doc.stix_header.description.value
            if package_bean.description is None:
                package_bean.description = ''
        except BaseException:
            package_bean.description = ''
        _set_stix_bean_from_doc_v1(package_bean, doc)
        if package_bean.sns_user_name == '':
            package_bean.sns_user_name = _get_sns_user_name_from_instance(package_bean.sns_instance)
        return package_bean
    except Exception:
        pass
