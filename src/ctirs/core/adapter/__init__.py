# -*- coding: utf-8 -*-
import tempfile
from ctirs.core.stix.regist import regist

#stixファイルの登録
def _regist_stix(content,community,via):
    #stixファイルを一時ファイルに出力
    stix_file_path = tempfile.mktemp(suffix='.xml')
    with open(stix_file_path,'wb+') as fp:
        #cb.contentがstixの中身(contentの型はstr)
        fp.write(content)
    #登録
    regist(stix_file_path,community,via)
    return