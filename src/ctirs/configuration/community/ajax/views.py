from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_protect
from ctirs.core.common import get_text_field_value
from ctirs.core.mongo.documents import Webhooks
from ctirs.core.webhook.webhook import webhook_test

def get_configuration_community_ajax_test_webhook_webhook_id(request):
    return get_text_field_value(request,'webhook_id',default_value=None)

@csrf_protect
def test_webhook(request):
    #GET以外はエラー
    if request.method != 'GET':
        r = {'status': 'NG',
             'message' : 'Invalid HTTP method'}
        return JsonResponse(r,safe=False)
    #activeユーザー以外はエラー
    if request.user.is_active == False:
        r = {'status': 'NG',
             'message' : 'You account is inactive.'}
        return JsonResponse(r,safe=False)
    #webhook_id取得
    webhook_id = get_configuration_community_ajax_test_webhook_webhook_id(request)
    if (webhook_id is None):
        r = {'status': 'NG',
             'message' : 'Invalid parameter.'}
        return JsonResponse(r,safe=False)
    try:
        #webhook document取得
        webhook = Webhooks.objects.get(id=webhook_id)
        #webhook test実施
        webhook_test(webhook)

        r = {'status': 'OK',
             'message' : 'Success.'}
    except Exception as e:
        print('Exception:' + str(e))
        r = {'status': 'NG',
             'message' : str(e)}
    finally:
        return JsonResponse(r,safe=False)


