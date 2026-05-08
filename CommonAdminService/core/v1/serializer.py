from msbc_rbac.core.models import Module,SubModule,ModuleSubModuleMapping,Role,RolePermission,Permission, TenantModule
from msbc_rbac.accounts.models import UserRole
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from django.apps import apps



User = get_user_model()
Tenant = apps.get_model(settings.TENANT_MODEL)

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['code', 'name', 'is_active']
        read_only_fields = ['code']

class TenantCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    tenant_name = serializers.CharField(max_length=255)
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_tenant_name(self, value):
        if Tenant.objects.filter(name=value).exists():
            raise serializers.ValidationError("Tenant name already exists")
        return value
    
    def create(self, validated_data):
        tenant = Tenant.objects.create(
            name=validated_data['tenant_name'],
            is_active=True
        )
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            tenant=tenant,
            is_staff=True
        )
        return {'tenant': tenant, 'user': user}

class UserSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source = 'tenant.name',read_only=True)

    class Meta:
        model = User
        fields = ['id' , 'username' , 'email' , "first_name" ,'last_name','tenant','tenant_name','is_active']
        read_only_fields = ['id']

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['code', 'name', 'icon', 'order']

class SubModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubModule
        fields = ['code', 'name', 'icon', 'order']

class ModuleSubModuleMappingSerializer(serializers.ModelSerializer):
    module_name = serializers.CharField(source = 'module.name',read_only = True)
    submodule_name = serializers.CharField(source = 'submodule.name',read_only=True)

    class Meta:
        model = ModuleSubModuleMapping
        fields = ['id', 'module', 'module_name', 'submodule', 'submodule_name']
        read_only_fields = ['id']

class RoleSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'tenant', 'tenant_name', 'is_active']
        read_only_fields = ['id', 'tenant']

class PermissionSerializer(serializers.ModelSerializer):
    module_name = serializers.CharField(source='module.name', read_only=True)
    submodule_name = serializers.CharField(source='submodule.name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = Permission
        fields = ['id', 'tenant', 'tenant_name', 'module', 'module_name', 'submodule', 'submodule_name', 'code', 'description', 'is_active']
        read_only_fields = ['id', 'tenant']

class RolePermissionSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    permission_code = serializers.CharField(source='permission.code', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'role_name', 'permission', 'permission_code', 'allowed', 'tenant', 'tenant_name']
        read_only_fields = ['id', 'tenant']

class UserRoleSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'user', 'username', 'role', 'role_name', 'tenant', 'tenant_name', 'hierarchy_level_override']
        read_only_fields = ['id', 'tenant']

class UserRolePermissionAssignSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    role_permissions = serializers.PrimaryKeyRelatedField(
        queryset=RolePermission.objects.all(),
        many=True
    )
    
    def validate(self, data):
        user = data.get('user')
        role_permissions = data.get('role_permissions')
        
        request = self.context.get('request')
        tenant = request.user.tenant
        
        if user.tenant and user.tenant != tenant:
            raise serializers.ValidationError("User must belong to same tenant")
        
        roles = set()
        for rp in role_permissions:
            if rp.tenant != tenant:
                raise serializers.ValidationError(f"RolePermission must belong to same tenant")
            roles.add(rp.role)
        
        if len(roles) > 1:
            raise serializers.ValidationError("All role-permissions must belong to the same role")
        
        data['role'] = roles.pop() if roles else None
        return data
    
    def create(self, validated_data):
        user = validated_data['user']
        role = validated_data['role']
        role_permissions = validated_data['role_permissions']
        tenant = self.context['request'].user.tenant
        
        if user.tenant is None:
            user.tenant = tenant
            user.save()
        
        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            tenant=tenant
        )
        
        return {
            'user_role': user_role,
            'role_permissions': role_permissions,
            'permissions_count': len(role_permissions)
        }
    
class TenantModuleSerializer(serializers.ModelSerializer):
    module_name = serializers.CharField(source='module.name', read_only=True)
    submodule_name = serializers.CharField(source='submodule.name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = TenantModule
        fields = ['id', 'tenant', 'tenant_name', 'module', 'module_name', 'submodule', 'submodule_name', 'is_enabled', 'expiration_date']
        read_only_fields = ['id', 'tenant']



