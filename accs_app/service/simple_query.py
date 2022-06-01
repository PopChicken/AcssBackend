"""简单查询服务"""
from typing import Any, Dict, List

from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist

from accs_app.models import Order, Pile, PileStatus
from accs_app.service.exceptions import PileDoesNotExisted


def get_all_orders(username: str) -> List[Dict[str, Any]]:
    order_list = []
    orders: QuerySet[Order] = Order.objects.filter(user__username=username)
    for order in orders:
        order_info = {
            'order_id': str(order.order_id),
            'create_time': str(order.create_time),
            'charged_amount': order.charged_amount,
            'charged_time': order.charged_time,
            'begin_time': str(order.begin_time),
            'end_time': str(order.end_time),
            'charging_cost': order.charging_cost,
            'service_cost': order.service_cost,
            'total_cost': order.total_cost,
            'pile_id': str(order.pile__pile_id)
        }
        order_list.append(order_info)
    return order_list


def get_all_piles_status() -> List[Dict[str, Any]]:
    status_list = []
    piles: QuerySet[Pile] = Pile.objects.all()
    for pile in piles:
        pile_status = {
            'pile_id': str(pile.pile_id),
            'status': PileStatus[pile.status],
            'cumulative_usage_times': pile.cumulative_usage_times,
            'cumulative_charging_time': pile.cumulative_charging_time,
            'cumulative_charging_amount': pile.cumulative_charging_amount
        }
        status_list.append(pile_status)
    return status_list


def update_pile_status(pile_id: int, status: PileStatus) -> None:
    try:
        pile: Pile = Pile.objects.get(pile_id=pile_id)
    except ObjectDoesNotExist as e:
        raise PileDoesNotExisted("充电桩不存在") from e

    pile.status = status
    pile.save()
