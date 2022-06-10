"""时间mock模块"""
import time

from datetime import datetime


FAST_FORWARD_RATE = 60

__boot_datetime = datetime.now()
__boot_timestamp = round(time.time())


def reset_time() -> None:
    global __boot_datetime
    global __boot_timestamp
    __boot_datetime = datetime.now()
    __boot_timestamp = round(time.time())


def get_timestamp_now() -> int:
    real_timestamp = round(time.time())
    delta = real_timestamp - __boot_timestamp
    mocked_timestamp = __boot_timestamp + delta * FAST_FORWARD_RATE
    return mocked_timestamp


def get_datetime_now() -> datetime:
    real_datetime = datetime.now()
    delta = real_datetime - __boot_datetime
    mocked_datetime = __boot_datetime + delta * FAST_FORWARD_RATE
    return mocked_datetime
