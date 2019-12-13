from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def change_api_key(request):
    # GET以外はエラー
    if request.method != 'GET':
        r = {'status': 'NG',
             'message': 'Invalid HTTP method'}
        return JsonResponse(r, safe=False)
    # activeユーザー以外はエラー
    if not request.user.is_active:
        r = {'status': 'NG',
             'message': 'You account is inactive.'}
        return JsonResponse(r, safe=False)

    try:
        user = request.user
        # apikey変更
        user.change_api_key()
        r = {'status': 'OK',
             'api_key': user.api_key}
    except Exception as e:
        import traceback
        traceback.print_exc()
        r = {'status': 'NG',
             'message': str(e)}
    finally:
        return JsonResponse(r, safe=False)
