import pkgutil
from pathlib import Path
import msbc_json_config_engine
from decouple import config

PROJECT_SCOPE = config("PROJECT_SCOPE",default="core")

BASE_DIR = Path(__file__).resolve().parent.parent

EXTERNAL_MIGRATION_ROOT = BASE_DIR / "migrations_external"


AUTHORITATIVE_SCHEMA_SERVICE = (
    config("AUTHORITATIVE_SCHEMA_SERVICE", default="False").lower() == "true"
)

MIGRATION_MODULES = {}



def discover_shared_apps_utils():
    shared_apps_list = []
    try:
        import common_models_service
        
        """
        Discover shared Django apps inside msbc_json_config_engine.

        Returns:
            list[str]: app labels
        """
        project_scope = config('PROJECT_SCOPE',default = "v1")
        base_path = Path(common_models_service.__path__[0])

        shared_apps_list = []

        for service in pkgutil.iter_modules([str(base_path)]):
            service_path = base_path / service.name

            print(service.name, "service_name")

            if not service_path.is_dir():
                continue

            if not service_path.is_dir() or project_scope.lower() != service.name.lower():
                continue

            for app_dir in service_path.iterdir():
                if app_dir.is_dir() and (app_dir / "__init__.py").exists():
                    shared_apps_list.append(app_dir.name)


        print(f"[ACMD] Shared apps: {shared_apps_list}")
    except Exception as e:
        print(f"{e}")
    return shared_apps_list




def discover_shared_apps():
    """
    Discover shared Django apps inside msbc_json_config_engine.

    Returns:
        list[str]: app labels
    """
    project_scope = config('PROJECT_SCOPE',default = "v1")
    base_path = Path(msbc_json_config_engine.__path__[0])

    shared_apps_list = []

    for service in pkgutil.iter_modules([str(base_path)]):
        service_path = base_path / service.name

        print(service.name, "service_name")

        if not service_path.is_dir():
            continue

        if not service_path.is_dir() or project_scope.lower() != service.name.lower():
            continue

        for app_dir in service_path.iterdir():
            if app_dir.is_dir() and (app_dir / "__init__.py").exists():
                shared_apps_list.append(app_dir.name)


    print(f"[ACMD] Shared apps: {shared_apps_list}")
    return shared_apps_list



def discover_shared_rbac_apps():


    shared_apps_list = []

    try:
        import msbc_rbac

        base_path = Path(msbc_rbac.__path__[0])

        for service in pkgutil.iter_modules([str(base_path)]):
            service_path = base_path / service.name

            if service_path.is_dir() and (service_path / "__init__.py").exists():
                shared_apps_list.append(service_path.name)

        print(f"[ACMD] Shared apps RBAC: {shared_apps_list}")
    except ImportError as e:
        print(f"[ACMD] Shared apps RBAC: No module found rbac")
    return shared_apps_list


def discover_internal_apps():
    """
    Discover internal Django apps inside project directory.

    Rule:
        - Folder must exist in BASE_DIR
        - Must contain __init__.py
    """

    base_path = BASE_DIR
    internal_apps_list = []

    for module in pkgutil.iter_modules([str(base_path)]):
        app_path = base_path / module.name

        # Skip migrations_external folder itself
        if module.name == "migrations_external":
            continue

        if not app_path.is_dir():
            continue

        # 🔥 Real django app folder
        if (app_path / "__init__.py").exists():
            internal_apps_list.append(module.name)

    print(f"[ACMD] Internal apps: {internal_apps_list}")
    return internal_apps_list


shared_apps = discover_shared_apps()
shared_apps += discover_shared_apps_utils()
print("[ACMD] Shared apps before :", shared_apps)
shared_rbac_apps = discover_shared_rbac_apps()
print("[ACMD] Shared apps After :", shared_rbac_apps)
internal_apps = discover_internal_apps()


def ensure_migration_dirs():

    print("Shared apps:", shared_apps)
    print("internal_apps:", internal_apps)

    """
    Create migration directories.

    External:
        migrations_external/<PROJECT_SCOPE>/<shared_app>/

    Internal:
        <internal_app>/migrations/<PROJECT_SCOPE>/
    """

    # =====================================
    # External folders (ONLY authoritative)
    # =====================================
    if AUTHORITATIVE_SCHEMA_SERVICE:

        EXTERNAL_MIGRATION_ROOT.mkdir(parents=True, exist_ok=True)
        (EXTERNAL_MIGRATION_ROOT / "__init__.py").touch(exist_ok=True)

        project_path = EXTERNAL_MIGRATION_ROOT / PROJECT_SCOPE
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "__init__.py").touch(exist_ok=True)

        for app in shared_apps:
            app_path = project_path / app
            app_path.mkdir(parents=True, exist_ok=True)
            (app_path / "__init__.py").touch(exist_ok=True)

        for app in shared_rbac_apps:
            app_path = project_path / app
            app_path.mkdir(parents=True, exist_ok=True)
            (app_path / "__init__.py").touch(exist_ok=True)

    # =====================================
    # Internal folders (ALWAYS)
    # =====================================
    for app in internal_apps:
        internal_path = BASE_DIR / app / "migrations" / PROJECT_SCOPE
        internal_path.mkdir(parents=True, exist_ok=True)
        (internal_path / "__init__.py").touch(exist_ok=True)


def get_migration_modules():
    """
    Build MIGRATION_MODULES safely.

    Only:
        - shared apps
        - internal apps

    NEVER iterate over INSTALLED_APPS.
    """


    # =====================================
    # External Shared Apps
    # =====================================

    print("[ACMD] Building MIGRATION_MODULES...",shared_apps)
    print("[ACMD] Building MIGRATION_MODULES...",AUTHORITATIVE_SCHEMA_SERVICE)
    for app in shared_apps:
        if AUTHORITATIVE_SCHEMA_SERVICE:
            MIGRATION_MODULES[app] = (
                f"migrations_external.{PROJECT_SCOPE}.{app}"
            )
        else:
            MIGRATION_MODULES[app] = None


    for app in shared_rbac_apps:
        print("calling shared app", shared_rbac_apps)
        if AUTHORITATIVE_SCHEMA_SERVICE:
            MIGRATION_MODULES[app] = (
                f"migrations_external.{PROJECT_SCOPE}.{app}"
            )
        else:
            MIGRATION_MODULES[app] = None
    # =====================================
    # Internal Apps
    # =====================================
    for app in internal_apps:
        MIGRATION_MODULES[app] = (
            f"{app}.migrations.{PROJECT_SCOPE}"
        )

    return MIGRATION_MODULES
