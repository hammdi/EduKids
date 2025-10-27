"""
Vues API pour l'application gamification - EduKids

Points de terminaison REST pour la gestion des missions, badges, avatars et accessoires.
"""
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from .models import (
    Badge, UserBadge, Mission, UserMission,
    Avatar, Accessory, UserAccessory
)
from .serializers import (
    BadgeSerializer, UserBadgeSerializer, MissionSerializer, UserMissionSerializer,
    AvatarSerializer, AccessorySerializer, UserAccessorySerializer
)
from .services import attribuer_points_et_badges

User = get_user_model()


@login_required
def avatar_view(request):
    """
    Vue pour la personnalisation d'avatar - redirige vers customize_avatar
    """
    try:
        if hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
            avatar, created = Avatar.objects.get_or_create(
                student=student,
                defaults={
                    'name': f"Avatar de {request.user.first_name}",
                    'is_active': True,
                    'level': 1
                }
            )
            
            # Get user's accessories/inventory
            user_accessories = UserAccessory.objects.filter(student=student).select_related('accessory')
            inventory = []
            equipped_count = 0
            
            for ua in user_accessories:
                inventory.append({
                    'id': ua.id,
                    'accessory': ua.accessory,
                    'is_equipped': ua.status == 'equipped',
                    'acquisition_date': ua.acquisition_date
                })
                if ua.status == 'equipped':
                    equipped_count += 1
            
            return render(request, 'students/gamification/customize_avatar.html', {
                'avatar': avatar,
                'inventory': inventory,
                'total_items': len(inventory),
                'equipped_count': equipped_count
            })
        else:
            return redirect('profile')
    except Exception as e:
        return render(request, 'gamification/avatar.html', {'error': str(e)})


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
            user_mission.statut = 'terminee'
            user_mission.date_terminee = timezone.now()
            user_mission.save()

            # Attribuer les points et badges
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


class AvatarViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les avatars personnalisés
    """
    queryset = Avatar.objects.all()  # Queryset de base pour le router
    serializer_class = AvatarSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Avatar.objects.filter(student=self.request.user.student_profile, is_active=True)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.student_profile)

    @action(detail=False, methods=['get', 'post'], url_path='my-avatar')
    def my_avatar(self, request):
        """
        GET: Retourne l'avatar de l'utilisateur actuel
        POST: Met à jour l'avatar (nom, etc.)
        """
        avatar, created = Avatar.objects.get_or_create(
            student=request.user.student_profile,
            defaults={
                'name': f"Avatar de {request.user.first_name}",
                'is_active': True,
                'level': 1
            }
        )
        
        if request.method == 'POST':
            # Mettre à jour les champs si fournis
            if 'name' in request.data:
                avatar.name = request.data['name']
                avatar.save()
        
        serializer = self.get_serializer(avatar)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='my-avatar/upload_image')
    def upload_my_avatar_image(self, request):
        """
        Upload une nouvelle image pour l'avatar de l'utilisateur actuel
        POST /gamification/api/avatars/my-avatar/upload_image/
        """
        try:
            from PIL import Image
        except ImportError:
            return Response({
                'success': False,
                'error': 'Pillow non installé. Contactez l\'administrateur.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Vérifier que l'utilisateur est un étudiant
        if not hasattr(request.user, 'student_profile'):
            return Response({
                'success': False,
                'error': 'Profil étudiant non trouvé. Seuls les étudiants peuvent uploader un avatar.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Récupérer ou créer l'avatar
            avatar, created = Avatar.objects.get_or_create(
                student=request.user.student_profile,
                defaults={
                    'name': f"Avatar de {request.user.first_name}",
                    'is_active': True,
                    'level': 1
                }
            )
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Erreur lors de la création de l\'avatar : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if 'image' not in request.FILES:
            return Response({
                'success': False,
                'error': 'Aucune image fournie. Veuillez sélectionner une image.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # Validation du format
        allowed_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if image_file.content_type not in allowed_formats:
            return Response({
                'success': False,
                'error': 'Format non supporté. Utilisez JPG, PNG, GIF ou WebP.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation de la taille (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if image_file.size > max_size:
            return Response({
                'success': False,
                'error': 'Image trop grande. Taille maximale : 5MB.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Vérifier que c'est une image valide
            img = Image.open(image_file)
            img.verify()
            
            # Réouvrir l'image après verify()
            image_file.seek(0)
            
            # Sauvegarder l'image
            avatar.image = image_file
            avatar.save()
            
            serializer = self.get_serializer(avatar)
            return Response({
                'success': True,
                'message': 'Avatar mis à jour avec succès !',
                'avatar': serializer.data,
                'image_url': avatar.image.url if avatar.image else None
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Erreur lors du traitement de l\'image : {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        """
        Upload une nouvelle image pour l'avatar (avec pk)
        """
        avatar = self.get_object()
        
        if 'image' not in request.FILES:
            return Response(
                {'error': 'Image requise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        avatar.image = request.FILES['image']
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

        try:
            user_accessory = UserAccessory.objects.get(
                student=request.user.student_profile,
                accessory_id=accessory_id,
                status='owned'
            )
        except UserAccessory.DoesNotExist:
            return Response(
                {'error': 'Accessoire non possédé'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Équiper l'accessoire
        user_accessory.equip()
        avatar.refresh_from_db()

        serializer = self.get_serializer(avatar)
        return Response(serializer.data)

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

        try:
            user_accessory = UserAccessory.objects.get(
                student=request.user.student_profile,
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
            student=request.user.student_profile,
            status__in=['owned', 'equipped']
        ).select_related('accessory')
        accessories = [ua.accessory for ua in user_accessories]
        serializer = self.get_serializer(accessories, many=True)
        return Response(serializer.data)


class UserAccessoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les accessoires des utilisateurs
    """
    serializer_class = UserAccessorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAccessory.objects.filter(student=self.request.user.student_profile)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.student_profile)

    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        """
        Achète un accessoire
        """
        user_accessory = self.get_object()

        # Vérifier si déjà possédé
        if user_accessory.status in ['owned', 'equipped']:
            return Response(
                {'error': 'Accessoire déjà possédé'},
                status=status.HTTP_400_BAD_REQUEST
            )

        accessory = user_accessory.accessory

        # Vérifier les points de l'utilisateur
        student = request.user.student_profile
        if student.points < accessory.points_required:
            return Response(
                {'error': 'Points insuffisants'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier le niveau requis
        if hasattr(student, 'level') and student.level < accessory.level_required:
            return Response(
                {'error': 'Niveau insuffisant'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Effectuer l'achat
        student.points -= accessory.points_required
        student.save()

        user_accessory.status = 'owned'
        user_accessory.unlocked_at = timezone.now()
        user_accessory.save()

        serializer = self.get_serializer(user_accessory)
        return Response(serializer.data)
