"""JWT工具箱"""
import functools

from enum import Enum
from typing import Callable

from jwt import encode, decode, DecodeError
from django.http import HttpRequest, JsonResponse

from acss_app.controller.util.resp_tool import RetCode


class Role(Enum):
    USER = 0
    ADMIN = 1


class RequestContext:
    def __init__(self, username: str, role: Role) -> None:
        self.username = username
        self.role = role


def gen_token(username: str, role: str) -> str:
    payload = {
        'username': username,
        'role': role
    }
    token = encode(payload, 'top-secret', algorithm='HS256')
    return token


def preprocess_token(
    limited_role: Role
) -> Callable:
    def decorator(request_handler: Callable[[RequestContext, HttpRequest], JsonResponse]):
        @functools.wraps(request_handler)
        def wrapper(request: HttpRequest):
            token: str = request.META.get('HTTP_AUTHORIZATION')
            if token is None:
                return JsonResponse({
                    'code': RetCode.FAIL.value,
                    'message': '需要登录'
                })
            try:
                token = token.removeprefix('Bearer ')
                payload = decode(token, 'top-secret', algorithms=['HS256'])
            except DecodeError:
                return JsonResponse({
                    'code': RetCode.FAIL.value,
                    'message': 'JWT损坏'
                })
            username = payload['username']
            role = Role[payload['role']]
            if role != limited_role:
                return JsonResponse({
                    'code': RetCode.FAIL.value,
                    'message': '无权限'
                })
            context = RequestContext(username, role)
            response: JsonResponse = request_handler(context, request)
            return response
        return wrapper
    return decorator
