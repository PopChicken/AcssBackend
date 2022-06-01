from django.urls import path

import accs_app.controller.auth_controller as auth_controller


urlpatterns = [
    path('login', auth_controller.login),
    path('register', auth_controller.register),
]
