"""
Models pour la gamification - EduKids

Phase 3 : Avatars & Personnalisation avancée

Diagramme des relations (ASCII UML) :

    +-----------+     +-----------+
    |   Student |     |   Avatar  |
    +-----------+     +-----------+
    |           |1---1| student   |
    |           |     | image     |
    |           |     | level     |
    |           |     | accessories|
    +-----------+     +-----------+
          |1
          |
          |*
    +-----------+     +-----------+
    | Accessory |     |UserAccessory|
    +-----------+     +-----------+
    | name      |1---*| student   |
    | image     |     | accessory |
    | type      |     | status    |
    | points_req|     | date_obt  |
    +-----------+     +-----------+

Relations :
- Student --1--> Avatar (avatar personnalisé)
- Student --*--> UserAccessory (accessoires possédés)
- Accessory --*--> UserAccessory
- Avatar --*--> Accessory (accessoires équipés)
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from students.models import Student


class Badge(models.Model):
    """
    Badges à gagner (accomplissements, maîtrise, etc.)
    """
    nom = models.CharField(max_length=100, verbose_name="Nom du badge")
    description = models.TextField(verbose_name="Description")
    icon = models.CharField(
        max_length=50,
        verbose_name="Icône",
        help_text="Nom de l'icône (ex: fa-trophy)"
    )
    condition = models.TextField(
        default="Condition à définir",
        verbose_name="Condition d'attribution",
        help_text="Règle textuelle pour gagner le badge (ex: 'Terminer 3 missions de lecture')"
    )
    points_bonus = models.IntegerField(
        default=10,
        verbose_name="Points bonus"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom}"


class UserBadge(models.Model):
    """
    Badges gagnés par les élèves
    """
    user = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name="Utilisateur"
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='gagnes_par',
        verbose_name="Badge"
    )
    date_obtention = models.DateTimeField(auto_now_add=True, verbose_name="Date d'obtention")
    
    class Meta:
        verbose_name = "Badge utilisateur"
        verbose_name_plural = "Badges utilisateurs"
        unique_together = ['user', 'badge']
        ordering = ['-date_obtention']
    
    def __str__(self):
        return f"{self.user} - {self.badge.nom}"


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


class Avatar(models.Model):
    """
    Avatar personnalisé de l'élève avec upload d'image
    """
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name='avatar',
        verbose_name="Élève"
    )
    name = models.CharField(
        max_length=100,
        default="Mon Avatar",
        verbose_name="Nom de l'avatar"
    )
    image = models.ImageField(
        upload_to='avatars/custom/',
        blank=True,
        null=True,
        verbose_name="Image d'avatar"
    )
    level = models.IntegerField(
        default=1,
        verbose_name="Niveau de l'élève"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    accessories = models.ManyToManyField(
        'Accessory',
        blank=True,
        related_name='equipped_on',
        verbose_name="Accessoires équipés"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")

    class Meta:
        verbose_name = "Avatar"
        verbose_name_plural = "Avatars"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Avatar de {self.student.user.get_full_name()}"

    def get_equipped_accessories_by_type(self):
        """
        Retourne les accessoires équipés groupés par type
        """
        equipped = {}
        for accessory in self.accessories.all():
            equipped[accessory.accessory_type] = accessory
        return equipped

    def can_equip_accessory(self, accessory):
        """
        Vérifie si l'élève peut équiper cet accessoire
        """
        return UserAccessory.objects.filter(
            student=self.student,
            accessory=accessory,
            status='owned'
        ).exists()


class Accessory(models.Model):
    """
    Accessoires disponibles dans la boutique
    """
    ACCESSORY_TYPE_CHOICES = (
        ('hat', 'Chapeau'),
        ('glasses', 'Lunettes'),
        ('outfit', 'Tenue'),
        ('background', 'Fond'),
        ('pet', 'Animal de compagnie'),
        ('other', 'Autre'),
    )

    name = models.CharField(max_length=100, verbose_name="Nom")
    image = models.ImageField(
        upload_to='accessories/',
        verbose_name="Image"
    )
    accessory_type = models.CharField(
        max_length=20,
        choices=ACCESSORY_TYPE_CHOICES,
        default='other',
        verbose_name="Type d'accessoire"
    )
    points_required = models.IntegerField(
        default=50,
        verbose_name="Points requis"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Disponible"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")

    class Meta:
        verbose_name = "Accessoire"
        verbose_name_plural = "Accessoires"
        ordering = ['accessory_type', 'points_required']

    def __str__(self):
        return f"{self.name} ({self.get_accessory_type_display()})"


class UserAccessory(models.Model):
    """
    Accessoires possédés par les élèves
    """
    STATUS_CHOICES = (
        ('unlocked', 'Débloqué'),
        ('owned', 'Possédé'),
        ('equipped', 'Équipé'),
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='user_accessories',
        verbose_name="Élève"
    )
    accessory = models.ForeignKey(
        Accessory,
        on_delete=models.CASCADE,
        related_name='user_ownerships',
        verbose_name="Accessoire"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='unlocked',
        verbose_name="Statut"
    )
    date_obtained = models.DateTimeField(default=timezone.now, verbose_name="Date d'obtention")

    class Meta:
        verbose_name = "Accessoire utilisateur"
        verbose_name_plural = "Accessoires utilisateurs"
        unique_together = ['student', 'accessory']
        ordering = ['-date_obtained']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.accessory.name} ({self.get_status_display()})"

    def purchase(self):
        """
        Acheter l'accessoire si l'élève a assez de points
        """
        if self.student.total_points >= self.accessory.points_required:
            self.student.total_points -= self.accessory.points_required
            self.student.save()
            self.status = 'owned'
            self.date_obtained = timezone.now()
            self.save()
            return True
        return False

    def equip(self, avatar):
        """
        Équiper l'accessoire sur l'avatar
        """
        if self.status == 'owned':
            # Déséquiper les autres accessoires du même type
            same_type_accessories = UserAccessory.objects.filter(
                student=self.student,
                accessory__accessory_type=self.accessory.accessory_type,
                status='equipped'
            )
            for ua in same_type_accessories:
                ua.unequip(avatar)

            # Équiper le nouvel accessoire
            self.status = 'equipped'
            self.save()
            avatar.accessories.add(self.accessory)
            avatar.save()
            return True
        return False

    def unequip(self, avatar):
        """
        Déséquiper l'accessoire de l'avatar
        """
        if self.status == 'equipped':
            self.status = 'owned'
            self.save()
            avatar.accessories.remove(self.accessory)
            avatar.save()
            return True
        return False


class Mission(models.Model):
    """
    Missions intelligentes pour les élèves
    """
    MISSION_TYPE_CHOICES = (
        ('lecture', 'Lecture'),
        ('math', 'Mathématiques'),
        ('science', 'Sciences'),
        ('histoire', 'Histoire'),
        ('geographie', 'Géographie'),
        ('langue', 'Langue'),
        ('creativite', 'Créativité'),
        ('general', 'Général'),
    )

    titre = models.CharField(max_length=200, verbose_name="Titre de la mission")
    description = models.TextField(verbose_name="Description détaillée")
    type_mission = models.CharField(
        max_length=15,
        choices=MISSION_TYPE_CHOICES,
        default='general',
        verbose_name="Type de mission"
    )
    objectif = models.IntegerField(
        default=1,
        verbose_name="Objectif (nombre de tâches)",
        help_text="Nombre d'actions à accomplir pour terminer la mission"
    )
    points = models.IntegerField(
        default=50,
        verbose_name="Points récompense"
    )
    date_expiration = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'expiration"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        verbose_name = "Mission"
        verbose_name_plural = "Missions"
        ordering = ['type_mission', '-created_at']

    def __str__(self):
        return f"{self.titre} ({self.get_type_mission_display()})"


class UserMission(models.Model):
    """
    Participation des utilisateurs aux missions
    """
    STATUS_CHOICES = (
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    )

    user = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='missions',
        verbose_name="Utilisateur"
    )
    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name="Mission"
    )
    progression = models.IntegerField(
        default=0,
        verbose_name="Progression actuelle",
        help_text="Nombre d'actions accomplies"
    )
    statut = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='en_cours',
        verbose_name="Statut"
    )
    date_attribuee = models.DateTimeField(auto_now_add=True, verbose_name="Date attribuée")
    date_terminee = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date terminée"
    )

    class Meta:
        verbose_name = "Mission utilisateur"
        verbose_name_plural = "Missions utilisateurs"
        unique_together = ['user', 'mission']
        ordering = ['-date_attribuee']

    def __str__(self):
        return f"{self.user} - {self.mission.titre} ({self.progression}/{self.mission.objectif})"
