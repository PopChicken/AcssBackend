"""请求检查工具箱"""
import json

from json import JSONDecodeError
from typing import Dict

from django.http import HttpRequest
from jsonschema import validate as _validate, ValidationError as _ValidationError


class ValidationError(BaseException):
    pass


def validate(request: HttpRequest, method: str = 'POST', schema: Dict = None) -> Dict | None:
    if request.method != method:
        raise ValidationError(f"请使用{method}请求")
    if method == 'GET':
        return

    try:
        req = json.loads(request.body)
        _validate(req, schema)
    except JSONDecodeError as e:
        raise ValidationError("请求解析错误") from e
    except _ValidationError as e:
        raise ValidationError("请求格式非法") from e

    return req
    