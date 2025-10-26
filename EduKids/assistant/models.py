"""
Models pour l'assistant virtuel IA - EduKids
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from students.models import User, Student


class VirtualAssistant(models.Model):
    """
    Configuration de l'assistant virtuel IA
    """
    name = models.CharField(max_length=100, verbose_name="Nom de l'assistant")
    personality = models.CharField(
        max_length=50,
        default='friendly',
        verbose_name="Personnalité",
        help_text="friendly, professional, playful, etc."
    )
    language = models.CharField(
        max_length=10,
        default='fr',
        verbose_name="Langue"
    )
    welcome_message = models.TextField(
        verbose_name="Message de bienvenue",
        default="Bonjour! Je suis là pour t'aider dans ton apprentissage. Comment puis-je t'aider aujourd'hui?"
    )
    system_prompt = models.TextField(
        verbose_name="Prompt système",
        help_text="Instructions pour l'IA"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Assistant Virtuel"
        verbose_name_plural = "Assistants Virtuels"
    
    def __str__(self):
        return self.name


class Conversation(models.Model):
    """
    Conversations entre élèves et assistant
    """
    TOPIC_CHOICES = (
        ('general', 'Général'),
        ('francais', 'Français'),
        ('mathematiques', 'Mathématiques'),
        ('sciences', 'Sciences'),
        ('histoire', 'Histoire'),
        ('geographie', 'Géographie'),
        ('other', 'Autre'),
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name="Élève"
    )
    assistant = models.ForeignKey(
        VirtualAssistant,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name="Assistant"
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Titre",
        help_text="Généré automatiquement à partir du premier message"
    )
    context = models.JSONField(
        default=dict,
        verbose_name="Contexte",
        help_text="Informations contextuelles pour l'IA"
    )
    topic = models.CharField(
        max_length=20,
        choices=TOPIC_CHOICES,
        default='general',
        verbose_name="Sujet"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Démarrée le")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Terminée le")
    
    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student} - {self.title or 'Conversation'}"


class Message(models.Model):
    """
    Messages dans les conversations
    """
    MESSAGE_TYPE_CHOICES = (
        ('text', 'Texte'),
        ('audio', 'Audio'),
        ('image', 'Image'),
        ('system', 'Système'),
    )
    
    SENDER_TYPE_CHOICES = (
        ('student', 'Élève'),
        ('assistant', 'Assistant'),
        ('system', 'Système'),
    )
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Conversation"
    )
    sender_type = models.CharField(
        max_length=10,
        choices=SENDER_TYPE_CHOICES,
        verbose_name="Émetteur"
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        verbose_name="Type de message"
    )
    content = models.TextField(verbose_name="Contenu")
    file = models.FileField(
        upload_to='messages/',
        blank=True,
        null=True,
        verbose_name="Fichier joint"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Données supplémentaires (tokens, modèle IA, etc.)"
    )
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Envoyé le")
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['conversation', 'created_at']
    
    def __str__(self):
        return f"{self.get_sender_type_display()}: {self.content[:50]}"


class KnowledgeBase(models.Model):
    """
    Base de connaissances pour l'assistant IA
    """
    CATEGORY_CHOICES = (
        ('general', 'Général'),
        ('francais', 'Français'),
        ('mathematiques', 'Mathématiques'),
        ('sciences', 'Sciences'),
        ('histoire', 'Histoire'),
        ('geographie', 'Géographie'),
        ('other', 'Autre'),
    )
    
    title = models.CharField(max_length=200, verbose_name="Titre")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Catégorie"
    )
    content = models.TextField(verbose_name="Contenu")
    keywords = models.JSONField(
        default=list,
        verbose_name="Mots-clés",
        help_text="Mots-clés pour la recherche sémantique"
    )
    grade_levels = models.JSONField(
        default=list,
        verbose_name="Niveaux",
        help_text="CP, CE1, CE2, CM1, CM2"
    )
    usage_count = models.IntegerField(
        default=0,
        verbose_name="Nombre d'utilisations"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Base de connaissances"
        verbose_name_plural = "Base de connaissances"
        ordering = ['-usage_count', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class AssistantInteraction(models.Model):
    """
    Historique des interactions pour améliorer l'IA
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='assistant_interactions',
        verbose_name="Élève"
    )
    question = models.TextField(verbose_name="Question de l'élève")
    answer = models.TextField(verbose_name="Réponse de l'assistant")
    was_helpful = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Réponse utile?"
    )
    feedback = models.TextField(blank=True, verbose_name="Feedback de l'élève")
    context = models.JSONField(
        default=dict,
        verbose_name="Contexte",
        help_text="Informations contextuelles"
    )
    response_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Temps de réponse (secondes)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    
    class Meta:
        verbose_name = "Interaction Assistant"
        verbose_name_plural = "Interactions Assistant"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student} - {self.question[:50]}"


class Quiz(models.Model):
    """A saved quiz generated by the assistant and attached to a conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200, blank=True)
    topic = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return f"Quiz {self.id} - {self.title or self.topic or 'Sans titre'}"


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.IntegerField(default=0)
    correct_choice_index = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['quiz', 'order']

    def __str__(self):
        return f"Q{self.order}: {self.text[:80]}"


class QuizOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=500)
    index = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.index}: {self.text[:60]}"


class MediaFile(models.Model):
    """Stores generated images/PDFs and links them to a conversation/message."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='media_files')
    uploader = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='assistant_media/%Y/%m/%d')
    thumbnail = models.ImageField(upload_to='assistant_media/thumbs/%Y/%m/%d', null=True, blank=True)
    media_type = models.CharField(max_length=20, choices=(('image','Image'),('pdf','PDF'),('other','Other')), default='image')
    caption = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Fichier média'
        verbose_name_plural = 'Fichiers médias'

    def __str__(self):
        return f"Media {self.id} ({self.media_type}) - {self.caption[:60]}"


class QuizAttempt(models.Model):
    """Record of a student attempt at a saved quiz."""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='quiz_attempts')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_attempts')
    total = models.IntegerField(default=0)
    correct = models.IntegerField(default=0)
    score = models.FloatField(default=0.0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tentative de quiz'
        verbose_name_plural = 'Tentatives de quiz'

    def __str__(self):
        return f"Attempt {self.id} - Quiz {self.quiz_id} - Student {self.student_id}"


class QuizAttemptAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='attempt_answers')
    selected_index = models.IntegerField(null=True, blank=True)
    # Store the actual option text chosen by the student (helps when answers come as text)
    selected_text = models.CharField(max_length=500, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Réponse tentative'
        verbose_name_plural = 'Réponses tentatives'

    def __str__(self):
        return f"AttemptAnswer {self.id} - Q{self.question_id} - correct={self.is_correct}"
