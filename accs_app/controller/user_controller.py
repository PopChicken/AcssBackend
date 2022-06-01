"""用户客户端控制器"""
from django.http import HttpRequest, JsonResponse

from accs_app.controller.util.validator import validate, ValidationError
from accs_app.controller.util.resp_tool import RetCode
from accs_app.service.auth import Role
from accs_app.service.simple_query import get_all_orders
from accs_app.service.util.jwt_tool import RequestContext, preprocess_token


__submit_charging_request_schema = {
    'type': 'object',
    'required': ['charge_mode', 'require_amount', 'battery_size'],
    'properties': {
        'charge_mode': {
            'type': 'string',
            'enum': ['T', 'F'],
            'errmsg': "charge_mode 应为可选值为'T'或'F'的字符串"
        },
        'require_amount': {
            'type': 'string',
            'pattern': r'\d+\.\d{2}',
            'errmsg': "require_amount 应为字符串表示的保留两位小数的实数"
        },
        'battery_size': {
            'type': 'string',
            'pattern': r'\d+\.\d{2}',
            'errmsg': "battery_size 应为字符串表示的保留两位小数的实数"
        }
    }
}


@preprocess_token(limited_role=Role.USER)
def query_orders_api(context: RequestContext, req: HttpRequest) -> JsonResponse:
    try:
        validate(req, method='GET')
    except ValidationError as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    username = context.username
    orders = get_all_orders(username)
    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success',
        'data': orders
    })


@preprocess_token(limited_role=Role.USER)
def submit_charging_request(context: RequestContext, req: HttpRequest) -> JsonResponse:
    pass
