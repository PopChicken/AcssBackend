"""身份验证控制器"""
from django.http import HttpRequest, JsonResponse

from accs_app.service.auth import login, register

from accs_app.controller.util.validator import validate, ValidationError
from accs_app.controller.util.resp_tool import RetCode
from accs_app.service.exceptions import UserAlreadyExisted, UserDoesNotExisted, WrongPassword


__login_schema = {
    'type': 'object',
    'required': ['username', 'password'],
    'properties': {
        'username': {
            'type': 'string',
            'errmsg': "username 应为字符串"
        },
        'password': {
            'type': 'string',
            'errmsg': "password 应为字符串"
        }
    }
}


__register_schema = {
    'type': 'object',
    'required': ['username', 'password', 're_password'],
    'properties': {
        'username': {
            'type': 'string',
            'errmsg': "username 应为字符串"
        },
        'password': {
            'type': 'string',
            'errmsg': "password 应为字符串"
        },
        're_password': {
            'type': 'string',
            'errmsg': "re_password 应为字符串"
        }
    }
}


def login_api(req: HttpRequest) -> JsonResponse:
    try:
        kwargs = validate(req, schema=__login_schema)
    except ValidationError as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })
    username = kwargs['username']
    password = kwargs['password']
    try:
        token = login(username, password)
    except UserDoesNotExisted as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })
    except WrongPassword as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success',
        'data': {
            'token': token
        }
    })


def register_api(req: HttpRequest) -> JsonResponse:
    try:
        kwargs = validate(req, schema=__register_schema)
    except ValidationError as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })
    username = kwargs['username']
    password = kwargs['password']
    re_password = kwargs['re_password']
    try:
        register(username, password, re_password)
    except UserAlreadyExisted as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })
    except WrongPassword as e:
        return JsonResponse({
            'code': RetCode.FAIL.value,
            'message': str(e)
        })

    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success'
    })
