from django.apps import AppConfig


class GamificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gamification'

    def ready(self):
        """
        Méthode appelée lors du démarrage de l'application.
        Enregistre les signaux pour les hooks automatiques.
        """
        import gamification.signals  # noqa
