from django.urls import path
from CommonAdminService.core.json_v1.views import OOBConfigCreateView, TenantOverrideView, UserOverrideView
from msbc_json_config_engine.apps.config_engine.views import (
    GetEffectiveConfigView,
    CreateOverrideView,
    ResetToOOBView,
    GetLineageView,
    DiffConfigView,
    OutdatedConfigsView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path("config/", GetEffectiveConfigView.as_view(), name="config-effective"),
    # path("config/override/", CreateOverrideView.as_view(), name="config-override"),  # replaced by scope-specific endpoints below
    path("config/reset/", ResetToOOBView.as_view(), name="config-reset"),
    path("config/lineage/", GetLineageView.as_view(), name="config-lineage"),
    path("config/diff/", DiffConfigView.as_view(), name="config-diff"),
    path("config/outdated/", OutdatedConfigsView.as_view(), name="config-outdated"),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('json', SpectacularSwaggerView.as_view(url_name='schema')),

    path("config/oob/create/", OOBConfigCreateView.as_view(), name="config-oob-create"),
    path("config/oob/tenant/override/", TenantOverrideView.as_view(), name="config-tenant-override"),
    path("config/oob/user/override/", UserOverrideView.as_view(), name="config-user-override"),
]
