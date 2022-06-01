"""管理员客户端控制器"""
from django.http import HttpRequest, JsonResponse

from accs_app.controller.util.validator import validate, ValidationError
from accs_app.controller.util.resp_tool import RetCode
from accs_app.service.auth import Role
from accs_app.service.simple_query import get_all_piles_status
from accs_app.service.util.jwt_tool import RequestContext, preprocess_token


@preprocess_token(limited_role=Role.ADMIN)
def query_all_piles_stat(_: RequestContext, req: HttpRequest) -> JsonResponse:
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
