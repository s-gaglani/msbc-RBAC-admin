from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated



class RBACViewSet(viewsets.ModelViewSet):
    """
    Framework-level API base class.

    Responsibilities:
    - Enforce RBAC once (via permission_api_resolver)
    - Provide Swagger-safe serializer + lookup typing
    - Centralize tenant-aware queryset filtering
    """

    permission_classes = [IsAuthenticated]

    # Swagger / router guarantees
    serializer_class = None
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    lookup_value_regex = "[0-9]+"

    # Optional (model-backed ViewSets)
    queryset = None
    tenant_field = "tenant"

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # RBAC is enforced by RBACMiddleware before this point
        # No need to check again here


    # ─────────────────────────────
    # Serializer contract
    # ─────────────────────────────
    def get_serializer_class(self):
        if self.serializer_class is None:
            raise AssertionError(
                f"{self.__class__.__name__} must define serializer_class"
            )
        return self.serializer_class

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    # ─────────────────────────────
    # Tenant-aware queryset
    # ─────────────────────────────
    def get_queryset(self):
        if self.queryset is None:
            raise AssertionError(
                f"{self.__class__.__name__} must define queryset "
                "or override get_queryset()"
            )

        tenant = self.request.user.tenant
        return self.queryset.filter(**{self.tenant_field: tenant})
