"""鉴权相关接口路由"""
from django.urls import path

import acss_app.controller.auth_controller as auth_controller
import acss_app.controller.generic_controller as generic_controller


urlpatterns = [
    path('login', auth_controller.login_api),
    path('time', generic_controller.query_time),
]
