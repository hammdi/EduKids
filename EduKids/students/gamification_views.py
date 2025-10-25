"""
Vues Gamification pour l'espace Student - EduKids

Toutes les vues sont protégées par @student_required
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .decorators import student_required
from gamification.models import Avatar, Accessory, UserAccessory, Badge, UserBadge, Mission, UserMission


@student_required
def student_dashboard(request):
    """
    Dashboard principal de l'espace Student avec stats gamification
    """
    student = request.user.student_profile
    
    # Récupérer ou créer l'avatar
    avatar, created = Avatar.objects.get_or_create(
        student=student,
        defaults={'level': 1}
    )
    
    # Statistiques gamification
    total_points = student.total_points
    
    # Badges obtenus
    user_badges = UserBadge.objects.filter(
        user=request.user,
        date_obtained__isnull=False
    ).select_related('badge').order_by('-date_obtained')[:5]
    
    total_badges = user_badges.count()
    
    # Missions
    active_missions = UserMission.objects.filter(
        user=request.user,
        statut='en_cours'
    ).select_related('mission')[:3]
    
    completed_missions = UserMission.objects.filter(
        user=request.user,
        statut='termine'
    ).count()
    
    # Accessoires équipés
    equipped_accessories = UserAccessory.objects.filter(
        student=student,
        status='equipped'
    ).select_related('accessory')
    
    # Progression niveau
    current_level = avatar.level
    next_level_points = current_level * 100  # 100 points par niveau
    progress_percentage = min((total_points % next_level_points) / next_level_points * 100, 100)
    
    context = {
        'student': student,
        'avatar': avatar,
        'total_points': total_points,
        'total_badges': total_badges,
        'user_badges': user_badges,
        'active_missions': active_missions,
        'completed_missions': completed_missions,
        'equipped_accessories': equipped_accessories,
        'current_level': current_level,
        'next_level_points': next_level_points,
        'progress_percentage': progress_percentage,
    }
    
    return render(request, 'students/gamification/dashboard.html', context)


@student_required
def student_customize(request):
    """
    Page de personnalisation de l'avatar
    Upload d'image + équipement des accessoires
    """
    student = request.user.student_profile
    
    # Récupérer ou créer l'avatar
    avatar, created = Avatar.objects.get_or_create(
        student=student,
        defaults={'level': 1}
    )
    
    # Accessoires possédés par l'étudiant
    owned_accessories = UserAccessory.objects.filter(
        student=student,
        status__in=['owned', 'equipped']
    ).select_related('accessory')
    
    # Grouper par type
    accessories_by_type = {}
    for ua in owned_accessories:
        acc_type = ua.accessory.accessory_type
        if acc_type not in accessories_by_type:
            accessories_by_type[acc_type] = []
        accessories_by_type[acc_type].append({
            'user_accessory': ua,
            'accessory': ua.accessory,
            'is_equipped': ua.status == 'equipped'
        })
    
    context = {
        'student': student,
        'avatar': avatar,
        'accessories_by_type': accessories_by_type,
        'total_points': student.total_points,
    }
    
    return render(request, 'students/gamification/customize.html', context)


@student_required
def student_store(request):
    """
    Boutique d'accessoires
    Affichage des accessoires disponibles + achat
    """
    student = request.user.student_profile
    
    # Tous les accessoires actifs
    all_accessories = Accessory.objects.filter(is_active=True).order_by('points_required')
    
    # Accessoires déjà possédés
    owned_accessory_ids = UserAccessory.objects.filter(
        student=student,
        status__in=['owned', 'equipped']
    ).values_list('accessory_id', flat=True)
    
    # Enrichir les accessoires avec les infos de possession
    accessories_data = []
    for accessory in all_accessories:
        is_owned = accessory.id in owned_accessory_ids
        can_afford = student.total_points >= accessory.points_required
        
        accessories_data.append({
            'accessory': accessory,
            'is_owned': is_owned,
            'can_afford': can_afford,
            'points_needed': max(0, accessory.points_required - student.total_points) if not can_afford else 0
        })
    
    context = {
        'student': student,
        'accessories_data': accessories_data,
        'total_points': student.total_points,
    }
    
    return render(request, 'students/gamification/store.html', context)


@student_required
def student_profile_gamification(request):
    """
    Profil gamification de l'étudiant
    Vue d'ensemble des achievements
    """
    student = request.user.student_profile
    
    # Avatar
    avatar = Avatar.objects.filter(student=student).first()
    
    # Tous les badges
    all_badges = UserBadge.objects.filter(
        user=request.user
    ).select_related('badge').order_by('-date_obtained')
    
    # Toutes les missions
    all_missions = UserMission.objects.filter(
        user=request.user
    ).select_related('mission').order_by('-date_terminee')
    
    # Stats
    total_accessories = UserAccessory.objects.filter(
        student=student,
        status__in=['owned', 'equipped']
    ).count()
    
    context = {
        'student': student,
        'avatar': avatar,
        'all_badges': all_badges,
        'all_missions': all_missions,
        'total_accessories': total_accessories,
    }
    
    return render(request, 'students/gamification/profile.html', context)


@student_required
def student_badges(request):
    """
    Page des badges avec animations
    """
    student = request.user.student_profile
    
    context = {
        'student': student,
    }
    
    return render(request, 'students/gamification/badges.html', context)


@student_required
def student_store_improved(request):
    """
    Boutique améliorée avec séparation débloqués/à acheter
    """
    student = request.user.student_profile
    
    context = {
        'student': student,
    }
    
    return render(request, 'students/gamification/store_improved.html', context)


@student_required
def student_inventory(request):
    """
    Page Mes Trésors - Inventaire motivant
    """
    student = request.user.student_profile
    
    context = {
        'student': student,
    }
    
    return render(request, 'students/gamification/inventory.html', context)
