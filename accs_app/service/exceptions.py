"""exceptions"""


class ServiceError(BaseException):
    pass


class UserDoesNotExisted(ServiceError):
    pass


class UserAlreadyExisted(ServiceError):
    pass


class WrongPassword(ServiceError):
    pass
