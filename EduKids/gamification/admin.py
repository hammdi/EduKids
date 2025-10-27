from django.contrib import admin
from .models import (
    Badge, UserBadge, Mission, UserMission,
    Avatar, Accessory, UserAccessory
)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    """
    Administration des badges
    """
    list_display = ['nom', 'icon', 'created_at']
    list_filter = ['created_at']
    search_fields = ['nom', 'description']
    readonly_fields = ['created_at']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    """
    Administration des badges utilisateur
    """
    list_display = ['user', 'badge', 'date_obtention']
    list_filter = ['date_obtention', 'badge']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'badge__nom']
    readonly_fields = ['date_obtention']


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    """
    Administration des missions
    """
    list_display = ['titre', 'type_mission', 'objectif', 'points', 'actif']
    list_filter = ['type_mission', 'actif', 'created_at']
    search_fields = ['titre', 'description']
    list_editable = ['actif']
    readonly_fields = ['created_at']


@admin.register(UserMission)
class UserMissionAdmin(admin.ModelAdmin):
    """
    Administration des missions utilisateur
    """
    list_display = ['user', 'mission', 'statut', 'progression', 'date_attribuee']
    list_filter = ['statut', 'date_attribuee', 'mission']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'mission__titre']
    readonly_fields = ['date_attribuee', 'date_terminee']


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    """
    Administration des avatars
    """
    list_display = ['student', 'level', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['student__user__username', 'student__user__first_name', 'student__user__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    """
    Administration des accessoires
    """
    list_display = ['name', 'accessory_type', 'points_required', 'is_active']
    list_filter = ['accessory_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at']


@admin.register(UserAccessory)
class UserAccessoryAdmin(admin.ModelAdmin):
    """
    Administration des accessoires utilisateur
    """
    list_display = ['student', 'accessory', 'status', 'date_obtained']
    list_filter = ['status', 'date_obtained', 'accessory__accessory_type']
    search_fields = ['student__user__username', 'student__user__first_name', 'student__user__last_name', 'accessory__name']
    list_editable = ['status']
    readonly_fields = ['date_obtained']
