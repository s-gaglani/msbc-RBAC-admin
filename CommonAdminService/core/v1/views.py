from msbc_rbac.core.models import TenantModule, Permission, TenantApiOverride, Role
from msbc_rbac.core.serializers import serialize_tenant_modules
from msbc_rbac.core.services.sidebar_context import build_sidebar_context
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from .base import RBACViewSet
from drf_spectacular.utils import extend_schema,OpenApiResponse
from .serializer import *
from rest_framework.response import Response
from rest_framework import status
from.permission import IsTenantAdmin
from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

def sidebar_context(request):
    """
    Context processor to inject sidebar modules into templates.
    """
    if not request.user.is_authenticated:
        return {}

    return {
        "sidebar_modules": build_sidebar_context(request.user)
    }

@extend_schema(tags=['User'])
class UserViewSet(RBACViewSet):
    """
    RBAC-protected User management - Tenant-specific.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    tenant_field = 'tenant'
    lookup_value_regex = '[^/]+'
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        if serializer.validated_data.get('tenant') is None:
            serializer.save(tenant=self.request.user.tenant)
        else:
            serializer.save()

@extend_schema(tags=['RoleView'])
class RoleViewSet(RBACViewSet):
    """
    RBAC-protected Role management - Tenant-specific.
    """
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    tenant_field = 'tenant'
    lookup_value_regex = '[^/]+'
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Role.objects.all()
        return Role.objects.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)

@extend_schema(tags=['Module'])
class ModuleViewSet(RBACViewSet):
    """
    Module view - Global, not tenant-scoped.
    """
    serializer_class = ModuleSerializer
    queryset = Module.objects.all()
    lookup_value_regex = '[^/]+'
    
    def get_queryset(self):
        return Module.objects.all()
    
@api_view(['GET'])
@permission_classes([AllowAny])
def role_permissions(request, role_id):
    """Return flat list of permission codes for a given role_id - Tenant-specific"""
    tenant = request.user.tenant if request.user.is_authenticated else None
    
    try:
        if request.user.is_superuser:
            role = Role.objects.get(id=role_id, is_deleted=False)
        else:
            role = Role.objects.get(id=role_id, is_deleted=False, tenant=tenant)
    except Role.DoesNotExist:
        return Response({'error': 'Role not found'}, status=404)
    
    perms = (
        Permission.objects
        .filter(roles__role=role, roles__allowed=True, is_active=True, tenant=tenant)
        .values_list('code', flat=True)
        .distinct()
    )
    return Response({'role_id': role_id, 'permissions': list(perms)})

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser

@extend_schema(tags=['Tenant'])
class TenantViewSet(viewsets.ModelViewSet):
    """Tenant - Only superuser can create/manage tenants"""
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsSuperUser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TenantCreateSerializer
        return TenantSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        tenant_serializer = TenantSerializer(result['tenant'])
        return Response({
            'tenant': tenant_serializer.data,
            'admin_user': {
                'id': result['user'].id,
                'username': result['user'].username,
                'email': result['user'].email
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['SubModule'])
class SubModuleViewSet(RBACViewSet):
    queryset = SubModule.objects.all()
    serializer_class = SubModuleSerializer
    permission_classes = [IsTenantAdmin]
    lookup_value_regex = '[^/]+'
    
    def get_queryset(self):
        # SubModules are global, not tenant scoped - all tenants see same data
        return SubModule.objects.all()

@extend_schema(tags=['ModuleSubModuleMapping'])
class ModuleSubModuleMappingViewSet(RBACViewSet):
    queryset = ModuleSubModuleMapping.objects.select_related('module', 'submodule').all()
    serializer_class = ModuleSubModuleMappingSerializer
    permission_classes = [IsTenantAdmin]
    lookup_value_regex = '[^/]+'
    
    def get_queryset(self):
        # Module mappings are global, not tenant scoped - all tenants see same data
        return ModuleSubModuleMapping.objects.select_related('module', 'submodule').all()

@extend_schema(tags=['Permission'])
class PermissionViewSet(RBACViewSet):
    """Permission - Tenant-specific, only tenant admin can manage"""
    queryset = Permission.objects.select_related('tenant', 'module', 'submodule').all()
    serializer_class = PermissionSerializer
    permission_classes = [IsTenantAdmin]
    tenant_field = 'tenant'
    lookup_value_regex = '[^/]+'
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Permission.objects.select_related('tenant', 'module', 'submodule').all()
        return Permission.objects.filter(tenant=self.request.user.tenant).select_related('tenant', 'module', 'submodule')
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)

@extend_schema(tags=['RolePermission'])
class RolePermissionViewSet(RBACViewSet):
    """RolePermission - Tenant-specific, only tenant admin can manage"""
    queryset = RolePermission.objects.select_related('role', 'permission', 'tenant').all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsTenantAdmin]
    tenant_field = 'tenant'
    lookup_value_regex = '[^/]+'
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return RolePermission.objects.select_related('role', 'permission', 'tenant').all()
        return RolePermission.objects.filter(tenant=self.request.user.tenant).select_related('role', 'permission', 'tenant')
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)

@extend_schema(tags=['UserRolePermission'])
class UserRolePermissionViewSet(viewsets.ViewSet):
    """
    Assign user -> role-permissions.
    Tenant admin assigns specific role-permissions to a user.
    """
    permission_classes = [IsTenantAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRolePermissionAssignSerializer
        return UserRoleSerializer
    
    def list(self, request):
        tenant = request.user.tenant
        user_roles = UserRole.objects.filter(tenant=tenant).select_related('user', 'role')
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = UserRolePermissionAssignSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        permissions_data = [{
            'id': rp.id,
            'permission_code': rp.permission.code,
            'allowed': rp.allowed
        } for rp in result['role_permissions']]
        
        return Response({
            'message': 'User role-permissions assigned successfully',
            'user_id': result['user_role'].user.id,
            'username': result['user_role'].user.username,
            'role_id': result['user_role'].role.id,
            'role_name': result['user_role'].role.name,
            'permissions': permissions_data,
            'permissions_count': result['permissions_count']
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        tenant = request.user.tenant
        try:
            user_role = UserRole.objects.get(pk=pk, tenant=tenant)
        except UserRole.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        
        role_permissions = RolePermission.objects.filter(
            role=user_role.role,
            tenant=tenant
        ).select_related('permission__module', 'permission__submodule')
        
        permissions_data = [{
            'role_permission_id': rp.id,
            'permission_id': rp.permission.id,
            'permission_code': rp.permission.code,
            'permission_description': rp.permission.description,
            'module_name': rp.permission.module.name if rp.permission.module else None,
            'submodule_name': rp.permission.submodule.name if rp.permission.submodule else None,
            'allowed': rp.allowed
        } for rp in role_permissions]
        
        return Response({
            'user_id': user_role.user.id,
            'username': user_role.user.username,
            'role_id': user_role.role.id,
            'role_name': user_role.role.name,
            'permissions': permissions_data
        })
    
    def destroy(self, request, pk=None):
        tenant = request.user.tenant
        try:
            user_role = UserRole.objects.get(pk=pk, tenant=tenant)
            user_role.delete()
            return Response({'message': 'User role assignment deleted'}, status=status.HTTP_204_NO_CONTENT)
        except UserRole.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        
@extend_schema(
    tags=['Sidebar'],
    summary='Get Sidebar Menu',
)
@api_view(['GET'])
@permission_classes([IsAuthenticated,IsTenantAdmin])
def get_sidebar_menu(request):
    """
    Returns sidebar menu structure for the authenticated user.
    
    - Superusers see all modules
    - Tenant users see only enabled modules with their permissions
    """
    sidebar_data = build_sidebar_context(request.user)
    return Response({
        'user': request.user.username,
        'tenant': request.user.tenant.name if request.user.tenant else None,
        'modules': sidebar_data
    })


@extend_schema(tags=['TenantModule'])
class TenantModuleViewSet(RBACViewSet):
    """TenantModule - Tenant admin can enable/disable modules for their tenant"""
    queryset = TenantModule.objects.select_related('tenant', 'module', 'submodule').all()
    serializer_class = TenantModuleSerializer
    permission_classes = [IsTenantAdmin]
    tenant_field = 'tenant'
    lookup_value_regex = '[^/]+'
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return TenantModule.objects.select_related('tenant', 'module', 'submodule').all()
        return TenantModule.objects.filter(tenant=self.request.user.tenant).select_related('tenant', 'module', 'submodule')
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)

# ------------------------------------------------------------------------------------------
# Token authentication view

"""
API views for accounts app - Token authentication endpoint.
"""



@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'example': 'editor@gmail.com'},
                'password': {'type': 'string', 'example': 'your_password'},
            },
            'required': ['username', 'password']
        }
    },
    responses={
        200: OpenApiResponse(
            description='Token generated successfully',
            response={
                'type': 'object',
                'properties': {
                    'token': {'type': 'string', 'example': '9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b'},
                    'user_id': {'type': 'integer', 'example': 1},
                    'email': {'type': 'string', 'example': 'editor@gmail.com'},
                    'tenant': {'type': 'string', 'example': 'Tenant A'},
                }
            }
        ),
        400: OpenApiResponse(description='Invalid credentials'),
    },
    tags=['Authentication'],
    summary='Obtain API Token',
)
@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_auth_token(request):

    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Both email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(request=request,email=email, password=password)
    
    if user:
        token,created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'email': user.email,
            'tenant': user.tenant.name if user.tenant else None,
        }, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_400_BAD_REQUEST
        )
