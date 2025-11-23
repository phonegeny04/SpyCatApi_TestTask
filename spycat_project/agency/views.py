# agency/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Cat, Mission, Target
from .serializers import CatSerializer, MissionSerializer, TargetSerializer, TargetUpdateNotesSerializer


class CatViewSet(viewsets.ModelViewSet):
    queryset = Cat.objects.all()
    serializer_class = CatSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if hasattr(instance, 'current_mission') and instance.current_mission is not None:
            return Response(
                {"detail": "Cannot delete a spy cat that is currently assigned to a mission."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        allowed_fields = {'salary'}
        input_keys = set(request.data.keys())
        if not input_keys.issubset(allowed_fields):
            return Response(
                {"detail": "Only 'salary' field can be updated for a cat."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().partial_update(request, *args, **kwargs)


class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.all().prefetch_related('targets')
    serializer_class = MissionSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.cat is not None:
            return Response(
                {"detail": "Mission cannot be deleted because it is currently assigned to a cat."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='assign/(?P<cat_id>[^/.]+)')
    def assign_cat(self, request, pk=None, cat_id=None):
        mission = self.get_object()
        try:
            cat = Cat.objects.get(pk=cat_id)
        except Cat.DoesNotExist:
            return Response({"detail": "Cat not found."}, status=status.HTTP_404_NOT_FOUND)

        if not cat.is_available:
            return Response({"detail": "Cat is already assigned to another mission."},
                            status=status.HTTP_400_BAD_REQUEST)

        if mission.cat is not None:
            return Response({"detail": "Mission is already assigned."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            mission.cat = cat
            mission.save()
            cat.is_available = False
            cat.save()

        return Response(self.get_serializer(mission).data)

    @action(detail=False, methods=['put'], url_path='target/(?P<target_id>[^/.]+)/notes')
    def update_target_notes(self, request, target_id=None):
        try:
            target = Target.objects.select_related('mission').get(pk=target_id)
        except Target.DoesNotExist:
            return Response({"detail": "Target not found."}, status=status.HTTP_404_NOT_FOUND)

        if target.is_completed:
            return Response({"detail": "Notes cannot be updated, target is already completed."},
                            status=status.HTTP_400_BAD_REQUEST)
        if target.mission.is_completed:
            return Response({"detail": "Notes cannot be updated, mission is already completed."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = TargetSerializer(target, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'], url_path='target/(?P<target_id>[^/.]+)/complete')
    def complete_target(self, request, target_id=None):
        try:
            target = Target.objects.select_related('mission').get(pk=target_id)
        except Target.DoesNotExist:
            return Response({"detail": "Target not found."}, status=status.HTTP_404_NOT_FOUND)

        if target.is_completed:
            return Response({"detail": "Target is already completed."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            target.is_completed = True
            target.save()

            mission = target.mission

            if not mission.targets.filter(is_completed=False).exists():
                mission.is_completed = True
                mission.save()

                if mission.cat:
                    mission.cat.is_available = True
                    mission.cat.save()

        return Response(TargetSerializer(target).data)