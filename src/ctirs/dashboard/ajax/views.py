from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from ctirs.core.mongo.documents import Communities
from ctirs.core.mongo.documents_stix import StixFiles


@login_required
def get_stix_counts(request):
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
        # STIX Fileをinput_community別に集計
        count_by_community = {}
        for input_community in Communities.objects.all():
            count = StixFiles.objects.filter(input_community=input_community).count()
            if count != 0:
                count_by_community[input_community.name] = count

        labels = []
        datasets = []
        # 値を降順ソート
        list_ = sorted(list(count_by_community.items()), key=lambda x: x[1], reverse=True)
        # キーと値をそれぞれリスト格納
        for l in list_:
            k, v = l
            labels.append(k)
            datasets.append(v)

        r = {}
        r['status'] = 'OK'
        r['data'] = {}
        r['data']['pie_labels'] = labels
        r['data']['pie_datasets'] = datasets
        return JsonResponse(r, safe=False)
    except BaseException:
        import traceback
        traceback.print_exc()
        r = {'status': 'NG',
             'message': 'Server Internal Error.'}
        return JsonResponse(r, safe=False)
