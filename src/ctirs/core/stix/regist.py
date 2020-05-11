import os
import traceback
import shutil
from ctirs import COMMUNITY_ORIGIN_DIR_NAME
from ctirs.core.mongo.documents_stix import StixFiles
from ctirs.core.webhook.webhook import webhook_create
from ctirs.core.stix.regist_v1 import get_package_bean_v1
from ctirs.core.stix.regist_v2 import get_package_bean_v2
from ctirs.core.mongo.documents import Communities


def regist(stix_file_path, community, via, package_name=None):
    package_bean = get_package_bean(stix_file_path)

    if package_name:
        package_bean.package_name = package_name

    try:
        with open(stix_file_path, 'rb') as fp:
            stix_file_doc = StixFiles.create(
                package_bean,
                community,
                fp,
                via)
    except BaseException:
        os.remove(stix_file_path)
        traceback.print_exc()
        raise Exception('duplicate package_id:%s' % (package_bean.package_id))

    try:
        path = os.path.join(
            community.dir_path,
            COMMUNITY_ORIGIN_DIR_NAME,
            str(stix_file_doc.content.grid_id))
        shutil.move(stix_file_path, path)
        stix_file_doc.origin_path = path
        stix_file_doc.save()
    except Exception as e:
        stix_file_doc.delete()
        traceback.print_exc()
        raise Exception(str(e))

    stix_file_doc.split_child_nodes()

    webhook_create(community, stix_file_doc)

    for cl in Communities.get_clients_from_community(community):
        cl.push(stix_file_doc)
    return


def get_package_bean(stix_file_path):
    try:
        return get_package_bean_v1(stix_file_path)
    except Exception:
        return get_package_bean_v2(stix_file_path)
