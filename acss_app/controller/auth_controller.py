"""身份验证控制器"""
from django.http import HttpRequest, JsonResponse

from acss_app.service.auth import login, register

from acss_app.controller.util.validator import validate, ValidationError
from acss_app.controller.util.resp_tool import RetCode
from acss_app.service.exceptions import UserAlreadyExisted, UserDoesNotExisted, WrongPassword
from acss_app.service.util.jwt_tool import Role


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
            'minLength': 6,
            'errmsg': "username 应为6位以上字符串"
        },
        'password': {
            'type': 'string',
            'minLength': 8,
            'errmsg': "password 应为8位以上字符串"
        },
        're_password': {
            'type': 'string',
            'minLength': 8,
            'errmsg': "re_password 应为8位以上字符串"
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
        token, role = login(username, password)
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

    is_admin = False
    if role == Role.ADMIN:
        is_admin = True

    return JsonResponse({
        'code': RetCode.SUCCESS.value,
        'message': 'success',
        'data': {
            'token': token,
            "is_admin": is_admin
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
