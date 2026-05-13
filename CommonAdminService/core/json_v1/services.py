from django.db import transaction
from msbc_json_config_engine.apps.config_engine.models import ConfigInstance
from msbc_json_config_engine.apps.config_engine.services import ConfigResolutionService
from msbc_json_config_engine.apps.config_engine.utils import ConfigHasher

def deep_merge(base, tenant, user):
    # Dict merge
    if isinstance(base, dict) and isinstance(tenant, dict) and isinstance(user, dict):
        result = {}

        all_keys = set(base.keys()) | set(tenant.keys()) | set(user.keys())

        for key in all_keys:
            result[key] = deep_merge(
                base.get(key),
                tenant.get(key),
                user.get(key)
            )

        return result

    # List merge
    elif isinstance(base, list) and isinstance(tenant, list) and isinstance(user, list):

        # User additions
        user_added = [x for x in user if x not in base]

        # Tenant additions
        tenant_added = [x for x in tenant if x not in base]

        # Keep original base order
        merged = list(base)

        # Add tenant additions
        for item in tenant_added:
            if item not in merged:
                merged.append(item)

        # Add user additions
        for item in user_added:
            if item not in merged:
                merged.append(item)

        return merged

    # Primitive merge
    else:
        user_changed = user != base
        tenant_changed = tenant != base

        if user_changed:
            return user

        if tenant_changed:
            return tenant

        return tenant if tenant is not None else user


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
            instance.save()

            # Auto-merge new tenant fields into all active user overrides
            user_overrides = ConfigInstance.objects.filter(
                config_key=config_key,
                scope_type="user",
                is_active=True,
            )


            for user_override in user_overrides:
                old_parent = ConfigInstance.objects.filter(
                    id=user_override.parent_config_instance_id
                ).first()

                new_tenant_json = instance.config_json
                user_json = user_override.config_json

                # Tenant fields merged, user customizations take priority
                oob_json = oob.config_json if oob else {}
                merged_json = deep_merge(oob_json, new_tenant_json, user_json)


                ConfigInstance.objects.filter(id=user_override.id).update(is_active=False)

                ConfigInstance.objects.create(
                    config_key=config_key,
                    scope_type="user",
                    scope_id=user_override.scope_id,
                    release_version=instance.release_version,
                    config_json=merged_json,
                    is_active=True,
                    parent_config_instance_id=instance.id,
                    base_config_id=instance.base_config_id,
                    base_release_version=instance.base_release_version,
                    base_config_hash=instance.base_config_hash,
                )

                ConfigResolutionService.invalidate_cache(config_key, user_id=user_override.scope_id)

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
            tenant_override = (
                ConfigResolutionService.get_active(config_key, scope_type="tenant", scope_id=tenant_id)
                if tenant_id else None
            )
            oob = ConfigResolutionService.get_active(config_key, scope_type="oob", scope_id=None)

            # parent_config_instance_id = latest tenant override (or OOB if no tenant override)
            parent = tenant_override or oob
            parent_config_instance_id = parent.id if parent else None

            # base lineage always tracks OOB
            base_config_id = oob.id if oob else None
            base_release_version = oob.release_version if oob else None
            base_config_hash = ConfigHasher.generate_hash(oob.config_json) if oob else None

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
