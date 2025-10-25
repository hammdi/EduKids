"""
Vues pour l'API gamification - EduKids

Phase 3 : Avatars & Personnalisation avancée
"""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from ..models import (
    Badge, UserBadge, Mission, UserMission,
    Avatar, Accessory, UserAccessory
)
from ..serializers import (
    BadgeSerializer, UserBadgeSerializer, MissionSerializer, UserMissionSerializer,
    AvatarSerializer, AccessorySerializer, UserAccessorySerializer,
    AvatarUploadSerializer, AccessoryPurchaseSerializer, AccessoryEquipSerializer
)

User = get_user_model()


# Vues existantes pour compatibilité
class MissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les missions
    """
    queryset = Mission.objects.filter(actif=True)
    serializer_class = MissionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def du_jour(self, request):
        """
        Retourne les missions du jour pour l'utilisateur
        """
        missions = Mission.objects.filter(
            actif=True,
            date_expiration__gte=timezone.now().date()
        ).order_by('created_at')[:5]  # Limiter à 5 missions

        serializer = self.get_serializer(missions, many=True)
        return Response(serializer.data)


class UserMissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les missions des utilisateurs
    """
    serializer_class = UserMissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserMission.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_progression(self, request, pk=None):
        """
        Met à jour la progression d'une mission utilisateur
        """
        user_mission = self.get_object()
        nouvelle_progression = request.data.get('progression', 0)

        if nouvelle_progression >= user_mission.mission.objectif:
            user_mission.progression = user_mission.mission.objectif
            user_mission.statut = 'termine'
            user_mission.date_terminee = timezone.now()
            user_mission.save()

            # Attribuer les points et badges
            from ..services import attribuer_points_et_badges
            attribuer_points_et_badges(user_mission.user, user_mission.mission.points)

        else:
            user_mission.progression = nouvelle_progression
            user_mission.save()

        serializer = self.get_serializer(user_mission)
        return Response(serializer.data)


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les badges
    """
    queryset = Badge.objects.filter(is_active=True)
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]


class UserBadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les badges des utilisateurs
    """
    serializer_class = UserBadgeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserBadge.objects.filter(user=self.request.user)


# Nouvelles vues Phase 3
class AvatarViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les avatars personnalisés
    """
    serializer_class = AvatarSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Avatar.objects.filter(student__user=self.request.user)

    def perform_create(self, serializer):
        # Créer l'avatar pour l'utilisateur connecté
        student = self.request.user.student_profile
        serializer.save(student=student)

    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        """
        Upload d'une nouvelle image d'avatar
        """
        avatar = self.get_object()

        # Vérifier que c'est bien l'avatar de l'utilisateur
        if avatar.student.user != request.user:
            return Response(
                {'error': 'Accès non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AvatarUploadSerializer(avatar, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Retourner l'avatar mis à jour
            response_serializer = AvatarSerializer(avatar, context={'request': request})
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccessoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les accessoires disponibles
    """
    queryset = Accessory.objects.filter(is_active=True)
    serializer_class = AccessorySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def owned(self, request):
        """
        Retourne les accessoires possédés par l'utilisateur
        """
        user_accessories = UserAccessory.objects.filter(
            student__user=request.user,
            status__in=['owned', 'equipped']
        ).select_related('accessory')

        accessories = [ua.accessory for ua in user_accessories]
        serializer = self.get_serializer(accessories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        """
        Acheter un accessoire
        """
        accessory = self.get_object()

        # Vérifier si déjà possédé
        user_accessory, created = UserAccessory.objects.get_or_create(
            student=request.user.student_profile,
            accessory=accessory,
            defaults={'status': 'unlocked'}
        )

        if user_accessory.status in ['owned', 'equipped']:
            return Response(
                {'error': 'Accessoire déjà possédé', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Tenter l'achat
        if user_accessory.purchase():
            # Retourner l'état mis à jour
            response_data = {
                'success': True,
                'message': f'Accessoire "{accessory.name}" acheté avec succès !',
                'accessory': AccessorySerializer(accessory, context={'request': request}).data,
                'new_points_balance': request.user.student_profile.points
            }
            return Response(response_data)
        else:
            return Response(
                {
                    'error': 'Points insuffisants',
                    'required_points': accessory.points_required,
                    'current_points': request.user.student_profile.points,
                    'success': False
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def equip(self, request, pk=None):
        """
        Équiper un accessoire
        """
        accessory = self.get_object()

        try:
            user_accessory = UserAccessory.objects.get(
                student__user=request.user,
                accessory=accessory,
                status='owned'
            )
        except UserAccessory.DoesNotExist:
            return Response(
                {'error': 'Accessoire non possédé', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtenir ou créer l'avatar de l'utilisateur
        avatar, created = Avatar.objects.get_or_create(
            student=request.user.student_profile,
            defaults={'level': 1}
        )

        # Équiper l'accessoire
        if user_accessory.equip(avatar):
            response_data = {
                'success': True,
                'message': f'Accessoire "{accessory.name}" équipé !',
                'avatar': AvatarSerializer(avatar, context={'request': request}).data
            }
            return Response(response_data)
        else:
            return Response(
                {'error': 'Impossible d\'équiper l\'accessoire', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def unequip(self, request, pk=None):
        """
        Déséquiper un accessoire
        """
        accessory = self.get_object()

        try:
            user_accessory = UserAccessory.objects.get(
                student__user=request.user,
                accessory=accessory,
                status='equipped'
            )
        except UserAccessory.DoesNotExist:
            return Response(
                {'error': 'Accessoire non équipé', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtenir l'avatar de l'utilisateur
        try:
            avatar = Avatar.objects.get(student__user=request.user)
        except Avatar.DoesNotExist:
            return Response(
                {'error': 'Avatar non trouvé', 'success': False},
                status=status.HTTP_404_NOT_FOUND
            )

        # Déséquiper l'accessoire
        if user_accessory.unequip(avatar):
            response_data = {
                'success': True,
                'message': f'Accessoire "{accessory.name}" déséquipé !',
                'avatar': AvatarSerializer(avatar, context={'request': request}).data
            }
            return Response(response_data)
        else:
            return Response(
                {'error': 'Impossible de déséquiper l\'accessoire', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserAccessoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les accessoires des utilisateurs
    """
    serializer_class = UserAccessorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAccessory.objects.filter(student__user=self.request.user)