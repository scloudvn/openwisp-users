from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import pagination
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.settings import api_settings
from swapper import load_model

from openwisp_users.api.authentication import BearerAuthentication

from .serializers import (
    OrganizationSerializer,
    SuperUserDetailSerializer,
    SuperUserListSerializer,
)
from .swagger import ObtainTokenRequest, ObtainTokenResponse
from .throttling import AuthRateThrottle

Organization = load_model('openwisp_users', 'Organization')
User = get_user_model()
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')


class ListViewPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ObtainAuthTokenView(ObtainAuthToken):
    throttle_classes = [AuthRateThrottle]
    authentication_classes = []
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    metadata_class = api_settings.DEFAULT_METADATA_CLASS
    versioning_class = api_settings.DEFAULT_VERSIONING_CLASS

    @swagger_auto_schema(
        request_body=ObtainTokenRequest, responses={200: ObtainTokenResponse}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ProtectedAPIMixin(object):
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = [
        IsAuthenticated,
        DjangoModelPermissions,
    ]


class BaseOrganizationView(ProtectedAPIMixin):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.order_by('-created')

        return Organization.objects.filter(pk__in=user.organizations_managed).order_by(
            '-created'
        )


class OrganizationListCreateView(BaseOrganizationView, ListCreateAPIView):
    pagination_class = ListViewPagination


class OrganizationDetailView(BaseOrganizationView, RetrieveUpdateDestroyAPIView):
    pass


class BaseUserView(ProtectedAPIMixin):
    serializer_class = SuperUserListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.order_by('-date_joined')

        if not user.is_superuser:
            org_users = OrganizationUser.objects.filter(user=user).select_related(
                'organization'
            )
            qs = User.objects.none()
            for org_user in org_users:
                if org_user.is_admin:
                    qs = qs | org_user.organization.users.all().distinct()
            qs = qs.filter(is_superuser=False)
            return qs.order_by('-date_joined')


class UsersListCreateView(BaseUserView, ListCreateAPIView):
    pagination_class = ListViewPagination


class UserDetailView(BaseUserView, RetrieveUpdateDestroyAPIView):
    serializer_class = SuperUserDetailSerializer


obtain_auth_token = ObtainAuthTokenView.as_view()
organization_list = OrganizationListCreateView.as_view()
organization_detail = OrganizationDetailView.as_view()
users_list = UsersListCreateView.as_view()
users_detail = UserDetailView.as_view()
