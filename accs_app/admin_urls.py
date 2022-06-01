from django.urls import path

from accs_app.controller.admin_controller import query_all_piles_stat_api, update_pile_status_api


urlpatterns = [
    path('query_all_piles_stat', query_all_piles_stat_api),
    path('update_pile', update_pile_status_api),
]
