from stip.common import get_text_field_value
from ctirs.core.mongo.documents import TaxiiClients


def get_trim_double_quotation(s):
    return s.strip('\"')


# 同じページを返却する場合のlocationを取得する(デフォルトは/)
def get_next_location(request):
    return get_text_field_value(request, 'next', default_value='/')


# CTIM画面の共通replace辞書取得
def get_common_replace_dict(request):
    replace_dict = {}
    # ヘッダのユーザー情報
    replace_dict['user'] = request.user
    replace_dict['taxiis'] = TaxiiClients.objects

    # デモモードの場合はsave_send_urlを取得
    return replace_dict
