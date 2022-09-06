import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseForbidden, HttpResponseNotAllowed, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ctirs.decorators import ajax_required
from stip.common.stix_customizer import StixCustomizer
from stip.common.matching_customizer import MatchingCustomizer


@login_required
def stix_customizer(request):
    if not request.user.is_admin:
        return HttpResponseForbidden('You have no permission.')
    return render(request, 'customizer.html', {})


@ajax_required
def get_customizer_configuration(request):
    if not request.user.is_admin:
        return HttpResponseForbidden('You have no permission.')
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    stix_customizer = StixCustomizer.get_instance()

    custom_objects = []
    if stix_customizer.conf_json is not None and 'objects' in stix_customizer.conf_json:
        for o_ in stix_customizer.conf_json['objects']:
            if ('class' in o_):
                del(o_['class'])
            if 'color' not in o_:
                o_['color'] = '#D2E5FF'
            if 'properties' in o_:
                for prop in o_['properties']:
                    if 'pattern' in prop:
                        del(prop['pattern'])
            custom_objects.append(o_)
    matching_customizer = MatchingCustomizer.get_instance()

    matching_json = []
    if matching_customizer.conf_json is not None and 'objects' in matching_customizer.conf_json:
        matching_json = matching_customizer.conf_json['matching_patterns']

    return JsonResponse({
        'custom_objects': custom_objects,
        'matching_patterns': matching_json
    })


@login_required
@csrf_exempt
def set_customizer_configuration(request):
    if not request.user.is_admin:
        return HttpResponseForbidden('You have no permission.')
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    j = json.loads(request.body)
    stix_customizer = StixCustomizer.get_instance()
    stix_customizer.update_customizer_conf({
        'objects': j['custom_objects']
    })
    matching_customizer = MatchingCustomizer.get_instance()
    matching_customizer.update_customizer_conf({
        'matching_patterns': j['matching_patterns']
    })
    return HttpResponse(status=201)
