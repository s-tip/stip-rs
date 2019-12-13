from django.utils.datastructures import MultiValueDictKeyError
from ctirs.core.mongo.documents import TaxiiClients


def get_trim_double_quotation(s):
    return s.strip('\"')


# textfieldからitem_name指定の値を取得。未定義時はdefault_value
def get_text_field_value(request, item_name, default_value=None):
    if request.method == 'GET':
        l = request.GET
    elif request.method == 'POST':
        l = request.POST
    else:
        return default_value
    try:
        v = l[item_name]
        if len(v) == 0:
            return default_value
        else:
            # テキストフィールドから取得する場合は前後の空白は取り除く
            return v.strip()
    except MultiValueDictKeyError:
        return default_value


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
