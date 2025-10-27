"""
URLs pour les API du module Gamification
Centralise toutes les routes API pour une meilleure organisation
"""
from django.urls import path
from . import ai_views, api_views

urlpatterns = [
    # === API Accessoires ===
    
    # Lister les accessoires de l'utilisateur
    path('user-accessories/', api_views.list_user_accessories, name='api_list_user_accessories'),
    
    # Acheter un accessoire
    path('buy-accessory/<int:accessory_id>/', api_views.buy_accessory, name='api_buy_accessory'),
    
    # Équiper un accessoire avec IA
    path('ai/equip/<int:accessory_id>/', ai_views.equip_accessory_with_ai, name='api_equip_ai'),
    
    # Déséquiper un accessoire
    path('unequip/<int:accessory_id>/', ai_views.unequip_accessory, name='api_unequip'),
    
    # Restaurer l'avatar original
    path('restore-avatar/', ai_views.restore_original_avatar, name='api_restore_avatar'),
    
    # === API Avatar ===
    
    # Récupérer l'avatar de l'utilisateur
    path('avatar/', api_views.get_user_avatar, name='api_get_avatar'),
    
    # Uploader un avatar
    path('upload-avatar/', api_views.upload_avatar, name='api_upload_avatar'),
    
    # === API Store ===
    
    # Lister les accessoires disponibles dans le store
    path('store/accessories/', api_views.list_store_accessories, name='api_store_accessories'),
]
