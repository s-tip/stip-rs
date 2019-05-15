# -*- coding: utf-8 -*-
import os
import json
import codecs
import traceback
import shutil
import datetime
#AIS生成 STIX解析のために予め読み込む必要がある
import stix.extensions.marking.ais  # @UnusedImport
from stix.extensions.marking.simple_marking import SimpleMarkingStructure
from stix.core.stix_package import STIXPackage
from ctirs import COMMUNITY_ORIGIN_DIR_NAME
from ctirs.core.mongo.documents_stix import StixFiles
from ctirs.core.webhook.webhook import webhook_create
import stip.common.const as const
from ctirs.models import SNSConfig
from ctirs.core.mongo.documents_stix import stix2_str_to_datetime

#S-TIP SNS 作成 STIX に含まれる ToolInformation の Name の値
S_TIP_SNS_TOOL_NAME = const.SNS_TOOL_NAME
#S-TIP SNS 作成 STIX に含まれる ToolInformation の Vendor の値
S_TIP_SNS_TOOL_VENDOR = const.SNS_TOOL_VENDOR
#S-TIP SNS の添付ファイルの STIX に付与される Statement の content の prefix
S_TIP_SNS_STATEMENT_ATTACHMENT_CONTENT_PREFIX = 'S-TIP attachement content:'
#S-TIP SNS の添付ファイルの STIX に付与される Statement の filename の prefix
S_TIP_SNS_STATEMENT_ATTACHMENT_FILENAME_PREFIX = 'S-TIP attachement filename:'
#S-TIP SNS の Unlike の STIX に付与される Title の prefix
S_TIP_SNS_UNLIKE_TITLE_PREFIX = 'Unlike to '
#S-TIP SNS の Like の STIX に付与される Title の prefix
S_TIP_SNS_LIKE_TITLE_PREFIX = 'Like to '
#S-TIP SNS の Comment の STIX に付与される Title の prefix
S_TIP_SNS_COMMENT_TITLE_PREFIX = 'Comment to '
#S-TIP SNS の添付ファイルの STIX に付与される Statement の Critical Infrastructure の prefix
S_TIP_SNS_STATEMENT_CRITICAL_INFRASTRUCTURE_PREFIX = 'Critical Infrastructure: '
#S-TIP SNS の添付ファイルの STIX に付与される Statement の Screen Name の prefix
S_TIP_SNS_STATEMENT_SCREEN_NAME_PREFIX = 'Screen Name: '
#S-TIP SNS の添付ファイルの STIX に付与される Statement の User Name の prefix
S_TIP_SNS_STATEMENT_USER_NAME_PREFIX = 'User Name: '
#S-TIP SNS の添付ファイルの STIX に付与される Statement の Affiliation の prefix
S_TIP_SNS_STATEMENT_AFFILIATION_PREFIX = 'Affiliation: '
#S-TIP SNS の添付ファイルの STIX に付与される Statement の Region Code の prefix
S_TIP_SNS_STATEMENT_REGION_CODE_PREFIX = 'Region Code: '
#S-TIP SNS の添付ファイルの STIX に付与される Statement の Sharing Range の prefix
S_TIP_SNS_STATEMENT_SHARING_RANGE_PREFIX = 'Sharing Range: '

def regist(stix_file_path,community,via,package_name=None):
    #stixの中身から STIX の情報を取得
    package_bean = get_package_bean(stix_file_path)

    #登録するパッケージ名はweb form指定があれば優先的に使用する 
    if package_name is not None:
        package_bean.package_name = package_name

    #STIXFileコレクションに保存
    try:
        #StixFileドキュメントを作成
        with open(stix_file_path,'r') as fp:
            stix_file_doc = StixFiles.create(
                package_bean,
                community,
                fp,
                via)
    except: #おもにduplicateエラー処理 #stixは削除
        os.remove(stix_file_path)
        traceback.print_exc()
        raise Exception('duplicate package_id:%s' % (package_bean.package_id))

    #Fileをコミュニティ別のディレクトリに移動
    try:
        #file名はGridFsの方のidとする
        #stixファイルを移動
        path = os.path.join(community.dir_path,COMMUNITY_ORIGIN_DIR_NAME,str(stix_file_doc.content.grid_id))
        shutil.move(stix_file_path,path)
        #path保存
        stix_file_doc.origin_path = path
        stix_file_doc.save()
    except Exception as e:
        #ドキュメント作成後のエラーはドキュメントを削除する
        #grid_fsもcascade削除される動作は確認済
        stix_file_doc.delete()
        traceback.print_exc()
        raise Exception(str(e))

    #Node分割+キャッシュ作成
    stix_file_doc.split_child_nodes()
    
    #CommunityのWebHooksの数だけPOSTする
    webhook_create(community,stix_file_doc)
    
    #push
    from ctirs.core.mongo.documents import Communities
    for cl in Communities.get_clients_from_community(community):
        cl.push(stix_file_doc)
    return

#STIX 1.1 から produced time を作成する　
def get_produced_time_stix_1_x(doc):
    #STIXPacakge の timestamp から
    if doc.timestamp is not None:
        return doc.timestamp 
    #STIXHeader -> information_source -> produced_timeから
    try:
        return  doc.stix_header.information_source.time.produced_time.value
    except AttributeError:
        return None

#S-TIP SNS で作成された STIX であるか?
def is_produced_by_stip_sns(doc):
    try:
        #S-TIP SNS 作成 STIX に含まれる Identity の Name の値 の prefix を取得する
        S_TIP_SNS_IDENTITY_NAME_PREFIX = SNSConfig.get_sns_identity_name()

        information_source = doc.stix_header.information_source
        identity_name = information_source.identity.name
        #identity が 's-tip-sns' で始まること
        if identity_name.startswith(S_TIP_SNS_IDENTITY_NAME_PREFIX) != True:
            return False
        #ToolInformation の name が 'S-TIP' であること
        tool_information = information_source.tools[0]
        if  tool_information.name != S_TIP_SNS_TOOL_NAME:
            return False
        #ToolInformation の vendor が 'Fujitsu' であること
        if  tool_information.vendor != S_TIP_SNS_TOOL_VENDOR:
            return False
        return True
    except:
        #SNS 特有フィールドがないので S-TIP SNS 作成ではない
        return False

#S-TIP SNS 作成のSTIXがオリジナル投稿か/titleで判定?
def get_stip_sns_type_from_title(title):
    if title.startswith(S_TIP_SNS_UNLIKE_TITLE_PREFIX) == True:
        return StixFiles.STIP_SNS_TYPE_UNLIKE
    if title.startswith(S_TIP_SNS_LIKE_TITLE_PREFIX) == True:
        return StixFiles.STIP_SNS_TYPE_LIKE
    if title.startswith(S_TIP_SNS_COMMENT_TITLE_PREFIX) == True:
        return StixFiles.STIP_SNS_TYPE_COMMENT
    return None

def get_stip_sns_type_from_marking(markings):
    is_contain_content = False
    is_contain_filename = False
    for marking in markings:
        try:
            marking_structure =  marking.marking_structures[0]
            if isinstance(marking_structure,SimpleMarkingStructure) == False:
                #SimpleMarkingStructure以外は判定材料としない
                continue
            statement =  marking.marking_structures[0].statement
            #S-TIP attachement content:で始まっている Statement チェック
            if statement.startswith(S_TIP_SNS_STATEMENT_ATTACHMENT_CONTENT_PREFIX) == True:
                is_contain_content = True
            #S-TIP attachement filename:で始まっている Statement チェック
            if statement.startswith(S_TIP_SNS_STATEMENT_ATTACHMENT_FILENAME_PREFIX) == True:
                is_contain_filename = True
        except:
            #statementが含まれない項目は無視する
            pass
    #filename, content 両方含む場合のみ attach 投稿
    if is_contain_content == True and is_contain_filename == True:
        return StixFiles.STIP_SNS_TYPE_ATTACH 
    else:
        return StixFiles.STIP_SNS_TYPE_ORIGIN

#S-TIP SNS 作成の STIX から pacakge_bean の値をセットする
def set_stix_bean_from_doc(package_bean,doc):
    try:
        #Information_Source から
        package_bean.sns_instance = doc.stix_header.information_source.identity.name
    except:
        pass
    
    #marking から
    markings =  doc.stix_header.handling
    if markings is None:
        return
    for marking in markings:
        try:
            marking_structure =  marking.marking_structures[0]
            if isinstance(marking_structure,SimpleMarkingStructure) == False:
                #SimpleMarkingStructure以外は判定材料としない
                continue
            statement =  marking.marking_structures[0].statement
            #Critical Infrastructure
            if statement.startswith(S_TIP_SNS_STATEMENT_CRITICAL_INFRASTRUCTURE_PREFIX) == True:
                package_bean.sns_critical_infrastructure = statement[len(S_TIP_SNS_STATEMENT_CRITICAL_INFRASTRUCTURE_PREFIX):]
            #Screen Name
            if statement.startswith(S_TIP_SNS_STATEMENT_SCREEN_NAME_PREFIX) == True:
                package_bean.sns_screen_name = statement[len(S_TIP_SNS_STATEMENT_SCREEN_NAME_PREFIX):]
            #User Name
            if statement.startswith(S_TIP_SNS_STATEMENT_USER_NAME_PREFIX) == True:
                package_bean.sns_user_name = statement[len(S_TIP_SNS_STATEMENT_USER_NAME_PREFIX):]
            #Affiliation
            if statement.startswith(S_TIP_SNS_STATEMENT_AFFILIATION_PREFIX) == True:
                package_bean.sns_affiliation = statement[len(S_TIP_SNS_STATEMENT_AFFILIATION_PREFIX):]
            #Sharing Range
            if statement.startswith(S_TIP_SNS_STATEMENT_SHARING_RANGE_PREFIX) == True:
                package_bean.sns_sharing_range = statement[len(S_TIP_SNS_STATEMENT_SHARING_RANGE_PREFIX):]
            #Region Code
            if statement.startswith(S_TIP_SNS_STATEMENT_REGION_CODE_PREFIX) == True:
                package_bean.sns_region_code = statement[len(S_TIP_SNS_STATEMENT_REGION_CODE_PREFIX):]
        except:
            #statementが含まれない項目は無視する
            pass
    return

#SNS 投稿種別を取得する
def get_stip_sns_type(doc):
    title = doc.stix_header.title
    #Title による判断
    if title is not None:
        #タイトルから種別が判別出来たらそれを返却
        type_from_title =  get_stip_sns_type_from_title(title) 
        if type_from_title is not None:
            return type_from_title

    #この段階で残りは attach or origin
    #Marking による判断
    try:
        markings =  doc.stix_header.handling
    except:
        #marking がないので 添付ファイル STIX ではない
        return StixFiles.STIP_SNS_TYPE_ORIGIN

    #marking による判定でオリジナル投稿を返却する
    return get_stip_sns_type_from_marking(markings)

#instance 名から sns_user_name を取得する
def get_sns_user_name_from_instance(instance):
    return instance.lower().replace(' ','')

#STIXファイルから取得できる情報である package_beanを取得する
def get_package_bean(stix_file_path):
    package_bean = StixFiles.PackageBean()
    #STIX 1.1 parse
    try:
        doc = STIXPackage.from_xml(stix_file_path)
        package_bean.is_post_sns = True
        package_bean.is_created_by_sns = False
        sns_type = None
        #S-TIP SNS で作成された STIX であるか?
        if is_produced_by_stip_sns(doc) == True:
            #SNS 産である
            package_bean.is_created_by_sns = True
            sns_type = get_stip_sns_type(doc)
            #origin 投稿以外は表示しない
            if sns_type != StixFiles.STIP_SNS_TYPE_ORIGIN:
                package_bean.is_post_sns = False
        #realted_packages探す
        try:
            package_bean.related_packages = []
            for related_package in  doc.related_packages:
                package_bean.related_packages.append(related_package.item.id_)
        except TypeError:
            package_bean.related_packages = None
        package_bean.package_id = doc.id_
        package_bean.version = doc._version
        package_bean.produced = get_produced_time_stix_1_x(doc)
        package_bean.package_name = doc.stix_header.title
        package_bean.sns_type = sns_type
        try:
            package_bean.description = doc.stix_header.description.value
            if package_bean.description is None:
                package_bean.description = ''
        except:
            package_bean.description = ''
        #S-TIP SNS 作成の STIX から pacakge_bean の値をセットする
        set_stix_bean_from_doc(package_bean,doc)
        #SNS 産以外は sns_user_name が設定されていないので instance 名から取得する
        if package_bean.sns_user_name == '':
            package_bean.sns_user_name = get_sns_user_name_from_instance(package_bean.sns_instance)
        return package_bean
    except Exception:
        pass

    #STIX 2.0 parse
    try:
        with codecs.open(stix_file_path,'r','utf-8') as fp:
            content = fp.read()
        doc = json.loads(content)
        package_bean.package_name = None
        #最初に見つかったtypeがreportのnameをpackage_nameとする
        #また、STIX 2.0 では package の timestampの格納場所がないのでNoneとする
        produced_str = None
        for d in doc['objects']:
            if d['type'] == 'report':
                package_bean.package_name = d['name']
                produced_str = d['created']
        package_bean.package_id = doc['id']
        if doc.has_key('spec_version') == True:
            package_bean.version = doc['spec_version']
        else:
            #STIX 2.1 には spec_version がない
            package_bean.version = '2.1'
        #Produced Time は Report の produced time
        if produced_str is not None:
            package_bean.produced = stix2_str_to_datetime(produced_str)
        else:
            package_bean.produced = datetime.datetime.now()
        package_bean.is_post_sns = True
        package_bean.is_created_by_sns = False
        package_bean.related_packages = None
        return package_bean
        
    except Exception as e:
        traceback.print_exc()
        raise Exception('Can\'t parse STIX. ' + e.message)