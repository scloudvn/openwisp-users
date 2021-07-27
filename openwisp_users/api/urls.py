from django.conf.urls import url
from django.urls import path

from openwisp_users import settings as app_settings

from . import views


def get_api_urls(api_views=None):
    urlpatterns = []
    if api_views is None:
        api_views = views
    urlpatterns += [
        path('user/organization/', views.organization_list, name='organization_list',),
        path(
            'user/organization/<str:pk>/',
            views.organization_detail,
            name='organization_detail',
        ),
        path('user/users/', views.users_list, name='user_list',),
        path('user/users/<str:pk>/', views.users_detail, name='users_detail'),
        path(
            'user/users/<str:pk>/changepassword/',
            views.change_password,
            name='change_password',
        ),
        path('user/group/', views.group_list, name='group_list'),
        path('user/group/<str:pk>/', views.group_detail, name='group_detail'),
    ]
    if app_settings.USERS_AUTH_API:
        urlpatterns += [
            url(r'^user/token/', views.obtain_auth_token, name='user_auth_token')
        ]
    return urlpatterns


urlpatterns = get_api_urls()
