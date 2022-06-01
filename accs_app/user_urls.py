"""用户相关接口路由"""
from django.urls import path

import accs_app.controller.user_controller as user_controller
import accs_app.controller.auth_controller as auth_controller


urlpatterns = [
    path('register', auth_controller.register_api),
    path('query_order_detail', user_controller.query_orders_api)
]