"""身份验证控制器"""
from django.http import HttpRequest, JsonResponse

from acss_app.service.timemock import get_timestamp_now, get_datetime_now

from acss_app.controller.util.validator import validate, ValidationError
from acss_app.controller.util.resp_tool import RetCode


def query_time(req: HttpRequest) -> JsonResponse:
    try:
        validate(req, method='GET')
    except ValidationError as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success',
        'data': {
            'datetime': get_datetime_now(),
            'timestamp': get_timestamp_now()
        }
    })
