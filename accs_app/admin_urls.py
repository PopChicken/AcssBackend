from django.urls import path

from accs_app.controller.admin_controller import query_all_piles_stat


urlpatterns = [
    path('query_all_piles_stat', query_all_piles_stat)
]
