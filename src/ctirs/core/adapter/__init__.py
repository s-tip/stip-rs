import tempfile
from ctirs.core.stix.regist import regist


def _regist_stix(content, community, via):
    stix_file_path = tempfile.mktemp(suffix='.xml')
    if not isinstance(content, str):
        content = content.decode('utf-8')
    with open(stix_file_path, 'w+t', encoding='utf-8') as fp:
        fp.write(content)
    regist(stix_file_path, community, via)
    return
