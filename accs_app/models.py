"""acss后端ORM模型定义
"""
from django.db import models


class User(models.Model):
    """用户ORM模型
    """
    user_id = models.BigAutoField(primary_key=True, unique=True, blank=False)
    username = models.CharField(max_length=20, unique=True, blank=False)
    password = models.CharField(max_length=32, blank=False)
    is_admin = models.BooleanField(default=False, blank=False)


class PileStatus(models.IntegerChoices):
    """充电桩状态枚举类
    """
    RUNNING = 0  # 运行中
    SHUTDOWN = 1  # 关机
    UNAVAILABLE = 2  # 不可用


class PileType(models.IntegerChoices):
    """充电桩类型枚举类
    """
    CHARGE = 0  # 普通充电桩
    FAST_CHARGE = 1  # 快充充电桩


class Pile(models.Model):
    """充电桩ORM模型
    """
    pile_id = models.BigAutoField(primary_key=True, unique=True, blank=False)
    status = models.IntegerField(choices=PileStatus.choices)
    pile_type = models.IntegerField(choices=PileType.choices)
    register_time = models.DateField(blank=False)
    cumulative_usage_times = models.IntegerField(default=0)
    cumulative_charging_time = models.IntegerField(default=0)
    cumulative_charging_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=False)


class Order(models.Model):
    """订单ORM模型
    """
    order_id = models.BigAutoField(primary_key=True, unique=True, blank=False)
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, blank=False)
    pile = models.ForeignKey(to=Pile, on_delete=models.DO_NOTHING, blank=False)
    create_time = models.DateTimeField(blank=False)
    begin_time = models.DateTimeField(blank=False)
    end_time = models.DateTimeField(blank=False)
    charging_cost = models.DecimalField(max_digits=5, decimal_places=2, blank=False)
    service_cost = models.DecimalField(max_digits=5, decimal_places=2, blank=False)
    total_cost = models.DecimalField(max_digits=5, decimal_places=2, blank=False)
    charged_amount = models.DecimalField(max_digits=6, decimal_places=2, blank=False)
    charged_time = models.IntegerField(blank=False)
