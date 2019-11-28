
#URLを正規表現で評価し、マッチングした場合の処理箇所を定義
from django.conf.urls import url
import ctirs.api.v1.gv.views as gv

urlpatterns =[
    #GV からのl1情報取得
    url(r'^l1_info_for_l1table', gv.l1_info_for_l1table),
    #STIXのpackage_list取得
    url(r'^package_list$', gv.package_list),
    #STIXのpackage_name_list取得
    url(r'^package_name_list$', gv.package_name_list),
    #関連しているSTIX一覧を取得
    url(r'^matched_packages$', gv.matched_packages),
    #関連しているSTIX一覧とコンテンツとノード情報を取得
    url(r'^contents_and_edges$', gv.contents_and_edges),
    #sharing table (package)返却
    url(r'^package_list_for_sharing_table$', gv.package_list_for_sharing_table),
    #STIX content取得
    url(r'^stix_files/(?P<package_id>\S+)/stix$', gv.stix_file_stix),
    #stix コメント変更
    url(r'^stix_files/(?P<package_id>\S+)/comment$', gv.stix_file_comment),
    #stix l1_info取得
    url(r'^stix_files/(?P<package_id>\S+)/l1_info$', gv.stix_file_l1_info),
    #stix情報返却/削除
    url(r'^stix_files/(?P<package_id>\S+)', gv.stix_files_id),
    #community一覧取得
    url(r'^communities', gv.communities),
    #種別毎の末端ノード数を取得
    url(r'^count_by_type', gv.count_by_type),
    #1日ごとの各コミュニティーごとのファイル数を返却する
    url(r'^latest_stix_count_by_community', gv.latest_stix_count_by_community),
]
