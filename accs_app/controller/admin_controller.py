"""管理员客户端控制器"""
from django.http import HttpRequest, JsonResponse

from accs_app.controller.util.validator import validate, ValidationError
from accs_app.controller.util.resp_tool import RetCode
from accs_app.service.auth import Role
from accs_app.service.exceptions import PileDoesNotExisted
from accs_app.service.simple_query import get_all_piles_status, update_pile_status
from accs_app.service.util.jwt_tool import RequestContext, preprocess_token
from accs_app.models import PileStatus


__update_pile_status_schema = {
    'type': 'object',
    'required': ['pile_id', 'status'],
    'properties': {
        'pile_id': {'type': 'string'},
        'status': {'type': 'string'}
    }
}


@preprocess_token(limited_role=Role.ADMIN)
def query_all_piles_stat_api(_: RequestContext, req: HttpRequest) -> JsonResponse:
    try:
        validate(req, method='GET')
    except ValidationError as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    status_list = get_all_piles_status()

    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success',
        'data': status_list
    })


@preprocess_token(limited_role=Role.ADMIN)
def update_pile_status_api(_: RequestContext, req: HttpRequest) -> JsonResponse:
    try:
        kwargs = validate(req, method='POST', schema=__update_pile_status_schema)
    except ValidationError as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    pile_id_str: str = kwargs['pile_id']
    status_str: str = kwargs['status']
    pile_id_str = pile_id_str.lstrip('P')

    pile_id = int(pile_id_str)
    status = PileStatus[status_str]

    try:
        update_pile_status(pile_id, status)
    except PileDoesNotExisted as e:
        return JsonResponse({
            'code': RetCode.SUCCESS.value,
            'message': str(e)
        })

    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success'
    })


