"""
Models pour les exercices et contenus éducatifs - EduKids
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
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
    order = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
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
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='topics',
        verbose_name="Matière"
    )
    name = models.CharField(max_length=200, verbose_name="Nom du thème")
    description = models.TextField(blank=True, verbose_name="Description")
    grade_level = models.CharField(
        max_length=3,
        choices=[
            ('CP', 'CP'), ('CE1', 'CE1'), ('CE2', 'CE2'),
            ('CM1', 'CM1'), ('CM2', 'CM2')
        ],
        verbose_name="Niveau"
    )
    order = models.IntegerField(default=0, verbose_name="Ordre")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Thème"
        verbose_name_plural = "Thèmes"
        ordering = ['subject', 'grade_level', 'order']
    
    def __str__(self):
        return f"{self.subject.name} - {self.name} ({self.grade_level})"


class Exercise(models.Model):
    """
    Exercices éducatifs
    """
    EXERCISE_TYPE_CHOICES = (
        ('qcm', 'QCM'),
        ('vrai_faux', 'Vrai/Faux'),
        ('text_field', 'Texte à trous'),
        ('dictee', 'Dictée'),
        ('problem', 'Problème mathématique'),
        ('conjugaison', 'Conjugaison'),
        ('calcul', 'Calcul'),
        ('lecture', 'Compréhension de lecture'),
        ('grammaire', 'Grammaire'),
        ('orthographe', 'Orthographe'),
    )
    
    DIFFICULTY_CHOICES = (
        (1, 'Très facile'),
        (2, 'Facile'),
        (3, 'Moyen'),
        (4, 'Difficile'),
        (5, 'Très difficile'),
    )
    
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='exercises',
        verbose_name="Thème"
    )
    exercise_type = models.CharField(
        max_length=20,
        choices=EXERCISE_TYPE_CHOICES,
        verbose_name="Type d'exercice"
    )
    difficulty_level = models.IntegerField(
        choices=DIFFICULTY_CHOICES,
        default=3,
        verbose_name="Niveau de difficulté"
    )
    estimated_time = models.IntegerField(
        default=10,
        verbose_name="Temps estimé (minutes)"
    )
    points = models.IntegerField(default=10, verbose_name="Points")
    instructions = models.TextField(verbose_name="Consignes")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_exercises',
        verbose_name="Créé par"
    )
    is_published = models.BooleanField(default=False, verbose_name="Publié")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Exercice"
        verbose_name_plural = "Exercices"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_exercise_type_display()})"


class Question(models.Model):
    """
    Questions dans les exercices
    """
    QUESTION_TYPE_CHOICES = (
        ('single_choice', 'Choix unique'),
        ('multiple_choice', 'Choix multiple'),
        ('text', 'Texte libre'),
        ('number', 'Nombre'),
        ('true_false', 'Vrai/Faux'),
    )
    
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="Exercice"
    )
    question_text = models.TextField(verbose_name="Question")
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        verbose_name="Type de question"
    )
    points = models.IntegerField(default=1, verbose_name="Points")
    order = models.IntegerField(default=0, verbose_name="Ordre")
    hint = models.TextField(blank=True, verbose_name="Indice")
    explanation = models.TextField(blank=True, verbose_name="Explication")
    image = models.ImageField(
        upload_to='questions/',
        blank=True,
        null=True,
        verbose_name="Image"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['exercise', 'order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class Answer(models.Model):
    """
    Réponses possibles aux questions
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="Question"
    )
    answer_text = models.CharField(max_length=500, verbose_name="Réponse")
    is_correct = models.BooleanField(default=False, verbose_name="Réponse correcte")
    order = models.IntegerField(default=0, verbose_name="Ordre")
    explanation = models.TextField(blank=True, verbose_name="Explication")
    
    class Meta:
        verbose_name = "Réponse"
        verbose_name_plural = "Réponses"
        ordering = ['question', 'order']
    
    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.answer_text[:50]}"


class ContentLibrary(models.Model):
    """
    Bibliothèque de ressources éducatives
    """
    CONTENT_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
        ('pdf', 'PDF'),
        ('text', 'Texte'),
    )
    
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPE_CHOICES,
        verbose_name="Type de contenu"
    )
    file = models.FileField(
        upload_to='library/',
        blank=True,
        null=True,
        verbose_name="Fichier"
    )
    url = models.URLField(blank=True, verbose_name="URL externe")
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='library_items',
        verbose_name="Matière"
    )
    grade_levels = models.JSONField(
        default=list,
        verbose_name="Niveaux concernés",
        help_text="Liste des niveaux: CP, CE1, CE2, CM1, CM2"
    )
    tags = models.JSONField(
        default=list,
        verbose_name="Mots-clés"
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_content',
        verbose_name="Ajouté par"
    )
    is_published = models.BooleanField(default=True, verbose_name="Publié")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Ressource"
        verbose_name_plural = "Bibliothèque de ressources"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"
