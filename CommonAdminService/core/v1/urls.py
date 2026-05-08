from .views import *
from django.contrib import admin
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserViewSet, basename='user')
router.register(r'modules', ModuleViewSet, basename='module')
router.register(r'tenants', TenantViewSet, basename='tenant')

router.register('submodules', SubModuleViewSet, basename='submodule')
router.register('module-mappings', ModuleSubModuleMappingViewSet, basename='module-mapping')
router.register('permissions', PermissionViewSet, basename='permission')
router.register('role-permissions', RolePermissionViewSet, basename='role-permission')
router.register('user-role-permissions', UserRolePermissionViewSet, basename='user-role-permission')
router.register('tenant-modules', TenantModuleViewSet, basename='tenant-module')


urlpatterns = router.urls + [
    path('admin/', admin.site.urls),
    path('roles/<int:role_id>/permissions/', role_permissions, name='role-permissions'),

    # Authentication
    # path('accounts/', include('msbc_rbac.accounts.urls')),
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),

    path('sidebar/', get_sidebar_menu, name='sidebar-menu'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/doc/', SpectacularSwaggerView.as_view(url_name='schema')),
]
