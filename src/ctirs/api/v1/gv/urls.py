try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.api.v1.gv.views as gv

urlpatterns = [
    # GV からのl1情報取得
    _url(r'^l1_info_for_l1table', gv.l1_info_for_l1table),
    # STIXのpackage_list取得
    _url(r'^package_list$', gv.package_list),
    # STIXのpackage_name_list取得
    _url(r'^package_name_list$', gv.package_name_list),
    # 関連しているSTIX一覧を取得
    _url(r'^matched_packages$', gv.matched_packages),
    # 関連しているSTIX一覧とコンテンツとノード情報を取得
    _url(r'^contents_and_edges$', gv.contents_and_edges),
    # sharing table (package)返却
    _url(r'^package_list_for_sharing_table$', gv.package_list_for_sharing_table),
    # STIX content取得
    _url(r'^stix_files/(?P<package_id>\S+)/stix$', gv.stix_file_stix),
    # stix コメント変更
    _url(r'^stix_files/(?P<package_id>\S+)/comment$', gv.stix_file_comment),
    # stix l1_info取得
    _url(r'^stix_files/(?P<package_id>\S+)/l1_info$', gv.stix_file_l1_info),
    # stix情報返却/削除
    _url(r'^stix_files/(?P<package_id>\S+)', gv.stix_files_id),
    # community一覧取得
    _url(r'^communities', gv.communities),
    # 種別毎の末端ノード数を取得
    _url(r'^count_by_type', gv.count_by_type),
    # 1日ごとの各コミュニティーごとのファイル数を返却する
    _url(r'^latest_stix_count_by_community', gv.latest_stix_count_by_community),
]
