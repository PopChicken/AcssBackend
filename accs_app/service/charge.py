"""计费模块"""
from datetime import datetime
from decimal import Decimal
from logging import debug

from accs_app.models import PileType
from accs_app.models import Order
from accs_app.models import User
from accs_app.service.timemock import get_datetime_now

# 计费区间:
# |  index   |   0    |   1    |    2    |    3    |    4    |    5    |   6    |
# |   type   | BOTTOM | MEDIUM |   TOP   | MEDIUM  |   TOP   | MEDIUM  | BOTTOM |
# | interval | 0 ~ 7  | 7 ~ 10 | 10 ~ 15 | 15 ~ 18 | 18 ~ 21 | 21 ~ 23 | 23 ~ 0 |
# |  length  |  420   |  180   |   300   |   180   |   180   |   120   |   60   |

BOTTOM = 0
MEDIUM = 1
TOP = 2
BILLING_INTERVALS_END = [7, 10, 15, 18, 21, 23, 0]    # （单位：小时）
WHICH_INTERVAL = [
    0, 0, 0, 0, 0, 0, 0,
    1, 1, 1,
    2, 2, 2, 2, 2,
    3, 3, 3,
    4, 4, 4,
    5, 5,
    6
]
WHICH_TYPE = [0, 1, 2, 1, 2, 1, 0]

# 服务费单价（元/度）
SERVICE_COST_PER_KWH = Decimal('0.80')

# 阶梯计价（时间左闭右开）
# 峰时: 10:00~15:00 & 18:00~21:00
CHARGING_COST_PER_KWH_TOP = Decimal('1.00')
# 平时: 7:00~10:00 & 15:00~18:00 & 21:00~23:00
CHARGING_COST_PER_KWH_MEDIUM = Decimal('0.70')
# 谷时: 23:00~次日7:00
CHARGING_COST_PER_KWH_BOTTOM = Decimal('0.40')


def calc_cost(begin_time: datetime,
              end_time: datetime,
              amount: Decimal):
    """计算费用

    Args:
        begin_time (datetime): 开始时间（包含）
        end_time (datetime): 结束时间（包含）
        amount (Decimal): 用量（单位：度）

    Returns:
        Decimal: 总费用
        Decimal: 充电费
        Decimal: 服务费
    """
    intervals_time_cnt = [0, 0, 0]           # 三种区间的计时列表（单位：秒）
    intervals_charging_cost = [0, 0, 0]       # 三种区间的充电量列表（单位：度）
    current_time = begin_time
    current_interval = WHICH_INTERVAL[begin_time.hour]          # 开始时间所属区间
    end_interval = WHICH_INTERVAL[end_time.hour]                # 结束时间所属区间
    print(datetime.now(), '开始时间所属区间', current_interval, sep='\t')
    print(datetime.now(), '结束时间所属区间', end_interval, sep='\t')
    # 当起始和结束不在同一天的同一区间时
    while not ((end_time - current_time).days == 0 and end_interval == current_interval):
        print(datetime.now(), '当前时间所属区间', current_interval, sep='\t')
        print(datetime.now(), 'current_time', current_time, sep='\t')

        current_interval_type = WHICH_TYPE[current_interval]    # 获取当前区间的类型

        print(datetime.now(), '当前时间所属区间类型', current_interval_type, sep='\t')

        next_interval_time = datetime(current_time.year,
                                      current_time.month,
                                      current_time.day,
                                      BILLING_INTERVALS_END[current_interval], 0, 0)
        current_interval = current_interval + 1  # 进入下一区间
        if current_interval % 7 == 0:
            current_interval = 0
            if (end_time - current_time).days > 0 or end_time.day > current_time.day:
                next_interval_time = datetime(current_time.year,
                                              current_time.month,
                                              current_time.day + 1,
                                              next_interval_time.hour, 0, 0)  # 进入下一天
        intervals_time_cnt[current_interval_type] += (
            next_interval_time - current_time).seconds  # 累计时间差
        current_time = next_interval_time

    print(datetime.now(), 'current_time', current_time, sep='\t')
    print(datetime.now(), 'end_time', end_time, sep='\t')
    # 累计同一天同一区间内当前时刻到结束的时间
    current_interval_type = WHICH_TYPE[current_interval]
    intervals_time_cnt[current_interval_type] += (
        end_time - current_time).seconds
    print(datetime.now(), 'intervals_time_cnt', intervals_time_cnt, sep='\t')
    # 按照与时间的正比例关系计算各个区间的充电度数
    # 充电费 = 单位电价 * 充电度数
    intervals_time_sum = sum(intervals_time_cnt)
    print(datetime.now(), 'intervals_time_sum', intervals_time_sum, sep='\t')
    intervals_charging_cost[TOP] = amount * CHARGING_COST_PER_KWH_TOP * \
        intervals_time_cnt[TOP] / intervals_time_sum
    intervals_charging_cost[MEDIUM] = amount * CHARGING_COST_PER_KWH_MEDIUM * \
        intervals_time_cnt[MEDIUM] / intervals_time_sum
    intervals_charging_cost[BOTTOM] = amount * CHARGING_COST_PER_KWH_BOTTOM * \
        intervals_time_cnt[BOTTOM] / intervals_time_sum
    print(datetime.now(), 'intervals_charging_cost',
          intervals_charging_cost, sep='\t')
    charging_cost = sum(intervals_charging_cost)
    # 服务费 = 服务费单价 * 充电度数
    service_cost = SERVICE_COST_PER_KWH * amount
    # 总费用 = 充电费 + 服务费
    print(datetime.now(), 'charging_cost', charging_cost, sep='\t')
    print(datetime.now(), 'service_cost', service_cost, sep='\t')
    charging_cost = Decimal(charging_cost).quantize(Decimal(0.00))
    service_cost = Decimal(service_cost).quantize(Decimal(0.00))
    return charging_cost + service_cost, charging_cost, service_cost


def create_order(request_type: PileType,
                 pile_id: int,
                 username: str,
                 amount: Decimal,
                 begin_time: datetime,
                 end_time: datetime) -> None:
    """生成详单

    使用 Django ORM 生成一条详单记录，详单的 create_time 字段
    使用 timemock 模块的 get_datetime_now 获取。

    Args:
        request_type (PileType): 充电模式
        pild_id (int): 充电桩编号
        username (str): 用户名
        amount (Decimal): 用量
        battery_capacity (Decimal): 电池容量
        begin_time (datetime): 开始时间
        end_time (datetime): 结束时间
    """
    costs = calc_cost(begin_time=begin_time, end_time=end_time, amount=amount)
    order = Order()
    # order.request_type = request_type
    order.pile_id = pile_id
    order.begin_time = begin_time
    order.end_time = end_time
    order.create_time = get_datetime_now()
    order.total_cost = costs[0]
    order.charging_cost = costs[1]
    order.service_cost = costs[2]
    order.charged_amount = amount
    order.charged_time = (end_time-begin_time).seconds
    # 需要注意详单内有外键 pile 和 user，这里传入的是username，需要设置为user_id
    # 查找 User
    user: User = User.objects.get(username=username)
    order.user_id = user.user_id
    # 保存数据至数据库
    order.save()
    debug("order created.")  # debug


if __name__ == '__main__':
    # calc_cost-Tests
    # Test-01
    begin = datetime(2022, 6, 6, 7, 0, 0)
    end = datetime(2022, 6, 6, 10, 0, 0)
    amount = 10
    print(datetime.now(), 'Expected Answer of Test-01', '15.00', sep='\t')
    if calc_cost(begin, end, amount) == Decimal(15.00):
        print(datetime.now(), 'Pass Test-01 ✔', sep='\t')
    else:
        print(datetime.now(), 'Pass Test-01 ✘', sep='\t')
    print()

    # Test-02
    begin = datetime(2022, 6, 6, 21, 0, 0)
    end = datetime(2022, 6, 7, 0, 0)
    amount = 30
    print(datetime.now(), 'Expected Answer of Test-02', '42.00', sep='\t')
    if calc_cost(begin, end, amount) == Decimal(42.00).quantize(Decimal('0.00')):
        print(datetime.now(), 'Pass Test-02 ✔', sep='\t')
    else:
        print(datetime.now(), 'Pass Test-02 ✘', sep='\t')
    print()

    # Test-03
    begin = datetime(2022, 6, 6, 21, 0, 0)
    end = datetime(2022, 6, 7, 21, 0, 0)
    amount = 30
    print(datetime.now(), 'Expected Answer of Test-03', '42.00', sep='\t')
    if calc_cost(begin, end, amount) == Decimal(45.00).quantize(Decimal('0.00')):
        print(datetime.now(), 'Pass Test-03 ✔', sep='\t')
    else:
        print(datetime.now(), 'Pass Test-03 ✘', sep='\t')
    print()

    # Test-04
    begin = datetime(2022, 6, 6, 21, 0, 0)
    end = datetime(2022, 6, 8, 0, 0, 0)
    amount = 30
    print(datetime.now(), 'Expected Answer of Test-04', '44.67', sep='\t')
    if calc_cost(begin, end, amount) == Decimal(44.67).quantize(Decimal('0.00')):
        print(datetime.now(), 'Pass Test-04 ✔', sep='\t')
    else:
        print(datetime.now(), 'Pass Test-04 ✘', sep='\t')
    print()

    # create_order-Tests
    begin = datetime(2022, 6, 6, 21, 0, 0)
    end = datetime(2022, 6, 7, 21, 0, 0)
    amount = Decimal(30)
    create_order(PileType.FAST_CHARGE, 5, 'user',
                 amount, begin, end)
