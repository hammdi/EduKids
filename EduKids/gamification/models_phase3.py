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
        if self.student.points >= self.accessory.points_required:
            self.student.points -= self.accessory.points_required
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