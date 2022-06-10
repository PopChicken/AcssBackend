"""调度模块"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from logging import debug
from threading import Lock
import threading
from time import sleep
from typing import Any, Dict, List, Tuple

from django.db.models import QuerySet

from acss_app.models import Pile, PileType
from acss_app.service.charge import create_order
from acss_app.service.timemock import get_datetime_now
from acss_app.service.exceptions import AlreadyRequested, IllegalUpdateAttemption, MappingNotExisted, OutOfRecycleResource, OutOfSpace


MAX_RECYCLE_ID = 1000

WAITING_AREA_CAPACITY = 20
WAITING_QUEUE_CAPACITY = 5

NORMAL_PILE_POWER = 30.00
FAST_CHARGE_PILE_POWER = 60.00


class _RequestIdAllocator:
    """请求ID分配器
    """

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
    begin_time: datetime = None
    is_removed = False
    pile_id: int = None
    requeue_flag = False
    fail_flag = False

    def __str__(self) -> str:
        return f'{self.request_type.name[0]}{self.request_id}'


class PileScheduler:
    """充电桩调度器
    """

    def __init__(self, pile_type: PileType) -> None:
        self.__waiting_queue: Dict[int, _ChargingRequest] = {}
        self.__executing_request: _ChargingRequest = None
        self.__pile_type = pile_type
        self.is_broken = False

    def get_type(self) -> PileType:
        return self.__pile_type

    def get_executing_request(self) -> _ChargingRequest | None:
        return self.__executing_request

    def next_request(self) -> None:
        if self.__executing_request is not None:
            self.__waiting_queue.pop(next(iter(self.__waiting_queue)))
            self.__executing_request = None
        if len(self.__waiting_queue) > 0:
            _, request = next(iter(self.__waiting_queue.items()))
            request.is_executing = True
            request.begin_time = get_datetime_now()
            self.__executing_request = request

    def push_to_queue(self, request: _ChargingRequest) -> None:
        self.__waiting_queue[request.request_id] = request
        if self.__executing_request is None:
            self.next_request()

    def get_used_size(self) -> int:
        return len(self.__waiting_queue)

    def estimate_time(self) -> int:
        total_cost = 0
        for request in self.__waiting_queue.values():
            if request.request_type == PileType.CHARGE:
                power = NORMAL_PILE_POWER
            else:
                power = FAST_CHARGE_PILE_POWER
            cost = float(request.amount) / power * 3600
            total_cost += cost
        return total_cost

    def contains(self, request_id: int) -> bool:
        return request_id in self.__waiting_queue

    def remove(self, request_id: int) -> None:
        request = self.__waiting_queue[request_id]
        if request.is_executing:
            self.next_request()
            return
        del self.__waiting_queue[request_id]

    def find_position(self, request_id) -> int:
        pos_cnt = 0
        for req_id in self.__waiting_queue:
            if req_id == request_id:
                return pos_cnt
            pos_cnt += 1

    def fetch_and_clear(self, include_executing: bool) -> List[_ChargingRequest]:
        if include_executing:
            requests = self.__waiting_queue.values()
            self.__waiting_queue = {}
            self.__executing_request = None
            return requests
        else:
            if self.__executing_request is not None:
                self.__waiting_queue.pop(next(iter(self.__waiting_queue)))
            requests = self.__waiting_queue.values()
            self.__waiting_queue = {}
            if self.__executing_request is not None:
                self.__waiting_queue[self.__executing_request.request_id] = self.__executing_request
            return requests


class StatusType(Enum):
    NOTCHARGING = 0
    WAITINGSTAGE1 = 1
    WAITINGSTAGE2 = 2
    CHARGING = 3
    CHANGEMODEREQUEUE = 4
    FAILTREQUEUE = 5


class SchedulingMode(Enum):
    NORMAL = 0
    PRIORITY = 1
    TIME_ORDERED = 2
    RECOVERY = 3


@dataclass
class RequestStatus:
    status: StatusType
    position: int
    pile_id: int | None


DEFAULT_RECOVERY_MODE = SchedulingMode.TIME_ORDERED


class Scheduler:
    """调度器类
    """

    def __init__(self) -> None:
        self.__id_allocator = _RequestIdAllocator()
        self.__lock = Lock()
        self.__check_lock = Lock()
        self.__pile_schedulers: Dict[int, PileScheduler] = {}
        self.__waiting_area_map: Dict[int, _ChargingRequest] = {}
        self.__username_to_request_id: Dict[str, int] = {}
        self.__scheduling_mode = SchedulingMode.NORMAL
        self.__broken_pile_id: int = None
        self.__recovery_queue = []
        self.__waiting_areas = {
            PileType.CHARGE: [[], 0],
            PileType.FAST_CHARGE: [[], 0]
        }

        __piles: QuerySet[Pile] = Pile.objects.all()
        for pile in __piles:
            self.__pile_schedulers[pile.pile_id] = PileScheduler(
                pile.pile_type)

        threading.Thread(target=self.__check_proc).start()

    @classmethod
    def __pop_queue(cls, queue: Tuple[List[_ChargingRequest], int]) -> _ChargingRequest | None:
        while len(queue[0]) > 0 and queue[0][0].is_removed:
            queue[0].pop(0)
            queue[1] -= 1
        if len(queue[0]) == 0:
            return
        request = queue[0].pop(0)
        queue[1] -= 1
        return request

    @classmethod
    def __push_queue(cls, queue: Tuple[List[_ChargingRequest], int],
                     request: _ChargingRequest) -> None:
        queue[0].append(request)
        queue[1] += 1

    def __find_fastest_spare_pile(self, request_type: PileType) -> int:
        fastest_pile = None
        shortest_time = float('inf')
        for pile_id, pile_scheduler in self.__pile_schedulers.items():
            if pile_scheduler.is_broken is True:
                continue
            if pile_scheduler.get_type() != request_type:
                continue
            if pile_scheduler.get_used_size() == WAITING_QUEUE_CAPACITY:
                continue
            cost = pile_scheduler.estimate_time()
            if shortest_time <= cost:
                continue
            fastest_pile = pile_id
            shortest_time = cost
        return fastest_pile

    def __try_schedule(self) -> None:
        def schedule_on_type(pile_type: PileType) -> None:
            while True:
                target_pile = self.__find_fastest_spare_pile(pile_type)
                if target_pile is None:
                    return
                waiting_area_queue = self.__waiting_areas[pile_type]
                request = Scheduler.__pop_queue(waiting_area_queue)
                if request is None:
                    return
                request.is_in_waiting_queue = True
                request.pile_id = target_pile
                self.__pile_schedulers[target_pile].push_to_queue(request)
                debug("[scheduler] request %d has been moved into queue of pile %d",
                      request.request_id, request.pile_id)

        skip_types = set()
        if self.__scheduling_mode != SchedulingMode.NORMAL:
            pile_type = self.__pile_schedulers[self.__broken_pile_id].get_type()
            skip_types.add(pile_type)  # 跳过进行故障调度的充电桩
            while len(self.__recovery_queue) > 0:
                target_pile = self.__find_fastest_spare_pile(pile_type)
                if target_pile is None:  # 队列全满
                    break
                request = self.__recovery_queue.pop(0)
                request.fail_flag = False
                request.pile_id = target_pile
                self.__pile_schedulers[target_pile].push_to_queue(request)
                debug("[recovery] request %d has been moved into queue of pile %d.",
                      request.request_id,
                      target_pile)
                if len(self.__recovery_queue) == 0:  # 故障队列调度完成
                    debug("[recovery] recovery queue is empty now. resume scheduling.")
                    self.__scheduling_mode = SchedulingMode.NORMAL
                    skip_types.clear()  # 清空 恢复正常调度

        # 对未被故障影响的充电桩进行调度
        schedule_on_type(PileType.CHARGE)
        schedule_on_type(PileType.FAST_CHARGE)

    def __find_recovery_position(self, request_id: int) -> int:
        pos_cnt = 0
        for request in self.__recovery_queue:
            if request.request_id == request_id:
                return pos_cnt
            pos_cnt += 1

    def __check_if_completed(self, request: _ChargingRequest) -> bool:
        time_now = get_datetime_now()
        if request.request_type == PileType.CHARGE:
            power = NORMAL_PILE_POWER
        else:
            power = FAST_CHARGE_PILE_POWER
        amount = request.amount
        begin_time = request.begin_time
        complete_time = begin_time + \
            timedelta(seconds=float(amount) / power * 3600)
        return time_now >= complete_time

    def __check_proc(self) -> None:
        while True:
            with self.__check_lock:
                for _scheduler in self.__pile_schedulers.values():
                    with self.__lock:
                        executing_request = _scheduler.get_executing_request()
                        if executing_request is None:
                            continue
                        is_completed = self.__check_if_completed(executing_request)
                    if is_completed:
                        debug("[scheduler] request %d completed.", executing_request.request_id)
                        self.end_request(executing_request.request_id)
            sleep(1)

    def end_request(self, request_id: int) -> None:
        with self.__lock:
            request = self.__waiting_area_map.pop(request_id)
            request.is_removed = True
            self.__id_allocator.dealloc(request_id)
            del self.__username_to_request_id[request.username]
            if not request.is_in_waiting_queue:
                self.__waiting_areas[request.request_type][1] -= 1
                return
            pile_id = request.pile_id
            pile_scheduler = self.__pile_schedulers[pile_id]
            pile_scheduler.remove(request_id)

            if request.is_executing:
                if not self.__check_if_completed(request):
                    debug("[scheduler] request %d is cancelled while executing.",
                          request.request_id)
                # 触发结算流程生成详单
                debug("[scheduler] request %d created an order.", request_id)
                create_order(request.request_type,
                             request.pile_id,
                             request.username,
                             request.amount,
                             request.create_time,
                             end_time=get_datetime_now())
            else:
                debug("[scheduler] request %d is cancelled.", request_id)

            # pile_scheduler 有空位 触发调度流程
            self.__try_schedule()

    def update_request(self, request_id: int, amount: Decimal, request_type: PileType) -> None:
        with self.__lock:
            request = self.__waiting_area_map[request_id]
            if request.is_in_waiting_queue:
                raise IllegalUpdateAttemption("不允许在充电区更新请求")

            if request.request_type == request_type:
                request.amount = amount
                return

            # 修改了模式
            self.end_request(request_id)  # 取消请求
            self.submit_request(request_type,  # 重新请求
                                request.username,
                                amount,
                                request.battery_capacity,
                                requeue=True)

    def submit_request(self, request_mode: PileType,
                       username: str,
                       amount: Decimal,
                       battery_capacity: Decimal,
                       requeue: bool = False) -> None:
        with self.__lock:
            if username in self.__username_to_request_id:
                raise AlreadyRequested("已存在用户请求")

            used_size = sum(q[1] for q in self.__waiting_areas.values())
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

            request.requeue_flag = requeue

            self.__waiting_area_map[request_id] = request
            self.__username_to_request_id[username] = request_id
            Scheduler.__push_queue(waiting_queue, request)

            debug("[scheduler] request %d from user %s is submitted", request_id, username)

            # 等待区更新 尝试调度
            self.__try_schedule()

    def get_request_status(self, request_id: int) -> RequestStatus:
        with self.__lock:
            request = self.__waiting_area_map[request_id]
            if request.is_removed:
                return RequestStatus(StatusType.NOTCHARGING, -1, None)
            if request.is_executing:
                return RequestStatus(StatusType.CHARGING, 0, request.pile_id)
            if request.fail_flag:
                pos = self.__find_recovery_position(request_id)
                return RequestStatus(StatusType.FAILTREQUEUE, pos, None)
            elif request.is_in_waiting_queue:
                pile_id = request.pile_id
                pile_scheduler = self.__pile_schedulers[pile_id]
                pos = pile_scheduler.find_position(request_id)
                return RequestStatus(StatusType.WAITINGSTAGE2, pos, pile_id)
            status = StatusType.WAITINGSTAGE1
            if request.requeue_flag is True:
                status = StatusType.CHANGEMODEREQUEUE
            request_type = request.request_type
            request_waiting_queue: List[_ChargingRequest] = self.__waiting_areas[request_type][0]
            pos_cnt = 0
            for req in request_waiting_queue:
                if req.request_id == request_id:
                    break
                if req.is_removed:
                    continue
                pos_cnt += 1

            pos_cnt += max(p.get_used_size()
                           for p in self.__pile_schedulers.values())
            return RequestStatus(status, pos_cnt, None)

    def brake(self, pile_id: int) -> None:
        with self.__check_lock:
            debug("[recovery] pile %d is down.", pile_id)

            self.__scheduling_mode = DEFAULT_RECOVERY_MODE
            self.__broken_pile_id = pile_id
            pile_scheduler = self.__pile_schedulers[pile_id]
            pile_scheduler.is_broken = True
            executing_request = pile_scheduler.get_executing_request()
            if executing_request is not None:
                self.end_request(executing_request.request_id)

            match self.__scheduling_mode:
                case SchedulingMode.PRIORITY:
                    requests = pile_scheduler.fetch_and_clear(include_executing=True)
                    for request in requests:
                        debug("[recovery] request %d has been moved to recovery queue.",
                              request.request_id)
                        request.pile_id = None
                        request.fail_flag = True
                    self.__recovery_queue = list(requests)
                case SchedulingMode.TIME_ORDERED:
                    pile_type = pile_scheduler.get_type()
                    requests: List[_ChargingRequest] = []
                    for _pile_id, _scheduler in self.__pile_schedulers.items():
                        if _scheduler.get_type() != pile_type:
                            continue
                        include_executing = False
                        if _pile_id == pile_id:
                            include_executing = True
                        _requests = _scheduler.fetch_and_clear(include_executing)
                        requests += _requests
                    for request in requests:
                        debug("[recovery] request %d has been moved to recovery queue.",
                              request.request_id)
                        request.pile_id = None
                        request.fail_flag = True
                    requests = sorted(requests)
                    self.__recovery_queue = list(requests)
            self.__try_schedule()

    def recover(self, pile_id: int) -> None:
        with self.__check_lock:
            debug("[recovery] pile %d is up.", pile_id)

            self.__scheduling_mode = SchedulingMode.RECOVERY
            pile_scheduler = self.__pile_schedulers[pile_id]
            pile_scheduler.is_broken = False

            pile_type = pile_scheduler.get_type()
            requests: List[_ChargingRequest] = []
            for _, _scheduler in self.__pile_schedulers.items():
                if _scheduler.get_type() != pile_type:
                    continue
                _requests = _scheduler.fetch_and_clear(include_executing=False)
                requests += _requests
            for request in requests:
                debug("[recovery] request %d has been moved to recovery queue.",
                        request.request_id)
                request.pile_id = None
                request.fail_flag = True
            requests = sorted(requests)
            self.__recovery_queue = list(requests)

    def get_request_id_by_username(self, username: str) -> int:
        with self.__lock:
            request_id = self.__username_to_request_id.get(username)
            if request_id is None:
                raise MappingNotExisted("用户未创建充电请求")
            return request_id


    def snapshot(self) -> List[Dict[str, Any]]:
        request_list = []
        for request in self.__waiting_area_map.values():
            request_info = {
                'pile_id': str(request.pile_id),
                'username': request.username,
                'battery_size': request.battery_capacity,
                'require_amount': request.amount,
                'waiting_time': (get_datetime_now() - request.create_time).seconds
            }
            request_list.append(request_info)
        return request_list


scheduler: Scheduler = None


# def get_request_position_by_identifier(request_id: int) -> _ChargingRequest:
#     pass


def on_init() -> None:
    """调度器模块初始化
    """
    global scheduler

    scheduler = Scheduler()
    # for i in range(18):
    #     scheduler.submit_request(PileType.CHARGE, f'user{i}', Decimal('5.00'), Decimal('65.50'))

    # scheduler.submit_request(PileType.CHARGE, 'user', Decimal('5.00'), Decimal('65.50'))

    # scheduler.update_request(15, Decimal('23.00'), Decimal('53.50'))
    # scheduler.end_request(0)
    # scheduler.update_request(15, Decimal('23.00'), Decimal('53.50'))
