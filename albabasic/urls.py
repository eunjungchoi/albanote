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
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rest_framework.permissions import AllowAny

from albalog import api, views

schema_view = get_schema_view(
    openapi.Info(
        title='ALBANOTE_API_INFO',
        description='ALBANOTE_API_INFO_description',
        default_version='v1'
    ),
    validators=['flex', 'ssv'],
    public=True,
    permission_classes=(AllowAny,),
)

router = routers.DefaultRouter()
router.register('users', api.UserViewSet)
router.register('businesses', api.BusinessViewSet)
router.register('members', api.MemberViewSet)
router.register('attendances', api.AttendanceViewSet)
router.register('timetables', api.TimeTableViewSet)
router.register('holiday-policies', api.HolidayPolicyViewSet)

urlpatterns = [
    path(r'api/v1/', include(router.urls)),
    path('admin/', admin.site.urls),
    path('swagger<str:format>', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('docs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('rest-auth/', include('rest_auth.urls')),
    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path(r'', views.IndexView.as_view(), name='index'),
]
