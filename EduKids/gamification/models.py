"""
Models pour la gamification - EduKids
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from students.models import Student


class Badge(models.Model):
    """
    Badges à gagner (accomplissements, maîtrise, etc.)
    """
    BADGE_TYPE_CHOICES = (
        ('achievement', 'Accomplissement'),
        ('mastery', 'Maîtrise'),
        ('streak', 'Série'),
        ('special', 'Spécial'),
    )
    
    RARITY_CHOICES = (
        ('common', 'Commun'),
        ('uncommon', 'Peu commun'),
        ('rare', 'Rare'),
        ('epic', 'Épique'),
        ('legendary', 'Légendaire'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Nom du badge")
    description = models.TextField(verbose_name="Description")
    badge_type = models.CharField(
        max_length=15,
        choices=BADGE_TYPE_CHOICES,
        verbose_name="Type de badge"
    )
    rarity = models.CharField(
        max_length=15,
        choices=RARITY_CHOICES,
        default='common',
        verbose_name="Rareté"
    )
    icon = models.CharField(
        max_length=50,
        verbose_name="Icône",
        help_text="Nom de l'icône (ex: fa-trophy)"
    )
    image = models.ImageField(
        upload_to='badges/',
        blank=True,
        null=True,
        verbose_name="Image du badge"
    )
    points_reward = models.IntegerField(
        default=10,
        verbose_name="Points récompense"
    )
    criteria = models.JSONField(
        default=dict,
        verbose_name="Critères d'obtention",
        help_text="Conditions pour obtenir le badge"
    )
    is_secret = models.BooleanField(
        default=False,
        verbose_name="Badge secret",
        help_text="Caché jusqu'à l'obtention"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"
        ordering = ['badge_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"


class StudentBadge(models.Model):
    """
    Badges gagnés par les élèves
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name="Élève"
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='earned_by',
        verbose_name="Badge"
    )
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="Gagné le")
    is_displayed = models.BooleanField(
        default=True,
        verbose_name="Affiché sur le profil"
    )
    
    class Meta:
        verbose_name = "Badge gagné"
        verbose_name_plural = "Badges gagnés"
        unique_together = ['student', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.student} - {self.badge.name}"


class Reward(models.Model):
    """
    Récompenses déblocables (avatars, thèmes, etc.)
    """
    REWARD_TYPE_CHOICES = (
        ('avatar', 'Avatar'),
        ('theme', 'Thème'),
        ('title', 'Titre'),
        ('accessory', 'Accessoire'),
        ('other', 'Autre'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Nom de la récompense")
    description = models.TextField(verbose_name="Description")
    reward_type = models.CharField(
        max_length=15,
        choices=REWARD_TYPE_CHOICES,
        verbose_name="Type de récompense"
    )
    image = models.ImageField(
        upload_to='rewards/',
        blank=True,
        null=True,
        verbose_name="Image"
    )
    cost_points = models.IntegerField(
        default=100,
        verbose_name="Coût en points"
    )
    unlock_criteria = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Critères de déverrouillage",
        help_text="Conditions supplémentaires (niveau, badge, etc.)"
    )
    is_premium = models.BooleanField(default=False, verbose_name="Premium")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créée le")
    
    class Meta:
        verbose_name = "Récompense"
        verbose_name_plural = "Récompenses"
        ordering = ['reward_type', 'cost_points']
    
    def __str__(self):
        return f"{self.name} ({self.cost_points} points)"


class StudentReward(models.Model):
    """
    Récompenses débloquées par les élèves
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='rewards',
        verbose_name="Élève"
    )
    reward = models.ForeignKey(
        Reward,
        on_delete=models.CASCADE,
        related_name='unlocked_by',
        verbose_name="Récompense"
    )
    unlocked_at = models.DateTimeField(auto_now_add=True, verbose_name="Débloquée le")
    is_equipped = models.BooleanField(
        default=False,
        verbose_name="Équipée",
        help_text="Actuellement utilisée par l'élève"
    )
    
    class Meta:
        verbose_name = "Récompense débloquée"
        verbose_name_plural = "Récompenses débloquées"
        unique_together = ['student', 'reward']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.student} - {self.reward.name}"


class Challenge(models.Model):
    """
    Défis quotidiens/hebdomadaires
    """
    CHALLENGE_TYPE_CHOICES = (
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('special', 'Spécial'),
    )
    
    DIFFICULTY_CHOICES = (
        ('easy', 'Facile'),
        ('medium', 'Moyen'),
        ('hard', 'Difficile'),
    )
    
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    challenge_type = models.CharField(
        max_length=10,
        choices=CHALLENGE_TYPE_CHOICES,
        verbose_name="Type de défi"
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        verbose_name="Difficulté"
    )
    subject = models.ForeignKey(
        'exercises.Subject',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='challenges',
        verbose_name="Matière"
    )
    objective = models.JSONField(
        default=dict,
        verbose_name="Objectif",
        help_text="Critères de complétion (ex: 10 exercices, 90% de réussite)"
    )
    points_reward = models.IntegerField(
        default=50,
        verbose_name="Points récompense"
    )
    badge_reward = models.ForeignKey(
        Badge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='challenge_rewards',
        verbose_name="Badge récompense"
    )
    start_date = models.DateTimeField(verbose_name="Date de début")
    end_date = models.DateTimeField(verbose_name="Date de fin")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Défi"
        verbose_name_plural = "Défis"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} ({self.get_challenge_type_display()})"


class StudentChallenge(models.Model):
    """
    Participation des élèves aux défis
    """
    STATUS_CHOICES = (
        ('not_started', 'Non commencé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    )
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='challenges',
        verbose_name="Élève"
    )
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name="Défi"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='not_started',
        verbose_name="Statut"
    )
    progress = models.FloatField(
        default=0.0,
        verbose_name="Progression (%)"
    )
    progress_data = models.JSONField(
        default=dict,
        verbose_name="Données de progression",
        help_text="Détails de l'avancement"
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Commencé le")
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Terminé le"
    )
    
    class Meta:
        verbose_name = "Participation défi"
        verbose_name_plural = "Participations défis"
        unique_together = ['student', 'challenge']
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student} - {self.challenge.title} ({self.progress}%)"


class Leaderboard(models.Model):
    """
    Classements (hebdomadaire, mensuel, par matière)
    """
    LEADERBOARD_TYPE_CHOICES = (
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('all_time', 'Tous temps'),
        ('subject', 'Par matière'),
        ('classroom', 'Par classe'),
    )
    
    name = models.CharField(max_length=200, verbose_name="Nom du classement")
    leaderboard_type = models.CharField(
        max_length=15,
        choices=LEADERBOARD_TYPE_CHOICES,
        verbose_name="Type de classement"
    )
    subject = models.ForeignKey(
        'exercises.Subject',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaderboards',
        verbose_name="Matière"
    )
    classroom = models.ForeignKey(
        'students.Classroom',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaderboards',
        verbose_name="Classe"
    )
    period_start = models.DateTimeField(verbose_name="Début de période")
    period_end = models.DateTimeField(verbose_name="Fin de période")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Classement"
        verbose_name_plural = "Classements"
        ordering = ['-period_start']
    
    def __str__(self):
        return f"{self.name} ({self.get_leaderboard_type_display()})"


class LeaderboardEntry(models.Model):
    """
    Entrées dans les classements
    """
    leaderboard = models.ForeignKey(
        Leaderboard,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name="Classement"
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        verbose_name="Élève"
    )
    rank = models.IntegerField(verbose_name="Rang")
    score = models.IntegerField(verbose_name="Score")
    exercises_completed = models.IntegerField(
        default=0,
        verbose_name="Exercices complétés"
    )
    average_score = models.FloatField(
        default=0.0,
        verbose_name="Score moyen (%)"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    class Meta:
        verbose_name = "Entrée classement"
        verbose_name_plural = "Entrées classement"
        unique_together = ['leaderboard', 'student']
        ordering = ['leaderboard', 'rank']
    
    def __str__(self):
        return f"#{self.rank} - {self.student} ({self.score} points)"


class Notification(models.Model):
    """
    Notifications de progression
    """
    NOTIFICATION_TYPE_CHOICES = (
        ('badge', 'Nouveau badge'),
        ('reward', 'Nouvelle récompense'),
        ('challenge', 'Nouveau défi'),
        ('level_up', 'Niveau supérieur'),
        ('achievement', 'Accomplissement'),
        ('reminder', 'Rappel'),
        ('general', 'Général'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Basse'),
        ('normal', 'Normale'),
        ('high', 'Haute'),
    )
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Élève"
    )
    notification_type = models.CharField(
        max_length=15,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name="Type"
    )
    title = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name="Priorité"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Icône"
    )
    link_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Lien",
        help_text="URL de redirection"
    )
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Envoyée le")
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Lue le"
    )
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-sent_at']
    
    def __str__(self):
        status = "✓" if self.is_read else "●"
        return f"{status} {self.student} - {self.title}"
