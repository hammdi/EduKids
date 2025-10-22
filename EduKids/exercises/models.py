"""
Models pour les exercices et contenus éducatifs - EduKids
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from students.models import User


class Subject(models.Model):
    """
    Matières scolaires (Français, Mathématiques, etc.)
    """
    name = models.CharField(max_length=100, verbose_name="Nom de la matière")
    description = models.TextField(blank=True, verbose_name="Description")
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Icône",
        help_text="Nom de l'icône (ex: fa-book)"
    )
    color = models.CharField(
        max_length=7,
        default='#3498db',
        verbose_name="Couleur",
        help_text="Code couleur hex (ex: #3498db)"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    image = models.ImageField(upload_to='subjects/', blank=True, null=True, verbose_name="Image")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_by = models.ForeignKey('students.User', on_delete=models.CASCADE, related_name='created_subjects')
    grade_level = models.CharField(
        max_length=10,
        choices=[
            ('CP', 'CP'),
            ('CE1', 'CE1'),
            ('CE2', 'CE2'),
            ('CM1', 'CM1'),
            ('CM2', 'CM2'),
        ],
        default='CP',
        help_text="Niveau scolaire pour cette matière/classe"
    )
    updated_at = models.DateTimeField(auto_now=True, help_text="Last updated when content added")

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Topic(models.Model):
    """
    Thèmes/Chapitres par matière
    """
    GRADE_LEVEL_CHOICES = [
        ('CP', 'CP'),
        ('CE1', 'CE1'),
        ('CE2', 'CE2'),
        ('CM1', 'CM1'),
        ('CM2', 'CM2'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics', verbose_name="Matière")
    name = models.CharField(max_length=200, verbose_name="Nom du thème")
    description = models.TextField(blank=True, verbose_name="Description")
    grade_level = models.CharField(max_length=3, choices=GRADE_LEVEL_CHOICES, verbose_name="Niveau scolaire")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last updated when content added")

    class Meta:
        verbose_name = "Thème"
        verbose_name_plural = "Thèmes"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.subject.name} - {self.name}"


class Exercise(models.Model):
    """
    Exercices éducatifs
    """
    EXERCISE_TYPE_CHOICES = [
        ('QCM', 'QCM'),
        ('dictée', 'Dictée'),
        ('texte_à_trous', 'Texte à trous'),  # Changed from 'trous' to 'texte_à_trous'
        ('math', 'Problème mathématique'),
    ]
    DIFFICULTY_CHOICES = [
        ('facile', 'Facile'),
        ('moyen', 'Moyen'),
        ('difficile', 'Difficile'),
    ]
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='exercises', verbose_name="Thème")
    name = models.CharField(max_length=200, verbose_name="Nom de l'exercice")
    description = models.TextField(blank=True, verbose_name="Description")
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPE_CHOICES, verbose_name="Type d'exercice")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, verbose_name="Difficulté")
    time_limit = models.PositiveIntegerField(blank=True, null=True, verbose_name="Temps limite (minutes)")
    points = models.PositiveIntegerField(default=10, verbose_name="Points")
    instructions = models.TextField(blank=True, verbose_name="Instructions")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créateur")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    available_from = models.DateTimeField(null=True, blank=True, help_text="When this exercise becomes available as an assignment (optional)")
    due_date = models.DateTimeField(null=True, blank=True, help_text="Due date for this assignment (optional)")

    class Meta:
        verbose_name = "Exercice"
        verbose_name_plural = "Exercices"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Question(models.Model):
    """
    Questions dans les exercices
    """
    QUESTION_TYPE_CHOICES = [
        ('text', 'Texte'),
        ('image', 'Image'),
        ('audio', 'Audio'),
    ]
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='questions', verbose_name="Exercice")
    question_text = models.TextField(verbose_name="Texte de la question")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES, default='text', verbose_name="Type de question")
    points = models.PositiveIntegerField(default=1, verbose_name="Points")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    hint = models.TextField(blank=True, verbose_name="Indice")
    image = models.ImageField(upload_to='questions/', blank=True, null=True, verbose_name="Image")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['order']

    def __str__(self):
        return f"Question {self.order} - {self.exercise.name}"


class Answer(models.Model):
    """
    Réponses possibles aux questions
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name="Question")
    answer_text = models.TextField(verbose_name="Texte de la réponse")
    is_correct = models.BooleanField(default=False, verbose_name="Réponse correcte")
    explanation = models.TextField(blank=True, verbose_name="Explication")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta:
        verbose_name = "Réponse"
        verbose_name_plural = "Réponses"
        ordering = ['order']

    def __str__(self):
        return f"Answer {self.order} - {self.question}"


class ContentLibrary(models.Model):
    """
    Bibliothèque de ressources éducatives
    """
    CONTENT_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='content_library', verbose_name="Matière")
    title = models.CharField(max_length=200, verbose_name="Titre")
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES, verbose_name="Type de contenu")
    file = models.FileField(upload_to='content/', blank=True, null=True, verbose_name="Fichier")  # Added blank=True, null=True
    tags = models.JSONField(default=list, verbose_name="Tags")
    grade_levels = models.JSONField(default=list, verbose_name="Niveaux scolaires")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Bibliothèque de contenu"
        verbose_name_plural = "Bibliothèques de contenu"

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """
    Leçons pédagogiques sous les thèmes
    """
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='lessons', verbose_name="Thème")
    title = models.CharField(max_length=200, verbose_name="Titre de la leçon")
    content = models.TextField(verbose_name="Contenu de la leçon")
    media = models.FileField(upload_to='lessons/', blank=True, null=True, verbose_name="Média (image/vidéo)")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Leçon"
        verbose_name_plural = "Leçons"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.topic.name} - {self.title}"


class ExerciseResult(models.Model):
    """
    Results of student exercise attempts
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_results')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='results')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(default=timezone.now)
    score = models.FloatField()  # Percentage score
    total_points = models.IntegerField()
    earned_points = models.IntegerField()
    attempt_number = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['-completed_at']
        verbose_name = "Résultat d'exercice"
        verbose_name_plural = "Résultats d'exercices"
    
    def __str__(self):
        return f"{self.student.username} - {self.exercise.name} - {self.score}%"


class StudentAnswer(models.Model):
    """
    Individual question answers within an exercise result
    """
    exercise_result = models.ForeignKey(ExerciseResult, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    student_answer = models.TextField()
    is_correct = models.BooleanField()
    points_earned = models.IntegerField()
    
    class Meta:
        verbose_name = "Réponse d'étudiant"
        verbose_name_plural = "Réponses d'étudiants"
    
    def __str__(self):
        return f"{self.exercise_result.student.username} - Q{self.question.pk}"


class SubjectMembership(models.Model):
    """
    Suivi des inscriptions des étudiants aux matières
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='memberships')
    student = models.ForeignKey('students.User', on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('subject', 'student')
        verbose_name = "Adhésion à une matière"
        verbose_name_plural = "Adhésions aux matières"

    def __str__(self):
        return f"{self.student.username} - {self.subject.name}"


class StudentSubjectView(models.Model):
    """
    Track last viewed subjects for students
    """
    student = models.ForeignKey('students.User', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    last_viewed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'subject')


class StudentTopicView(models.Model):
    """
    Track last viewed topics for students
    """
    student = models.ForeignKey('students.User', on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    last_viewed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'topic')
