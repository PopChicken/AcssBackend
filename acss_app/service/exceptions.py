"""exceptions"""


class ServiceError(BaseException):
    pass


class UserDoesNotExisted(ServiceError):
    pass


class UserAlreadyExisted(ServiceError):
    pass


class WrongPassword(ServiceError):
    pass


class PileDoesNotExisted(ServiceError):
    pass


class IllegalUpdateAttemption(ServiceError):
    pass


class OutOfRecycleResource(ServiceError):
    pass


class OutOfSpace(ServiceError):
    pass


class AlreadyRequested(ServiceError):
    pass


class MappingNotExisted(ServiceError):
    pass
