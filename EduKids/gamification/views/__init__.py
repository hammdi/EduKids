"""
Vues pour l'API gamification - EduKids

API REST pour la gestion des missions, badges, avatars et accessoires.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..models import (
    Mission, UserMission, Badge, UserBadge,
    Avatar, Accessory, UserAccessory
)
from ..serializers import (
    MissionSerializer, UserMissionSerializer, BadgeSerializer, UserBadgeSerializer,
    AvatarSerializer, AccessorySerializer, UserAccessorySerializer
)
from ..services import attribuer_points_et_badges

User = get_user_model()


class MissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les missions
    """
    queryset = Mission.objects.filter(actif=True)
    serializer_class = MissionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def du_jour(self, request):
        """
        Récupère les missions du jour pour l'utilisateur connecté
        """
        user = request.user
        # Pour simplifier, on retourne toutes les missions actives
        # En production, filtrer par date ou attribution spécifique
        missions = self.get_queryset()
        serializer = self.get_serializer(missions, many=True)
        return Response(serializer.data)


class UserMissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les missions des utilisateurs
    """
    queryset = UserMission.objects.all()
    serializer_class = UserMissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtre les missions de l'utilisateur connecté
        """
        return UserMission.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_progression(self, request, pk=None):
        """
        Met à jour la progression d'une mission utilisateur
        """
        user_mission = self.get_object()
        nouvelle_progression = request.data.get('progression', 0)

        if nouvelle_progression < 0:
            return Response(
                {'error': 'La progression ne peut pas être négative'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_mission.progression = min(nouvelle_progression, user_mission.mission.objectif)

        # Vérifier si la mission est terminée
        if user_mission.progression >= user_mission.mission.objectif:
            user_mission.statut = 'termine'
            user_mission.date_terminee = timezone.now()

            # Attribution automatique des points et badges
            result = attribuer_points_et_badges(user_mission)

        user_mission.save()
        serializer = self.get_serializer(user_mission)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        """
        Marque une mission comme terminée
        """
        user_mission = self.get_object()

        if user_mission.statut == 'termine':
            return Response(
                {'error': 'La mission est déjà terminée'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_mission.progression = user_mission.mission.objectif
        user_mission.statut = 'termine'
        user_mission.date_terminee = timezone.now()

        # Attribution automatique des points et badges
        result = attribuer_points_et_badges(user_mission)

        user_mission.save()
        serializer = self.get_serializer(user_mission)
        return Response(serializer.data)


class BadgeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les badges
    """
    queryset = Badge.objects.filter(is_active=True)
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]


class UserBadgeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les badges des utilisateurs
    """
    queryset = UserBadge.objects.all()
    serializer_class = UserBadgeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtre les badges de l'utilisateur connecté
        """
        return UserBadge.objects.filter(user=self.request.user)


class AvatarViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les avatars personnalisés
    """
    queryset = Avatar.objects.all()  # Queryset de base pour le router
    serializer_class = AvatarSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Avatar.objects.filter(student=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    @action(detail=False, methods=['get'])
    def my_avatar(self, request):
        """
        Retourne l'avatar de l'utilisateur actuel
        """
        try:
            from students.models import Student
            student = Student.objects.get(user=request.user)
        except Exception:
            return Response(
                {'error': 'Profil étudiant non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        avatar, created = Avatar.objects.get_or_create(
            student=student,
            defaults={
                'level': 1
            }
        )
        serializer = self.get_serializer(avatar)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='my-avatar/upload_image')
    def upload_my_avatar_image(self, request):
        """
        Upload une nouvelle image pour l'avatar de l'utilisateur connecté
        """
        try:
            from students.models import Student
            student = Student.objects.get(user=request.user)
        except Exception:
            return Response(
                {'error': 'Profil étudiant non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        avatar, created = Avatar.objects.get_or_create(
            student=student,
            defaults={'level': 1}
        )
        
        if 'image' not in request.FILES:
            return Response(
                {'error': 'Image requise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation de la taille (2MB max)
        image_file = request.FILES['image']
        if image_file.size > 2 * 1024 * 1024:
            return Response(
                {'error': 'Fichier trop volumineux. Maximum 2MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation du format
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if image_file.content_type not in allowed_types:
            return Response(
                {'error': 'Format non autorisé. Utilise JPG ou PNG.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        avatar.image = image_file
        avatar.updated_at = timezone.now()
        avatar.save()
        
        serializer = self.get_serializer(avatar)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def equip_accessory(self, request, pk=None):
        """
        Équipe un accessoire sur l'avatar
        """
        avatar = self.get_object()
        accessory_id = request.data.get('accessory_id')

        if not accessory_id:
            return Response(
                {'error': 'accessory_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer le profil étudiant
        try:
            from students.models import Student
            student = Student.objects.get(user=request.user)
        except Exception:
            return Response(
                {'error': 'Profil étudiant non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            user_accessory = UserAccessory.objects.get(
                student=student,
                accessory_id=accessory_id,
                status='owned'
            )
        except UserAccessory.DoesNotExist:
            return Response(
                {'error': 'Accessoire non possédé'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Équiper l'accessoire
        success = user_accessory.equip(avatar)
        if success:
            avatar.refresh_from_db()
            serializer = self.get_serializer(avatar)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Échec de l\'équipement'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def unequip_accessory(self, request, pk=None):
        """
        Déséquipe un accessoire de l'avatar
        """
        avatar = self.get_object()
        accessory_id = request.data.get('accessory_id')

        if not accessory_id:
            return Response(
                {'error': 'accessory_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer le profil étudiant
        try:
            from students.models import Student
            student = Student.objects.get(user=request.user)
        except Exception:
            return Response(
                {'error': 'Profil étudiant non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            user_accessory = UserAccessory.objects.get(
                student=student,
                accessory_id=accessory_id,
                status='equipped'
            )
        except UserAccessory.DoesNotExist:
            return Response(
                {'error': 'Accessoire non équipé'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Déséquiper l'accessoire
        user_accessory.unequip()
        avatar.refresh_from_db()

        serializer = self.get_serializer(avatar)
        return Response(serializer.data)


class AccessoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les accessoires
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
            student=request.user,
            status__in=['owned', 'equipped']
        ).select_related('accessory')
        accessories = [ua.accessory for ua in user_accessories]
        serializer = self.get_serializer(accessories, many=True)
        return Response(serializer.data)


class UserAccessoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les accessoires des utilisateurs
    """
    queryset = UserAccessory.objects.all()
    serializer_class = UserAccessorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAccessory.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    @action(detail=False, methods=['post'])
    def purchase(self, request):
        """
        Achète un accessoire
        """
        accessory_id = request.data.get('accessory')
        
        if not accessory_id:
            return Response(
                {'error': 'ID d\'accessoire requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            accessory = Accessory.objects.get(id=accessory_id, is_active=True)
        except Accessory.DoesNotExist:
            return Response(
                {'error': 'Accessoire non trouvé ou indisponible'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer le profil étudiant
        try:
            from students.models import Student
            student = Student.objects.get(user=request.user)
        except Exception:
            return Response(
                {'error': 'Profil étudiant non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier si déjà possédé
        existing = UserAccessory.objects.filter(
            student=student,
            accessory=accessory
        ).first()
        
        if existing and existing.status in ['owned', 'equipped']:
            return Response(
                {'error': 'Tu possèdes déjà cet accessoire !'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier les points
        if student.total_points < accessory.points_required:
            points_needed = accessory.points_required - student.total_points
            return Response(
                {'error': f'Points insuffisants. Il te faut encore {points_needed} points.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Effectuer l'achat
        student.total_points -= accessory.points_required
        student.save()
        
        # Créer ou mettre à jour UserAccessory
        if existing:
            existing.status = 'owned'
            existing.date_obtained = timezone.now()
            existing.save()
            user_accessory = existing
        else:
            user_accessory = UserAccessory.objects.create(
                student=student,
                accessory=accessory,
                status='owned'
            )
        
        serializer = self.get_serializer(user_accessory)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# Vue Django pour la page avatar
@login_required
def avatar_view(request):
    """
    Vue pour la page de personnalisation d'avatar
    """
    try:
        from students.models import Student
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Aucun profil étudiant associé à ce compte. Veuillez vous inscrire comme élève.")
        return redirect('home')

    avatar, created = Avatar.objects.get_or_create(
        student=student,
        defaults={
            'level': 1
        }
    )

    accessories = Accessory.objects.filter(is_active=True).prefetch_related('user_ownerships')
    
    owned_accessories = []
    available_accessories = []
    
    for accessory in accessories:
        user_accessory = accessory.user_ownerships.filter(student=student).first()
        accessory.is_owned_by_user = user_accessory is not None
        accessory.is_equipped = user_accessory and user_accessory.status == 'equipped' if user_accessory else False
        
        if accessory.is_owned_by_user:
            owned_accessories.append(accessory)
        else:
            available_accessories.append(accessory)

    context = {
        'avatar': avatar,
        'accessories': accessories,
        'owned_accessories': owned_accessories,
        'available_accessories': available_accessories,
        'owned_count': len(owned_accessories),
        'available_count': len(available_accessories),
        'user': request.user,
    }
    return render(request, 'gamification/avatar.html', context)