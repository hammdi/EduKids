"""
Models pour les évaluations et suivi des progrès - EduKids
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from students.models import Student, Teacher
from exercises.models import Exercise, Question

# Import des modèles d'évaluation vocale
from .voice_models import VoiceAssessment, VoiceAssessmentCriteria


class Assessment(models.Model):
    """
    Évaluations des exercices par les élèves
    """
    STATUS_CHOICES = (
        ('not_started', 'Non commencé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('abandoned', 'Abandonné'),
    )
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name="Élève"
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name="Exercice"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='not_started',
        verbose_name="Statut"
    )
    score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score (%)"
    )
    points_earned = models.IntegerField(
        default=0,
        verbose_name="Points gagnés"
    )
    time_taken = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Temps passé (secondes)"
    )
    attempts = models.IntegerField(
        default=1,
        verbose_name="Nombre de tentatives"
    )
    feedback = models.TextField(blank=True, verbose_name="Feedback automatique")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Commencé le")
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Terminé le"
    )
    
    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student} - {self.exercise.title} ({self.score}%)"
    
    def calculate_score(self):
        """Calcule le score en pourcentage"""
        total_questions = self.responses.count()
        if total_questions == 0:
            return 0
        correct_answers = self.responses.filter(is_correct=True).count()
        return round((correct_answers / total_questions) * 100, 2)


class StudentResponse(models.Model):
    """
    Réponses des élèves aux questions
    """
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name="Évaluation"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='student_responses',
        verbose_name="Question"
    )
    answer_text = models.TextField(verbose_name="Réponse de l'élève")
    selected_answers = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Réponses sélectionnées",
        help_text="IDs des réponses sélectionnées pour les QCM"
    )
    is_correct = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Réponse correcte?"
    )
    points_earned = models.IntegerField(default=0, verbose_name="Points gagnés")
    time_taken = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Temps passé (secondes)"
    )
    feedback = models.TextField(blank=True, verbose_name="Feedback")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="Répondu le")
    
    class Meta:
        verbose_name = "Réponse d'élève"
        verbose_name_plural = "Réponses d'élèves"
        ordering = ['assessment', 'question']
    
    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.question} - {self.assessment.student}"


class Progress(models.Model):
    """
    Suivi des progrès des élèves par matière
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name="Élève"
    )
    subject = models.ForeignKey(
        'exercises.Subject',
        on_delete=models.CASCADE,
        related_name='student_progress',
        verbose_name="Matière"
    )
    skill_level = models.FloatField(
        default=0.0,
        verbose_name="Niveau de compétence (0-100)"
    )
    exercises_completed = models.IntegerField(
        default=0,
        verbose_name="Exercices terminés"
    )
    total_points = models.IntegerField(
        default=0,
        verbose_name="Points totaux"
    )
    average_score = models.FloatField(
        default=0.0,
        verbose_name="Score moyen (%)"
    )
    improvement_rate = models.FloatField(
        default=0.0,
        verbose_name="Taux d'amélioration (%)"
    )
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière activité"
    )
    strengths = models.JSONField(
        default=list,
        verbose_name="Points forts",
        help_text="Liste des thèmes maîtrisés"
    )
    weaknesses = models.JSONField(
        default=list,
        verbose_name="Points à améliorer",
        help_text="Liste des thèmes à travailler"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Progrès"
        verbose_name_plural = "Progrès"
        unique_together = ['student', 'subject']
        ordering = ['student', 'subject']
    
    def __str__(self):
        return f"{self.student} - {self.subject} (Niveau: {self.skill_level})"


class Report(models.Model):
    """
    Rapports générés (élève, classe, matière)
    """
    REPORT_TYPE_CHOICES = (
        ('student', 'Rapport individuel'),
        ('classroom', 'Rapport de classe'),
        ('subject', 'Rapport par matière'),
        ('period', 'Rapport périodique'),
    )
    
    report_type = models.CharField(
        max_length=15,
        choices=REPORT_TYPE_CHOICES,
        verbose_name="Type de rapport"
    )
    title = models.CharField(max_length=200, verbose_name="Titre")
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="Élève"
    )
    classroom = models.ForeignKey(
        'students.Classroom',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="Classe"
    )
    subject = models.ForeignKey(
        'exercises.Subject',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="Matière"
    )
    period_start = models.DateField(verbose_name="Début de période")
    period_end = models.DateField(verbose_name="Fin de période")
    data = models.JSONField(
        default=dict,
        verbose_name="Données du rapport",
        help_text="Statistiques, graphiques, etc."
    )
    summary = models.TextField(verbose_name="Résumé")
    generated_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports',
        verbose_name="Généré par"
    )
    file = models.FileField(
        upload_to='reports/',
        blank=True,
        null=True,
        verbose_name="Fichier PDF"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Rapport"
        verbose_name_plural = "Rapports"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_report_type_display()}"


class Recommendation(models.Model):
    """
    Recommandations personnalisées générées par l'IA
    """
    RECOMMENDATION_TYPE_CHOICES = (
        ('exercise', 'Exercice recommandé'),
        ('topic', 'Thème à réviser'),
        ('learning_strategy', 'Stratégie d\'apprentissage'),
        ('general', 'Recommandation générale'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    )
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name="Élève"
    )
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPE_CHOICES,
        verbose_name="Type de recommandation"
    )
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Priorité"
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recommendations',
        verbose_name="Exercice suggéré"
    )
    topic = models.ForeignKey(
        'exercises.Topic',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recommendations',
        verbose_name="Thème suggéré"
    )
    reason = models.TextField(
        verbose_name="Raison",
        help_text="Pourquoi cette recommandation"
    )
    is_completed = models.BooleanField(default=False, verbose_name="Complétée")
    is_dismissed = models.BooleanField(default=False, verbose_name="Ignorée")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créée le")
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Complétée le"
    )
    
    class Meta:
        verbose_name = "Recommandation"
        verbose_name_plural = "Recommandations"
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.student} - {self.title} ({self.get_priority_display()})"
