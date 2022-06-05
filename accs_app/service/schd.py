"""调度模块"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from threading import Lock
from typing import Dict, List, Tuple

from django.db.models import QuerySet

from accs_app.models import Pile, PileType
from accs_app.service.timemock import get_datetime_now
from accs_app.service.exceptions import AlreadyRequested, IllegalUpdateAttemption, MappingNotExisted, OutOfRecycleResource, OutOfSpace


MAX_RECYCLE_ID = 1000

WAITING_AREA_CAPACITY = 20
WAITING_QUEUE_CAPACITY = 5


class _RequestIdAllocator:
    def __init__(self) -> None:
        self.__lock = Lock()
        self.__id_flags = [False for _ in range(MAX_RECYCLE_ID)]
        self.__cur = 0

    def alloc(self) -> int:
        with self.__lock:
            failure_cnt = 0
            while self.__id_flags[self.__cur]:
                if failure_cnt == MAX_RECYCLE_ID:
                    raise OutOfRecycleResource("充电标识已用尽")
                self.__cur = (self.__cur + 1) % MAX_RECYCLE_ID
                failure_cnt += 1
            self.__id_flags[self.__cur] = True
            return self.__cur

    def dealloc(self, charging_id: int) -> None:
        with self.__lock:
            self.__id_flags[charging_id] = False


@dataclass(order=True)
class _ChargingRequest:
    """充电请求
    """
    create_time: datetime
    request_id: int
    request_type: PileType
    username: str
    amount: Decimal
    battery_capacity: Decimal
    is_in_waiting_queue = False
    is_executing = False
    is_removed = False
    pile_id: int = None

    def __str__(self) -> str:
        return f'{self.request_type.name[0]}{self.request_id}'


class PileScheduler:
    """充电桩调度器
    """

    def __init__(self, pile_type: PileType) -> None:
        self.__waiting_queue: Dict[int, _ChargingRequest] = {}
        self.__executing_request: _ChargingRequest = None
        self.__pile_type = pile_type

    def get_type(self) -> PileType:
        return self.__pile_type

    def get_executing_request(self) -> _ChargingRequest | None:
        return self.__executing_request

    def next_request(self) -> None:
        if self.__executing_request is not None:
            self.__waiting_queue.popitem()
            self.__executing_request = None
        if len(self.__waiting_queue) > 0:
            _, request = next(iter(self.__waiting_queue.items()))
            request.is_executing = True
            self.__executing_request = request

    def push_to_queue(self, request: _ChargingRequest) -> None:
        self.__waiting_queue[request.request_id] = request
        if self.__executing_request is None:
            self.next_request()

    def get_used_size(self) -> int:
        return len(self.__waiting_queue)

    def contains(self, request_id: int) -> bool:
        return request_id in self.__waiting_queue

    def remove(self, request_id: int) -> None:
        request = self.__waiting_queue[request_id]
        if request.is_executing:
            self.next_request()
            return
        del self.__waiting_queue[request_id]


class Scheduler:
    """调度器类
    """

    def __init__(self) -> None:
        self.__id_allocator = _RequestIdAllocator()
        self.__pile_schedulers: Dict[int, PileScheduler] = {}
        self.__waiting_area_map: Dict[int, _ChargingRequest] = {}
        self.__username_to_request_id: Dict[str, int] = {}
        self.__waiting_areas = {
            PileType.CHARGE: [[], 0],
            PileType.FAST_CHARGE: [[], 0]
        }

        __piles: QuerySet[Pile] = Pile.objects.all()
        for pile in __piles:
            self.__pile_schedulers[pile.pile_id] = PileScheduler(
                pile.pile_type)

    @classmethod
    def __pop_queue(cls, queue: Tuple[List[_ChargingRequest], int]) -> _ChargingRequest | None:
        while len(queue[0]) > 0 and queue[0][0].is_removed:
            queue[0].pop()
            queue[1] -= 1
        if len(queue[0]) == 0:
            return
        request = queue[0].pop(0)
        queue[1] -= 1
        return request

    @classmethod
    def __push_queue(cls, queue: Tuple[List[_ChargingRequest], int], request: _ChargingRequest) -> None:
        queue[0].append(request)
        queue[1] += 1

    def __try_schedule(self) -> None:
        skip_types = set()
        for pild_id, pile_scheduler in self.__pile_schedulers.items():
            if pile_scheduler.get_type() in skip_types:
                continue
            if pile_scheduler.get_used_size() == WAITING_QUEUE_CAPACITY:
                continue
            waiting_area = self.__waiting_areas[pile_scheduler.get_type()]
            request = Scheduler.__pop_queue(waiting_area)
            if request is None:
                skip_types.add(pile_scheduler.get_type())
                continue
            request.is_in_waiting_queue = True
            request.pile_id = pild_id
            pile_scheduler.push_to_queue(request)
            return

    def end_request(self, request_id: int) -> None:
        request = self.__waiting_area_map.pop(request_id)
        if not request.is_in_waiting_queue:
            return
        pile_id = request.pile_id
        pile_scheduler = self.__pile_schedulers[pile_id]
        pile_scheduler.remove(request_id)

        if request.is_executing:
            # 触发结算流程生成详单
            pass

        request.is_removed = True
        self.__id_allocator.dealloc(request_id)
        del self.__username_to_request_id[request.username]

        # pile_scheduler 有空位 触发调度流程
        self.__try_schedule()

    def update_request(self, request_id: int, amount: Decimal, request_type: PileType) -> None:
        request = self.__waiting_area_map[request_id]
        if request.is_in_waiting_queue:
            raise IllegalUpdateAttemption("不允许在充电区更新请求")
        request.amount = amount
        request.request_type = request_type

    def submit_request(self, request_mode: PileType,
                       username: str,
                       amount: Decimal,
                       battery_capacity: Decimal) -> None:
        if username in self.__username_to_request_id:
            raise AlreadyRequested("已存在用户请求")

        used_size = sum([q[1] for q in self.__waiting_areas.values()])
        waiting_queue = self.__waiting_areas[request_mode]
        if used_size == WAITING_AREA_CAPACITY:
            raise OutOfSpace("等候区空间不足")

        request_id = self.__id_allocator.alloc()
        request = _ChargingRequest(request_id=request_id,
                                   request_type=request_mode,
                                   username=username,
                                   amount=amount,
                                   battery_capacity=battery_capacity,
                                   create_time=get_datetime_now())

        self.__waiting_area_map[request_id] = request
        self.__username_to_request_id[username] = request_id
        Scheduler.__push_queue(waiting_queue, request)
        # 等待区更新 尝试调度
        self.__try_schedule()

    def get_request_id_by_username(self, username: str) -> int:
        request_id = self.__username_to_request_id.get(username)
        if request_id is None:
            raise MappingNotExisted("用户未创建充电请求")
        return request_id


scheduler: Scheduler = None


# def get_request_position_by_identifier(request_id: int) -> _ChargingRequest:
#     pass


def on_init() -> None:
    """调度器模块初始化
    """
    global scheduler

    scheduler = Scheduler()
    # for i in range(25):
    #     scheduler.submit_request(PileType.CHARGE, f'user{i}', Decimal('25.00'), Decimal('65.50'))

    # scheduler.update_request(15, Decimal('23.00'), Decimal('53.50'))
    # scheduler.end_request(0)
    # scheduler.update_request(15, Decimal('23.00'), Decimal('53.50'))

