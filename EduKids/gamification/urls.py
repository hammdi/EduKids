"""
URLs pour la gamification - EduKids

Routes pour l'API REST des missions, badges, avatars et accessoires.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MissionViewSet, UserMissionViewSet, BadgeViewSet, UserBadgeViewSet,
    AvatarViewSet, AccessoryViewSet, UserAccessoryViewSet, avatar_view
)

app_name = 'gamification'

# Router pour l'API REST
router = DefaultRouter()
router.register(r'missions', MissionViewSet, basename='mission')
router.register(r'user-missions', UserMissionViewSet, basename='user-mission')
router.register(r'badges', BadgeViewSet, basename='badge')
router.register(r'user-badges', UserBadgeViewSet, basename='user-badge')
router.register(r'avatars', AvatarViewSet, basename='avatar')
router.register(r'accessories', AccessoryViewSet, basename='accessory')
router.register(r'user-accessories', UserAccessoryViewSet, basename='user-accessory')

urlpatterns = [
    # Template views
    path('avatar/', avatar_view, name='avatar'),
    
    # API REST
    path('api/', include(router.urls)),
]