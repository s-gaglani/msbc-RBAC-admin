from rest_framework import serializers
from msbc_json_config_engine.apps.config_engine.models import ConfigInstance


class TenantOverrideSerializer(serializers.ModelSerializer):
    # Mandatory for tenant
    config_key = serializers.CharField(max_length=255)
    scope_id = serializers.CharField(max_length=255)
    release_version = serializers.CharField(max_length=50)
    config_json = serializers.JSONField()
    is_active = serializers.BooleanField()

    # Auto-resolved in service — optional in request
    base_config_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    base_release_version = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    base_config_hash = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)

    # Not applicable for tenant — always null
    parent_config_instance_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    class Meta:
        model = ConfigInstance
        fields = [
            "config_key", "scope_type", "scope_id",
            "release_version", "config_json", "is_active",
            "base_config_id", "base_release_version",
            "base_config_hash", "parent_config_instance_id",
        ]

    def to_internal_value(self, data):
        data = data.copy()
        data["scope_type"] = "tenant"
        for field in ("base_config_id", "parent_config_instance_id"):
            if data.get(field) == "":
                data[field] = None
        return super().to_internal_value(data)

    def validate(self, data):
        data["parent_config_instance_id"] = None
        return data

    def create(self, validated_data):
        from CommonAdminService.core.json_v1.services import TenantOverrideService
        return TenantOverrideService.create(validated_data)


class UserOverrideSerializer(serializers.ModelSerializer):
    # Mandatory for user
    config_key = serializers.CharField(max_length=255)
    scope_id = serializers.CharField(max_length=255)  # user_id
    tenant_id = serializers.CharField(max_length=255, write_only=True)  # used for auto-resolving parent
    release_version = serializers.CharField(max_length=50)
    config_json = serializers.JSONField()
    is_active = serializers.BooleanField()

    # Optional — auto-resolved from active tenant or OOB if not provided
    parent_config_instance_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    base_config_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    base_release_version = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    base_config_hash = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)

    class Meta:
        model = ConfigInstance
        fields = [
            "config_key", "scope_type", "scope_id", "tenant_id",
            "release_version", "config_json", "is_active",
            "parent_config_instance_id", "base_config_id",
            "base_release_version", "base_config_hash",
        ]

    def to_internal_value(self, data):
        data = data.copy()
        data["scope_type"] = "user"
        for field in ("base_config_id", "parent_config_instance_id"):
            if data.get(field) == "":
                data[field] = None
        return super().to_internal_value(data)

    def create(self, validated_data):
        from CommonAdminService.core.json_v1.services import UserOverrideService
        return UserOverrideService.create(validated_data)


class OOBConfigCreateSerializer(serializers.ModelSerializer):
    # Optional fields — if not provided or blank, forced to null for OOB
    scope_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    base_config_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    base_release_version = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    base_config_hash = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    parent_config_instance_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    class Meta:
        model = ConfigInstance
        fields = [
            "config_key", "scope_type", "scope_id",
            "release_version", "config_json", "is_active",
            "base_config_id", "base_release_version",
            "base_config_hash", "parent_config_instance_id",
        ]

    def validate_scope_type(self, value):
        if value != "oob":
            raise serializers.ValidationError("This endpoint only accepts scope_type='oob'.")
        return value

    def validate(self, data):
        # Force all non-mandatory lineage fields to null for OOB regardless of input
        data["scope_id"] = None
        data["base_config_id"] = None
        data["base_release_version"] = None
        data["base_config_hash"] = None
        data["parent_config_instance_id"] = None
        return data

    def to_internal_value(self, data):
        # Convert empty strings to None for UUID fields before validation
        for field in ("base_config_id", "parent_config_instance_id"):
            if data.get(field) == "":
                data[field] = None
        return super().to_internal_value(data)

    def create(self, validated_data):
        from CommonAdminService.core.json_v1.services import OOBConfigService
        return OOBConfigService.create(validated_data)
