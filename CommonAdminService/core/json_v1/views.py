from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from CommonAdminService.core.json_v1.serilaizers import OOBConfigCreateSerializer, TenantOverrideSerializer, UserOverrideSerializer


class UserOverrideView(APIView):
    @extend_schema(
        request=UserOverrideSerializer,
        responses={
            201: UserOverrideSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
        summary="Create or replace User Config Override",
    )
    def post(self, request):
        serializer = UserOverrideSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(UserOverrideSerializer(instance).data, status=status.HTTP_201_CREATED)


class TenantOverrideView(APIView):
    @extend_schema(
        request=TenantOverrideSerializer,
        responses={
            201: TenantOverrideSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
        summary="Create or replace Tenant Config Override",
    )
    def post(self, request):
        serializer = TenantOverrideSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(TenantOverrideSerializer(instance).data, status=status.HTTP_201_CREATED)


class OOBConfigCreateView(APIView):
    @extend_schema(
        request=OOBConfigCreateSerializer,
        responses={
            201: OpenApiResponse(description="OOB config created"),
            400: OpenApiResponse(description="Validation error"),
        },
        summary="Create OOB Config",
    )
    def post(self, request):
        serializer = OOBConfigCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(
            {"id": str(instance.id), "release_version": instance.release_version},
            status=status.HTTP_201_CREATED,
        )
