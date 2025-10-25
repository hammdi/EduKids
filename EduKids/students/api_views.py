"""
API Views pour la gamification Student - EduKids
Tous les endpoints sont protégés par @student_required
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from .decorators import student_required
from .models import Student
from gamification.models import Badge, UserBadge, Accessory, UserAccessory, Avatar


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_points(request):
    """
    GET /api/student/points/
    Récupérer les points de l'étudiant
    """
    if request.user.user_type != 'student':
        return Response({'error': 'Accès réservé aux étudiants'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = request.user.student_profile
        return Response({
            'points': student.total_points,
            'level': getattr(student.avatar, 'level', 1) if hasattr(student, 'avatar') else 1,
            'username': request.user.get_full_name() or request.user.username
        })
    except Student.DoesNotExist:
        return Response({'error': 'Profil étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_student_points(request):
    """
    POST /api/student/points/add
    Ajouter des points à l'étudiant
    
    Body: {
        "points": 10,
        "reason": "Quiz réussi"
    }
    """
    if request.user.user_type != 'student':
        return Response({'error': 'Accès réservé aux étudiants'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = request.user.student_profile
        points_to_add = request.data.get('points', 0)
        reason = request.data.get('reason', 'Action réussie')
        
        if points_to_add <= 0:
            return Response({'error': 'Le nombre de points doit être positif'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Ajouter les points
        old_points = student.total_points
        student.total_points += points_to_add
        student.save()
        
        # Vérifier les badges à débloquer
        unlocked_badges = check_and_unlock_badges(request.user, student)
        
        # Vérifier le niveau de l'avatar
        if hasattr(student, 'avatar'):
            avatar = student.avatar
            new_level = (student.total_points // 100) + 1
            if new_level > avatar.level:
                avatar.level = new_level
                avatar.save()
                level_up = True
            else:
                level_up = False
        else:
            level_up = False
        
        return Response({
            'success': True,
            'points': student.total_points,
            'points_added': points_to_add,
            'old_points': old_points,
            'reason': reason,
            'level_up': level_up,
            'unlocked_badges': unlocked_badges
        })
    
    except Student.DoesNotExist:
        return Response({'error': 'Profil étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def daily_reward(request):
    """
    POST /api/student/points/daily-reward
    Récompense journalière (connexion quotidienne)
    """
    if request.user.user_type != 'student':
        return Response({'error': 'Accès réservé aux étudiants'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = request.user.student_profile
        
        # Vérifier la dernière connexion
        last_login = getattr(student, 'last_daily_reward', None)
        today = timezone.now().date()
        
        if last_login and last_login == today:
            return Response({
                'already_claimed': True,
                'message': 'Tu as déjà récupéré ta récompense aujourd\'hui !',
                'next_reward': 'Reviens demain pour plus de points !'
            })
        
        # Donner la récompense
        daily_points = 10
        student.total_points += daily_points
        student.last_daily_reward = today
        student.save()
        
        # Vérifier les badges
        unlocked_badges = check_and_unlock_badges(request.user, student)
        
        return Response({
            'success': True,
            'points_earned': daily_points,
            'total_points': student.total_points,
            'message': f'🎉 +{daily_points} points ! Reviens demain pour plus !',
            'unlocked_badges': unlocked_badges
        })
    
    except Student.DoesNotExist:
        return Response({'error': 'Profil étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_badges(request):
    """
    GET /api/student/badges/
    Récupérer tous les badges (gagnés et verrouillés)
    """
    if request.user.user_type != 'student':
        return Response({'error': 'Accès réservé aux étudiants'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = request.user.student_profile
        
        # Tous les badges disponibles
        all_badges = Badge.objects.filter(is_active=True)
        
        # Badges gagnés par l'utilisateur
        user_badges = UserBadge.objects.filter(
            user=request.user,
            date_obtained__isnull=False
        ).values_list('badge_id', flat=True)
        
        badges_data = []
        for badge in all_badges:
            is_unlocked = badge.id in user_badges
            user_badge = UserBadge.objects.filter(user=request.user, badge=badge).first()
            
            badges_data.append({
                'id': badge.id,
                'name': badge.name,
                'description': badge.description,
                'icon': badge.icon,
                'points_required': badge.points_required,
                'is_unlocked': is_unlocked,
                'date_obtained': user_badge.date_obtained.isoformat() if user_badge and user_badge.date_obtained else None,
                'progress': calculate_badge_progress(badge, student)
            })
        
        return Response({
            'badges': badges_data,
            'total_unlocked': len(user_badges),
            'total_available': all_badges.count()
        })
    
    except Student.DoesNotExist:
        return Response({'error': 'Profil étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)


def check_and_unlock_badges(user, student):
    """
    Vérifier et débloquer automatiquement les badges
    Retourne la liste des badges débloqués
    """
    unlocked_badges = []
    all_badges = Badge.objects.filter(is_active=True)
    
    for badge in all_badges:
        # Vérifier si déjà possédé
        user_badge, created = UserBadge.objects.get_or_create(
            user=user,
            badge=badge
        )
        
        if user_badge.date_obtained:
            continue  # Déjà débloqué
        
        # Vérifier les conditions
        should_unlock = False
        
        # Badge basé sur les points
        if badge.points_required and student.total_points >= badge.points_required:
            should_unlock = True
        
        # Badge "Premier login" (si l'utilisateur a des points)
        if 'premier' in badge.name.lower() and student.total_points > 0:
            should_unlock = True
        
        if should_unlock:
            user_badge.date_obtained = timezone.now()
            user_badge.save()
            unlocked_badges.append({
                'id': badge.id,
                'name': badge.name,
                'description': badge.description,
                'icon': badge.icon
            })
    
    return unlocked_badges


def calculate_badge_progress(badge, student):
    """
    Calculer la progression vers un badge
    """
    if badge.points_required:
        if student.total_points >= badge.points_required:
            return 100
        return int((student.total_points / badge.points_required) * 100)
    return 0


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_shop_items(request):
    """
    GET /api/student/shop/items
    Récupérer tous les accessoires de la boutique
    """
    if request.user.user_type != 'student':
        return Response({'error': 'Accès réservé aux étudiants'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = request.user.student_profile
        
        # Tous les accessoires actifs
        accessories = Accessory.objects.filter(is_active=True).order_by('points_required')
        
        # Accessoires possédés
        owned_ids = UserAccessory.objects.filter(
            student=student,
            status__in=['owned', 'equipped']
        ).values_list('accessory_id', flat=True)
        
        items_data = []
        for acc in accessories:
            items_data.append({
                'id': acc.id,
                'name': acc.name,
                'imageURL': acc.image.url if acc.image else None,
                'prixPoints': acc.points_required,
                'categorie': acc.accessory_type,
                'description': acc.description if hasattr(acc, 'description') else '',
                'is_owned': acc.id in owned_ids,
                'can_afford': student.total_points >= acc.points_required
            })
        
        return Response({
            'items': items_data,
            'student_points': student.total_points
        })
    
    except Student.DoesNotExist:
        return Response({'error': 'Profil étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_shop_item(request, item_id):
    """
    POST /api/student/shop/buy/{itemId}
    Acheter un accessoire
    """
    if request.user.user_type != 'student':
        return Response({'error': 'Accès réservé aux étudiants'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = request.user.student_profile
        accessory = Accessory.objects.get(id=item_id, is_active=True)
        
        # Vérifier si déjà possédé
        if UserAccessory.objects.filter(student=student, accessory=accessory).exists():
            return Response({'error': 'Tu possèdes déjà cet accessoire'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier les points
        if student.total_points < accessory.points_required:
            points_needed = accessory.points_required - student.total_points
            return Response({
                'error': f'Points insuffisants. Il te faut encore {points_needed} points.',
                'points_needed': points_needed
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Effectuer l'achat
        student.total_points -= accessory.points_required
        student.save()
        
        user_accessory = UserAccessory.objects.create(
            student=student,
            accessory=accessory,
            status='owned'
        )
        
        return Response({
            'success': True,
            'message': f'🎉 Tu as débloqué {accessory.name} !',
            'item': {
                'id': accessory.id,
                'name': accessory.name,
                'imageURL': accessory.image.url if accessory.image else None
            },
            'new_points': student.total_points,
            'points_spent': accessory.points_required
        })
    
    except Accessory.DoesNotExist:
        return Response({'error': 'Accessoire non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Student.DoesNotExist:
        return Response({'error': 'Profil étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_avatar_inventory(request):
    """
    GET /api/student/avatar/inventory
    Récupérer l'inventaire des accessoires
    """
    if request.user.user_type != 'student':
        return Response({'error': 'Accès réservé aux étudiants'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = request.user.student_profile
        
        # Accessoires possédés
        user_accessories = UserAccessory.objects.filter(
            student=student,
            status__in=['owned', 'equipped']
        ).select_related('accessory')
        
        inventory = []
        for ua in user_accessories:
            inventory.append({
                'id': ua.accessory.id,
                'name': ua.accessory.name,
                'imageURL': ua.accessory.image.url if ua.accessory.image else None,
                'categorie': ua.accessory.accessory_type,
                'is_equipped': ua.status == 'equipped',
                'date_obtained': ua.date_obtained.isoformat()
            })
        
        # Avatar info
        avatar = None
        if hasattr(student, 'avatar'):
            avatar = {
                'id': student.avatar.id,
                'imageURL': student.avatar.image.url if student.avatar.image else None,
                'level': student.avatar.level
            }
        
        return Response({
            'inventory': inventory,
            'avatar': avatar,
            'total_items': len(inventory)
        })
    
    except Student.DoesNotExist:
        return Response({'error': 'Profil étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def equip_item(request, item_id):
    """
    POST /api/student/avatar/equip/{itemId}
    Équiper un accessoire
    """
    if request.user.user_type != 'student':
        return Response({'error': 'Accès réservé aux étudiants'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = request.user.student_profile
        
        # Vérifier que l'accessoire est possédé
        user_accessory = UserAccessory.objects.get(
            student=student,
            accessory_id=item_id,
            status__in=['owned', 'equipped']
        )
        
        # Déséquiper les autres accessoires du même type
        UserAccessory.objects.filter(
            student=student,
            accessory__accessory_type=user_accessory.accessory.accessory_type,
            status='equipped'
        ).update(status='owned')
        
        # Équiper l'accessoire
        user_accessory.status = 'equipped'
        user_accessory.save()
        
        # Mettre à jour l'avatar
        if hasattr(student, 'avatar'):
            avatar = student.avatar
            avatar.accessories.add(user_accessory.accessory)
            avatar.save()
        
        return Response({
            'success': True,
            'message': f'✨ {user_accessory.accessory.name} équipé !',
            'item_id': item_id
        })
    
    except UserAccessory.DoesNotExist:
        return Response({'error': 'Accessoire non possédé'}, status=status.HTTP_404_NOT_FOUND)
    except Student.DoesNotExist:
        return Response({'error': 'Profil étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unequip_item(request, item_id):
    """
    POST /api/student/avatar/unequip/{itemId}
    Déséquiper un accessoire
    """
    if request.user.user_type != 'student':
        return Response({'error': 'Accès réservé aux étudiants'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = request.user.student_profile
        
        user_accessory = UserAccessory.objects.get(
            student=student,
            accessory_id=item_id,
            status='equipped'
        )
        
        user_accessory.status = 'owned'
        user_accessory.save()
        
        # Retirer de l'avatar
        if hasattr(student, 'avatar'):
            avatar = student.avatar
            avatar.accessories.remove(user_accessory.accessory)
            avatar.save()
        
        return Response({
            'success': True,
            'message': 'Accessoire retiré',
            'item_id': item_id
        })
    
    except UserAccessory.DoesNotExist:
        return Response({'error': 'Accessoire non équipé'}, status=status.HTTP_404_NOT_FOUND)
    except Student.DoesNotExist:
        return Response({'error': 'Profil étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)
