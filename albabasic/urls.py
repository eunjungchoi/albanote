"""albabasic URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from albalog import api, views

router = routers.DefaultRouter()
router.register('users', api.UserViewSet)
router.register('businesses', api.BusinessViewSet)
router.register('members', api.MemberViewSet)
router.register('works', api.WorkViewSet)
router.register('timetables', api.TimeTableViewSet)

urlpatterns = [
    path(r'api/v1/', include(router.urls)),
    path('admin/', admin.site.urls),
    path('rest-auth/', include('rest_auth.urls')),
    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path(r'', views.IndexView.as_view(), name='index'),
]
