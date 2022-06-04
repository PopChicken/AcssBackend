"""计费模块"""
from datetime import datetime
from decimal import Decimal


SERVICE_COST_PER_KWH = Decimal('0.80')

# 阶梯计价（时间左闭右开）
CHARGING_COST_PER_KWH_TOP = Decimal('1.00')
CHARGING_COST_PER_KWH_MEDIUM = Decimal('0.70')
CHARGING_COST_PER_KWH_BOTTOM = Decimal('0.40')


# TODO 实现计费函数
def calc_cost(begin_time: datetime,
              end_time: datetime,
              amount: Decimal) -> Decimal:
    """计算费用

    Args:
        begin_time (datetime): 开始时间（包含）
        end_time (datetime): 结束时间（包含）
        amount (Decimal): 用量（单位：度）

    Returns:
        Decimal: 费用
    """
    pass
