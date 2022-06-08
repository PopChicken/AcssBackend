"""用户客户端控制器"""
from decimal import Decimal
from django.http import HttpRequest, JsonResponse

from accs_app.controller.util.validator import validate, ValidationError
from accs_app.controller.util.resp_tool import RetCode
from accs_app.models import PileType
from accs_app.service.auth import Role
from accs_app.service.exceptions import AlreadyRequested, IllegalUpdateAttemption, MappingNotExisted, OutOfSpace
from accs_app.service.simple_query import get_all_orders
from accs_app.service.util.jwt_tool import RequestContext, preprocess_token
from accs_app.service.schd import scheduler


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


__edit_charging_request_schema = {
    'type': 'object',
    'required': ['charge_mode', 'require_amount'],
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
    try:
        kwargs = validate(req, schema=__submit_charging_request_schema)
    except ValidationError as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    charge_mode: str = kwargs['charge_mode']
    require_amount: Decimal = Decimal(kwargs['require_amount'])
    battery_capacity: Decimal = Decimal(kwargs['battery_size'])

    if charge_mode == 'T':
        request_mode = PileType.CHARGE
    elif charge_mode == 'F':
        request_mode = PileType.FAST_CHARGE

    try:
        scheduler.submit_request(
            request_mode, context.username, require_amount, battery_capacity)
    except AlreadyRequested as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })
    except OutOfSpace as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success'
    })


@preprocess_token(limited_role=Role.USER)
def edit_charging_request(context: RequestContext, req: HttpRequest) -> JsonResponse:
    try:
        kwargs = validate(req, schema=__edit_charging_request_schema)
    except ValidationError as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    charge_mode: str = kwargs['charge_mode']
    require_amount: Decimal = Decimal(kwargs['require_amount'])

    try:
        request_id = scheduler.get_request_id_by_username(context.username)
        scheduler.update_request(request_id, require_amount, charge_mode)
    except MappingNotExisted as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })
    except IllegalUpdateAttemption as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success'
    })


@preprocess_token(limited_role=Role.USER)
def end_charging_request(context: RequestContext, req: HttpRequest) -> JsonResponse:
    try:
        validate(req, method='GET')
    except ValidationError as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    try:
        request_id = scheduler.get_request_id_by_username(context.username)
        scheduler.end_request(request_id)
    except MappingNotExisted as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success'
    })


# TODO 兼容修改请求与故障恢复
@preprocess_token(limited_role=Role.USER)
def preview_queue_api(context: RequestContext, req: HttpRequest) -> JsonResponse:
    try:
        validate(req, method='GET')
    except ValidationError as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    requested_flag = False

    try:
        request_id = scheduler.get_request_id_by_username(context.username)
        position, pile_id = scheduler.get_in_queue_position(request_id)
        if pile_id is None:
            place = 'WAITINGPLACE'
        else:
            place = pile_id
    except MappingNotExisted:
        requested_flag = True

    if not requested_flag:
        cur_state = 'NOTCHARGING'
    elif pile_id is None:
        cur_state = 'WAITINGSTAGE1'
    elif position == 0:
        cur_state = 'CHARGING'
    else:
        cur_state = 'WAITINGSTAGE2'

    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success',
        'data': {
            'charge_id': str(request_id),
            'queue_len': position,
            'cur_state': cur_state,
            'place': place
        }
    })
