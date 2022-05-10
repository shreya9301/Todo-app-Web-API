import json

from fastutils.jsonutils import SimpleJsonEncoder
from fastutils.cacheutils import get_cached_value

from django.core.serializers.json import DjangoJSONEncoder as DjangoJSONEncoderBase
from django.forms.models import model_to_dict


def _get_request_data(request, extra_view_parameters):
    data = {"_request": request}
    data.update(extra_view_parameters)
    for name, _ in request.GET.items():
        value = request.GET.getlist(name)
        if isinstance(value, (list, tuple, set)) and len(value) == 1:
            data[name] = value[0]
        else:
            data[name] = value
    for name, _ in request.POST.items():
        value = request.POST.getlist(name)
        if isinstance(value, (list, tuple, set)) and len(value) == 1:
            data[name] = value[0]
        else:
            data[name] = value
    if request.body:
        try:
            payload = json.loads(request.body)
            data["_form"] = payload
            data.update(payload)
        except:
            pass
    for name, fobj in request.FILES.items():
        data[name] = fobj
    return data

def get_request_data(request, extra_view_parameters):
    return get_cached_value(request, "_django_apiview_request_data", _get_request_data, request, extra_view_parameters)
