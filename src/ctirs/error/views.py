import traceback
import io
from ctirs.core.common import get_common_replace_dict
from django.shortcuts import render

# tracebackよりメッセージを取得し返却


def get_error_msg():
    # error情報取得
    err_io = io.StringIO()
    traceback.print_exc(None, err_io)
    err_msg = err_io.getvalue()
    err_io.close()
    return err_msg

# エラーページレンダリング


def error_page(request):
    # error情報取得
    err_msg = get_error_msg()
    return error_page_free_format(request, err_msg)

# エラーページレンダリング/許可されていないページのアクセス


def error_page_no_view_permission(request):
    return error_page_free_format(request, 'You have no permission to view this page.')

# エラーページレンダリング/activeユーザーではない


def error_page_inactive(request):
    return error_page_free_format(request, 'You account is inactive.')

# エラーページレンダリング/フリーフォーマット


def error_page_free_format(request, msg):
    replace_dict = get_common_replace_dict(request)
    # error情報取得
    replace_dict['err_msg'] = msg
    # RequestContext作成
    return render(request, 'error.html', replace_dict)
