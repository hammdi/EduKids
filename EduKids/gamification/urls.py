"""
URLs pour la gamification - EduKids

Routes pour l'API REST des missions, badges, avatars et accessoires.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MissionViewSet, UserMissionViewSet, BadgeViewSet, UserBadgeViewSet,
    AvatarViewSet, AccessoryViewSet, UserAccessoryViewSet
)
from gamification.views import avatar_view

# Router pour l'API REST
router = DefaultRouter()
router.register(r'missions', MissionViewSet)
router.register(r'user-missions', UserMissionViewSet)
router.register(r'badges', BadgeViewSet)
router.register(r'user-badges', UserBadgeViewSet)
router.register(r'avatars', AvatarViewSet)
router.register(r'accessories', AccessoryViewSet)
router.register(r'user-accessories', UserAccessoryViewSet)

urlpatterns = [
    # Template views
    path('avatar/', avatar_view, name='avatar'),

    # API REST
    path('api/', include(router.urls)),
]