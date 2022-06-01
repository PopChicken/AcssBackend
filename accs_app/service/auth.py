"""authentication service
"""
import hashlib

from django.core.exceptions import ObjectDoesNotExist

from accs_app.models import User
from accs_app.service.exceptions import UserAlreadyExisted, UserDoesNotExisted, WrongPassword
from accs_app.service.util.jwt_tool import Role, gen_token


def register(username: str, password: str, re_password: str) -> None:
    if password != re_password:
        raise WrongPassword("两次输入的密码不一致")
    registered: User = User.objects.filter(username=username).exists()
    if registered:
        raise UserAlreadyExisted("用户名已被注册")
    hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
    user = User(username=username, password=hashed_password)
    user.save()


def login(username: str, password: str) -> str:
    """登陆

    Args:
        username (str): 用户名
        password (str): 密码

    Raises:
        UserDoesNotExisted: 用户名不存在
        WrongPassword: 密码错误

    Returns:
        str: JWT令牌
    """
    try:
        user: User = User.objects.get(username=username)
    except ObjectDoesNotExist as e:
        raise UserDoesNotExisted("用户名不存在") from e
    hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
    if user.password != hashed_password:
        raise WrongPassword("密码错误")
    role = Role.USER.name
    if user.is_admin:
        role = Role.ADMIN.name
    return gen_token(username, role)
