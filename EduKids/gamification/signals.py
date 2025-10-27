"""
Signaux pour la gamification - EduKids

Hooks automatiques pour rattacher les profils gamification aux nouveaux utilisateurs.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from students.models import Student
from .models import Avatar


@receiver(post_save, sender=Student)
def create_default_gamification_profile(sender, instance, created, **kwargs):
    """
    Crée automatiquement un profil gamification pour chaque nouvel élève.
    - Crée un avatar personnalisé vide
    - Initialise les statistiques de base
    """
    if created:
        # Créer un avatar personnalisé vide pour le nouvel élève
        Avatar.objects.create(
            student=instance
        )


# Autres signaux peuvent être ajoutés ici pour :
# - Attribution automatique de badges
# - Mise à jour des statistiques
# - Notifications de progression