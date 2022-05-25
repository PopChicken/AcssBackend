"""accs_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.urls.conf import include

import data.admin_urls as admin_urls
import data.user_urls as user_urls
import data.pile_urls as pile_urls
import schd.urls as schd_urls


urlpatterns = [
    path('admin/', include(admin_urls)),
    path('user/', include(user_urls)),
    path('pile/', include(pile_urls)),
    path('schd/', include(schd_urls))
]
