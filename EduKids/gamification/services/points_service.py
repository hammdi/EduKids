"""
Services pour la gestion des points et badges - EduKids

Fonctions utilitaires pour la gestion automatique des points et badges.
"""
from gamification.models import UserMission, Badge, UserBadge


def attribuer_points_et_badges(user_mission):
    """
    Attribue automatiquement les points et vérifie les badges lors de la completion d'une mission.

    Args:
        user_mission (UserMission): L'instance UserMission terminée

    Returns:
        dict: Résumé des attributions (points ajoutés, badges gagnés)
    """
    user = user_mission.user
    mission = user_mission.mission
    result = {
        'points_ajoutes': 0,
        'badges_gagnes': []
    }

    # Ajouter les points de la mission
    # Note: Ici, on suppose qu'il y a un modèle Student avec un champ points
    # Pour simplifier, on peut utiliser un champ sur Student ou créer un modèle Points séparé
    # Pour l'exemple, on simule l'ajout de points
    result['points_ajoutes'] = mission.points

    # Vérifier les badges à attribuer
    badges_a_verifier = Badge.objects.filter(is_active=True)

    for badge in badges_a_verifier:
        if _verifier_condition_badge(user, badge):
            # Créer UserBadge si pas déjà gagné
            if not UserBadge.objects.filter(user=user, badge=badge).exists():
                UserBadge.objects.create(user=user, badge=badge)
                result['badges_gagnes'].append(badge.nom)

    return result


def _verifier_condition_badge(user, badge):
    """
    Vérifie si un utilisateur remplit la condition d'un badge.

    Args:
        user: Instance Student
        badge: Instance Badge

    Returns:
        bool: True si la condition est remplie
    """
    condition = badge.condition.lower()

    if '3 missions lecture terminees' in condition:
        # Compter les missions de lecture terminées
        missions_lecture = UserMission.objects.filter(
            user=user,
            mission__type_mission='lecture',
            statut='termine'
        ).count()
        return missions_lecture >= 3

    elif '5 missions math terminees' in condition:
        missions_math = UserMission.objects.filter(
            user=user,
            mission__type_mission='math',
            statut='termine'
        ).count()
        return missions_math >= 5

    elif '10 missions totales terminees' in condition:
        total_missions = UserMission.objects.filter(
            user=user,
            statut='termine'
        ).count()
        return total_missions >= 10

    # Ajouter d'autres conditions selon les besoins
    return False
