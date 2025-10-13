"""
Modèles pour l'évaluation vocale par IA - EduKids
Système d'évaluation innovant basé sur l'analyse de la voix des élèves
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from students.models import Student, Teacher
from exercises.models import Exercise


class VoiceAssessment(models.Model):
    """
    Évaluation vocale d'un élève avec analyse IA complète
    """
    STATUS_CHOICES = (
        ('pending', 'En attente de traitement'),
        ('processing', 'En cours d\'analyse'),
        ('completed', 'Terminé'),
        ('failed', 'Échec'),
    )
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='voice_assessments',
        verbose_name="Élève"
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='voice_assessments',
        verbose_name="Exercice associé"
    )
    prompt = models.TextField(
        verbose_name="Question/Sujet",
        help_text="Question posée à l'élève ou sujet de réflexion"
    )
    audio_file = models.FileField(
        upload_to='voice_assessments/%Y/%m/%d/',
        verbose_name="Fichier audio"
    )
    duration = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Durée (secondes)"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    
    # Transcription
    transcription = models.TextField(
        blank=True,
        verbose_name="Transcription du discours",
        help_text="Texte converti depuis l'audio"
    )
    
    # === SCORES PRINCIPAUX (0-100) ===
    
    # 1. Originalité de l'idée
    originality_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score d'originalité",
        help_text="Créativité et innovation de la réponse (0-100)"
    )
    
    # 2. Communication Verbale
    verbal_structure_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score de structure",
        help_text="Organisation et cohérence du discours (0-100)"
    )
    verbal_fluency_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score de fluidité",
        help_text="Fluidité et naturel du discours (0-100)"
    )
    verbal_vocabulary_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score de vocabulaire",
        help_text="Richesse et diversité du vocabulaire (0-100)"
    )
    
    # 3. Communication Paraverbale
    paraverbal_intonation_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score d'intonation",
        help_text="Variation d'intonation via ponctuation (0-100)"
    )
    paraverbal_rhythm_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score de rythme",
        help_text="Rythme de parole et débit (0-100)"
    )
    paraverbal_timing_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score de temporalité",
        help_text="Gestion des pauses et segments temporels (0-100)"
    )
    
    # Score global
    overall_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score global",
        help_text="Moyenne pondérée de tous les critères (0-100)"
    )
    
    # === ANALYSES DÉTAILLÉES (JSON) ===
    
    originality_analysis = models.JSONField(
        default=dict,
        verbose_name="Analyse d'originalité",
        help_text="Détails: mots-clés uniques, concepts innovants, créativité"
    )
    
    verbal_analysis = models.JSONField(
        default=dict,
        verbose_name="Analyse verbale",
        help_text="Détails: structure phrases, hésitations, vocabulaire utilisé"
    )
    
    paraverbal_analysis = models.JSONField(
        default=dict,
        verbose_name="Analyse paraverbale",
        help_text="Détails: variations tonales, pauses, débit parole"
    )
    
    # Statistiques audio
    audio_metrics = models.JSONField(
        default=dict,
        verbose_name="Métriques audio",
        help_text="Données brutes: pitch, energy, spectral features"
    )
    
    # Feedback IA
    ai_feedback = models.TextField(
        blank=True,
        verbose_name="Feedback de l'IA",
        help_text="Commentaires et recommandations générés par l'IA"
    )
    
    # Métadonnées
    processing_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Temps de traitement (secondes)"
    )
    ai_model_used = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Modèle IA utilisé",
        help_text="Ex: OpenAI Whisper, GPT-4, etc."
    )
    error_message = models.TextField(
        blank=True,
        verbose_name="Message d'erreur"
    )
    
    # Validation enseignant
    teacher_review = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_voice_assessments',
        verbose_name="Enseignant évaluateur"
    )
    teacher_comments = models.TextField(
        blank=True,
        verbose_name="Commentaires de l'enseignant"
    )
    teacher_validated = models.BooleanField(
        default=False,
        verbose_name="Validé par l'enseignant"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Traité le"
    )
    
    class Meta:
        verbose_name = "Évaluation Vocale"
        verbose_name_plural = "Évaluations Vocales"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student} - {self.prompt[:50]} ({self.get_status_display()})"
    
    def calculate_overall_score(self):
        """
        Calcule le score global basé sur les pondérations scientifiques
        
        Pondérations:
        - Originalité: 30%
        - Communication Verbale: 40% (structure 15%, fluency 15%, vocabulary 10%)
        - Communication Paraverbale: 30% (intonation 12%, rhythm 10%, timing 8%)
        """
        scores = [
            (self.originality_score, 0.30),
            (self.verbal_structure_score, 0.15),
            (self.verbal_fluency_score, 0.15),
            (self.verbal_vocabulary_score, 0.10),
            (self.paraverbal_intonation_score, 0.12),
            (self.paraverbal_rhythm_score, 0.10),
            (self.paraverbal_timing_score, 0.08),
        ]
        
        # Calculer la moyenne pondérée uniquement avec les scores disponibles
        total_score = 0
        total_weight = 0
        
        for score, weight in scores:
            if score is not None:
                total_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            self.overall_score = round(total_score / total_weight, 2)
        else:
            self.overall_score = 0
        
        return self.overall_score
    
    def get_grade_letter(self):
        """Convertit le score en lettre (A, B, C, D, E)"""
        if self.overall_score is None:
            return 'N/A'
        
        if self.overall_score >= 90:
            return 'A (Excellent)'
        elif self.overall_score >= 80:
            return 'B (Très bien)'
        elif self.overall_score >= 70:
            return 'C (Bien)'
        elif self.overall_score >= 60:
            return 'D (Assez bien)'
        else:
            return 'E (À améliorer)'
    
    def get_strengths_weaknesses(self):
        """Identifie les points forts et faibles"""
        criteria = {
            'Originalité': self.originality_score,
            'Structure': self.verbal_structure_score,
            'Fluidité': self.verbal_fluency_score,
            'Vocabulaire': self.verbal_vocabulary_score,
            'Intonation': self.paraverbal_intonation_score,
            'Rythme': self.paraverbal_rhythm_score,
            'Temporalité': self.paraverbal_timing_score,
        }
        
        # Filtrer les scores non nuls
        valid_criteria = {k: v for k, v in criteria.items() if v is not None}
        
        if not valid_criteria:
            return {'strengths': [], 'weaknesses': []}
        
        # Trier par score
        sorted_criteria = sorted(valid_criteria.items(), key=lambda x: x[1], reverse=True)
        
        # Points forts: scores >= 75
        strengths = [name for name, score in sorted_criteria if score >= 75]
        
        # Points faibles: scores < 60
        weaknesses = [name for name, score in sorted_criteria if score < 60]
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses
        }


class VoiceAssessmentCriteria(models.Model):
    """
    Critères d'évaluation configurables pour l'évaluation vocale
    Permet aux enseignants de personnaliser les critères selon l'âge/niveau
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Nom du critère"
    )
    category = models.CharField(
        max_length=50,
        choices=(
            ('originality', 'Originalité'),
            ('verbal', 'Communication Verbale'),
            ('paraverbal', 'Communication Paraverbale'),
        ),
        verbose_name="Catégorie"
    )
    description = models.TextField(
        verbose_name="Description"
    )
    weight = models.FloatField(
        default=1.0,
        verbose_name="Pondération",
        help_text="Poids relatif du critère (0-1)"
    )
    grade_levels = models.JSONField(
        default=list,
        verbose_name="Niveaux applicables",
        help_text="CP, CE1, CE2, CM1, CM2"
    )
    evaluation_rubric = models.JSONField(
        default=dict,
        verbose_name="Grille d'évaluation",
        help_text="Critères détaillés pour chaque niveau de score"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    class Meta:
        verbose_name = "Critère d'Évaluation Vocale"
        verbose_name_plural = "Critères d'Évaluation Vocale"
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"

