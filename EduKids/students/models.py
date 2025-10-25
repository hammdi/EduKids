"""
Models pour la gestion des utilisateurs (élèves, enseignants, parents) - EduKids
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour EduKids
    """
    USER_TYPE_CHOICES = (
        ('student', 'Élève'),
        ('teacher', 'Enseignant'),
        ('parent', 'Parent'),
        ('admin', 'Administrateur'),
    )
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='student',
        verbose_name="Type d'utilisateur"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Téléphone"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Avatar"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"


class Student(models.Model):
    """
    Modèle pour les élèves du primaire (6-12 ans)
    """
    GRADE_LEVEL_CHOICES = (
        ('CP', 'CP (6-7 ans)'),
        ('CE1', 'CE1 (7-8 ans)'),
        ('CE2', 'CE2 (8-9 ans)'),
        ('CM1', 'CM1 (9-10 ans)'),
        ('CM2', 'CM2 (10-11 ans)'),
    )
    
    LEARNING_STYLE_CHOICES = (
        ('visual', 'Visuel'),
        ('auditory', 'Auditif'),
        ('kinesthetic', 'Kinesthésique'),
        ('reading', 'Lecture/Écriture'),
    )
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name="Utilisateur"
    )
    grade_level = models.CharField(
        max_length=3,
        choices=GRADE_LEVEL_CHOICES,
        verbose_name="Niveau scolaire"
    )
    birth_date = models.DateField(
        verbose_name="Date de naissance",
        null=True,
        blank=True
    )
    learning_style = models.CharField(
        max_length=15,
        choices=LEARNING_STYLE_CHOICES,
        default='visual',
        verbose_name="Style d'apprentissage"
    )
    preferred_language = models.CharField(
        max_length=10,
        default='fr',
        verbose_name="Langue préférée"
    )
    progress_score = models.FloatField(
        default=0.0,
        verbose_name="Score de progression global"
    )
    total_points = models.IntegerField(
        default=0,
        verbose_name="Points totaux"
    )
    current_level = models.IntegerField(
        default=1,
        verbose_name="Niveau actuel"
    )
    last_daily_reward = models.DateField(
        null=True,
        blank=True,
        verbose_name="Dernière récompense quotidienne"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière activité")
    
    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ['grade_level', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_grade_level_display()}"
    
    def get_age(self):
        """Calcule l'âge de l'élève"""
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


class Teacher(models.Model):
    """
    Modèle pour les enseignants du primaire
    """
    CERTIFICATION_LEVEL_CHOICES = (
        ('bachelor', 'Licence'),
        ('master', 'Master'),
        ('phd', 'Doctorat'),
        ('certified', 'Certifié'),
        ('other', 'Autre'),
    )
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        verbose_name="Utilisateur"
    )
    subject_specialties = models.JSONField(
        default=list,
        verbose_name="Matières enseignées",
        help_text="Liste des matières: Français, Mathématiques, Sciences, etc."
    )
    teaching_experience = models.IntegerField(
        default=0,
        verbose_name="Années d'expérience"
    )
    certification_level = models.CharField(
        max_length=100,
        choices=CERTIFICATION_LEVEL_CHOICES,
        default='bachelor',
        blank=True,
        verbose_name="Niveau de certification"
    )
    classes = models.ManyToManyField(
        'Classroom',
        related_name='teachers',
        blank=True,
        verbose_name="Classes"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"
    
    def __str__(self):
        return f"Prof. {self.user.get_full_name()}"


class Parent(models.Model):
    """
    Modèle pour les parents d'élèves
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        verbose_name="Utilisateur"
    )
    children = models.ManyToManyField(
        Student,
        related_name='parents',
        verbose_name="Enfants"
    )
    notification_preferences = models.JSONField(
        default=dict,
        verbose_name="Préférences de notification",
        help_text="Email, SMS, Push, etc."
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"
    
    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"


class Classroom(models.Model):
    """
    Modèle pour les classes
    """
    name = models.CharField(max_length=100, verbose_name="Nom de la classe")
    grade_level = models.CharField(
        max_length=3,
        choices=Student.GRADE_LEVEL_CHOICES,
        verbose_name="Niveau"
    )
    school_year = models.CharField(
        max_length=9,
        verbose_name="Année scolaire",
        help_text="Ex: 2024-2025"
    )
    students = models.ManyToManyField(
        Student,
        related_name='classrooms',
        blank=True,
        verbose_name="Élèves"
    )
    max_students = models.IntegerField(
        default=30,
        verbose_name="Nombre maximum d'élèves"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ['school_year', 'grade_level', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.get_grade_level_display()} ({self.school_year})"
    
    def get_student_count(self):
        """Retourne le nombre d'élèves dans la classe"""
        return self.students.count()