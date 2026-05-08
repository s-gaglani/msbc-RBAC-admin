from django.db import transaction
from msbc_json_config_engine.apps.config_engine.models import ConfigInstance
from msbc_json_config_engine.apps.config_engine.services import ConfigResolutionService
from msbc_json_config_engine.apps.config_engine.utils import ConfigHasher


class TenantOverrideService:
    @staticmethod
    def create(data: dict) -> ConfigInstance:
        config_key = data["config_key"]
        scope_id = data["scope_id"]

        with transaction.atomic():
            # Deactivate existing active tenant override for this scope
            ConfigInstance.objects.filter(
                config_key=config_key,
                scope_type="tenant",
                scope_id=scope_id,
                is_active=True,
            ).update(is_active=False)

            # Auto-resolve OOB base if not provided
            oob = ConfigResolutionService.get_active(config_key, scope_type="oob", scope_id=None)
            base_config_id = data.get("base_config_id") or (oob.id if oob else None)
            base_release_version = data.get("base_release_version") or (oob.release_version if oob else None)
            base_config_hash = data.get("base_config_hash") or (ConfigHasher.generate_hash(oob.config_json) if oob else None)

            instance = ConfigInstance(
                config_key=config_key,
                scope_type="tenant",
                scope_id=scope_id,
                release_version=data["release_version"],
                config_json=data["config_json"],
                is_active=data["is_active"],
                base_config_id=base_config_id,
                base_release_version=base_release_version,
                base_config_hash=base_config_hash,
                parent_config_instance_id=None,
            )
            # Skip Python-level unique check — deactivation already happened above
            # DB partial index (WHERE is_active=True) handles the real constraint
            instance.save()

        ConfigResolutionService.invalidate_cache(config_key, tenant_id=scope_id)
        return instance


class UserOverrideService:
    @staticmethod
    def create(data: dict) -> ConfigInstance:
        config_key = data["config_key"]
        scope_id = data["scope_id"]  # user_id
        tenant_id = data.pop("tenant_id", None)

        with transaction.atomic():
            ConfigInstance.objects.filter(
                config_key=config_key,
                scope_type="user",
                scope_id=scope_id,
                is_active=True,
            ).update(is_active=False)

            # Resolve parent: provided → active tenant → active OOB
            parent_config_instance_id = data.get("parent_config_instance_id")
            if not parent_config_instance_id:
                parent = (
                    ConfigResolutionService.get_active(config_key, scope_type="tenant", scope_id=tenant_id)
                    if tenant_id else None
                ) or ConfigResolutionService.get_active(config_key, scope_type="oob", scope_id=None)
                parent_config_instance_id = parent.id if parent else None

            # Resolve OOB base lineage
            oob = ConfigResolutionService.get_active(config_key, scope_type="oob", scope_id=None)
            base_config_id = data.get("base_config_id") or (oob.id if oob else None)
            base_release_version = data.get("base_release_version") or (oob.release_version if oob else None)
            base_config_hash = data.get("base_config_hash") or (ConfigHasher.generate_hash(oob.config_json) if oob else None)

            instance = ConfigInstance(
                config_key=config_key,
                scope_type="user",
                scope_id=scope_id,
                release_version=data["release_version"],
                config_json=data["config_json"],
                is_active=data["is_active"],
                parent_config_instance_id=parent_config_instance_id,
                base_config_id=base_config_id,
                base_release_version=base_release_version,
                base_config_hash=base_config_hash,
            )
            instance.save()

        ConfigResolutionService.invalidate_cache(config_key, user_id=scope_id)
        return instance


class OOBConfigService:
    @staticmethod
    def create(data: dict) -> ConfigInstance:
        # Deactivate any existing active OOB for the same config_key + release_version
        ConfigInstance.objects.filter(
            config_key=data["config_key"],
            scope_type="oob",
            scope_id=None,
            is_active=True,
        ).update(is_active=False)

        return ConfigInstance.objects.create(
            config_key=data["config_key"],
            scope_type="oob",
            scope_id=None,
            release_version=data["release_version"],
            config_json=data["config_json"],
            is_active=data["is_active"],
            base_config_id=None,
            base_release_version=None,
            base_config_hash=None,
            parent_config_instance_id=None,
        )
