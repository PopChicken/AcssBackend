"""用户相关接口路由"""
from django.urls import path

import accs_app.controller.user_controller as user_controller
import accs_app.controller.auth_controller as auth_controller


urlpatterns = [
    path('register', auth_controller.register_api),
    path('query_order_detail', user_controller.query_orders_api),
    path('submit_charging_request', user_controller.submit_charging_request),
    path('edit_charging_request', user_controller.edit_charging_request),
    path('end_charging_request', user_controller.end_charging_request),
    path('preview_queue', user_controller.preview_queue_api),
]
