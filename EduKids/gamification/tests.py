"""
Tests unitaires pour la gamification - EduKids
"""
from django.test import TestCase
from django.utils import timezone
from students.models import Student, User
from .models import (
    Mission, UserMission, Badge, UserBadge,
    Avatar, Accessory, UserAccessory
)
from .services import attribuer_points_et_badges


class MissionModelTest(TestCase):
    """
    Tests pour le modèle Mission
    """

    def setUp(self):
        """
        Configuration initiale pour les tests
        """
        self.mission = Mission.objects.create(
            titre="Lire 5 histoires",
            description="Lire au moins 5 histoires courtes",
            type_mission="lecture",
            objectif=5,
            points=50
        )

    def test_mission_creation(self):
        """
        Test de création d'une mission
        """
        self.assertEqual(self.mission.titre, "Lire 5 histoires")
        self.assertEqual(self.mission.objectif, 5)
        self.assertEqual(self.mission.points, 50)
        self.assertTrue(self.mission.actif)

    def test_mission_str(self):
        """
        Test de la méthode __str__ de Mission
        """
        self.assertEqual(str(self.mission), "Lire 5 histoires (Lecture)")


class UserMissionModelTest(TestCase):
    """
    Tests pour le modèle UserMission
    """

    def setUp(self):
        """
        Configuration initiale
        """
        self.user = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='password123',
            first_name='Test',
            last_name='Student'
        )
        self.student = Student.objects.create(
            user=self.user,
            grade_level='CP',
            birth_date='2018-01-01'
        )
        self.mission = Mission.objects.create(
            titre="Test Mission",
            description="Mission de test",
            type_mission="lecture",
            objectif=3,
            points=30
        )

    def test_user_mission_creation(self):
        """
        Test de création d'une UserMission
        """
        user_mission = UserMission.objects.create(
            user=self.student,
            mission=self.mission,
            progression=1
        )
        self.assertEqual(user_mission.progression, 1)
        self.assertEqual(user_mission.statut, 'en_cours')

    def test_user_mission_completion(self):
        """
        Test de completion d'une mission
        """
        user_mission = UserMission.objects.create(
            user=self.student,
            mission=self.mission,
            progression=3
        )

        # Simuler la completion
        user_mission.statut = 'termine'
        user_mission.date_terminee = timezone.now()
        user_mission.save()

        self.assertEqual(user_mission.statut, 'termine')
        self.assertIsNotNone(user_mission.date_terminee)


class BadgeModelTest(TestCase):
    """
    Tests pour le modèle Badge
    """

    def setUp(self):
        """
        Configuration initiale
        """
        self.badge = Badge.objects.create(
            nom="Lecteur Débutant",
            description="Premier badge de lecture",
            icon="fa-book",
            condition="Terminer 3 missions de lecture",
            points_bonus=10
        )

    def test_badge_creation(self):
        """
        Test de création d'un badge
        """
        self.assertEqual(self.badge.nom, "Lecteur Débutant")
        self.assertEqual(self.badge.points_bonus, 10)
        self.assertTrue(self.badge.is_active)

    def test_badge_str(self):
        """
        Test de la méthode __str__ de Badge
        """
        self.assertEqual(str(self.badge), "Lecteur Débutant")


class UserBadgeModelTest(TestCase):
    """
    Tests pour le modèle UserBadge
    """

    def setUp(self):
        """
        Configuration initiale
        """
        self.user = User.objects.create_user(
            username='test_student2',
            email='student2@test.com',
            password='password123',
            first_name='Test2',
            last_name='Student2'
        )
        self.student = Student.objects.create(
            user=self.user,
            grade_level='CE1',
            birth_date='2017-01-01'
        )
        self.badge = Badge.objects.create(
            nom="Test Badge",
            description="Badge de test",
            icon="fa-star",
            condition="Test condition",
            points_bonus=5
        )

    def test_user_badge_creation(self):
        """
        Test de création d'un UserBadge
        """
        user_badge = UserBadge.objects.create(
            user=self.student,
            badge=self.badge
        )
        self.assertEqual(user_badge.user, self.student)
        self.assertEqual(user_badge.badge, self.badge)
        self.assertIsNotNone(user_badge.date_obtention)


class GamificationServicesTest(TestCase):
    """
    Tests pour les services de gamification
    """

    def setUp(self):
        """
        Configuration initiale
        """
        self.user = User.objects.create_user(
            username='test_student3',
            email='student3@test.com',
            password='password123',
            first_name='Test3',
            last_name='Student3'
        )
        self.student = Student.objects.create(
            user=self.user,
            grade_level='CE2',
            birth_date='2016-01-01'
        )
        self.mission = Mission.objects.create(
            titre="Mission Test",
            description="Mission pour test",
            type_mission="lecture",
            objectif=1,
            points=20
        )
        self.badge = Badge.objects.create(
            nom="Lecteur Débutant",
            description="Badge pour test",
            icon="fa-test",
            condition="3 missions lecture terminees",
            points_bonus=15
        )

    def test_attribuer_points_et_badges(self):
        """
        Test de la fonction d'attribution automatique
        """
        user_mission = UserMission.objects.create(
            user=self.student,
            mission=self.mission,
            progression=1,
            statut='termine'
        )

        result = attribuer_points_et_badges(user_mission)

        # Vérifier que les points sont attribués
        self.assertEqual(result['points_ajoutes'], 20)

        # Comme il n'y a qu'une mission terminée, pas de badge
        self.assertEqual(len(result['badges_gagnes']), 0)

    def test_badge_attribution_multiple_missions(self):
        """
        Test d'attribution de badge après plusieurs missions
        """
        # Créer 3 missions terminées
        for i in range(3):
            mission = Mission.objects.create(
                titre=f"Mission {i}",
                description=f"Mission {i}",
                type_mission="lecture",
                objectif=1,
                points=10
            )
            UserMission.objects.create(
                user=self.student,
                mission=mission,
                progression=1,
                statut='termine'
            )

        # Tester la dernière mission
        last_mission = Mission.objects.create(
            titre="Last Mission",
            description="Last Mission",
            type_mission="lecture",
            objectif=1,
            points=10
        )
        user_mission = UserMission.objects.create(
            user=self.student,
            mission=last_mission,
            progression=1,
            statut='termine'
        )

        result = attribuer_points_et_badges(user_mission)

        # Devrait gagner le badge
        self.assertIn("Lecteur Débutant", result['badges_gagnes'])


class AvatarModelTest(TestCase):
    """
    Tests pour le modèle Avatar
    """

    def setUp(self):
        """
        Configuration initiale
        """
        self.avatar = Avatar.objects.create(
            name="Avatar Test",
            avatar_type="base",
            level_required=1,
            points_required=0
        )

    def test_avatar_creation(self):
        """
        Test de création d'un avatar
        """
        self.assertEqual(self.avatar.name, "Avatar Test")
        self.assertEqual(self.avatar.avatar_type, "base")
        self.assertEqual(self.avatar.level_required, 1)
        self.assertTrue(self.avatar.is_active)

    def test_avatar_str(self):
        """
        Test de la méthode __str__ d'Avatar
        """
        self.assertEqual(str(self.avatar), "Avatar Test (base)")


class AvatarModelTest(TestCase):
    """
    Tests pour le modèle Avatar (Phase 3)
    """

    def setUp(self):
        """
        Configuration initiale
        """
        self.user = User.objects.create_user(
            username='teststudent',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Student'
        )
        self.student = Student.objects.create(
            user=self.user,
            grade_level='cm2',
            learning_style='visual',
            birth_date='2010-01-01'
        )

    def test_avatar_creation(self):
        """
        Test de création d'un avatar personnalisé
        """
        # Supprimer l'avatar créé par le signal
        Avatar.objects.filter(student=self.student).delete()
        
        avatar = Avatar.objects.create(
            student=self.student,
            level=1
        )
        self.assertEqual(avatar.student, self.student)
        self.assertEqual(avatar.level, 1)

    def test_get_equipped_accessories_by_type(self):
        """
        Test des accessoires équipés sur l'avatar
        """
        # Utiliser l'avatar créé par le signal ou en créer un nouveau
        avatar, created = Avatar.objects.get_or_create(
            student=self.student,
            defaults={'level': 1}
        )

        # Créer des accessoires
        hat = Accessory.objects.create(
            name="Chapeau", accessory_type="hat", points_required=10
        )
        glasses = Accessory.objects.create(
            name="Lunettes", accessory_type="glasses", points_required=15
        )

        # Équiper les accessoires directement sur l'avatar
        avatar.accessories.add(hat, glasses)
        
        # Vérifier que les accessoires sont équipés
        equipped_accessories = avatar.accessories.all()
        self.assertEqual(equipped_accessories.count(), 2)
        accessory_types = [acc.accessory_type for acc in equipped_accessories]
        self.assertIn('hat', accessory_types)
        self.assertIn('glasses', accessory_types)


class UserAccessoryPhase3Test(TestCase):
    """
    Tests supplémentaires pour UserAccessory (Phase 3)
    """

    def setUp(self):
        """
        Configuration initiale
        """
        self.user = User.objects.create_user(
            username='teststudent2',
            email='test2@example.com',
            password='testpass123',
            first_name='Test2',
            last_name='Student2'
        )
        self.student = Student.objects.create(
            user=self.user,
            grade_level='cm1',
            learning_style='kinesthetic',
            birth_date='2011-01-01'
        )
        # Créer ou récupérer un avatar pour les tests
        self.avatar, created = Avatar.objects.get_or_create(
            student=self.student,
            defaults={'level': 1}
        )
        self.accessory = Accessory.objects.create(
            name="Chapeau Premium",
            accessory_type="hat",
            points_required=100
        )

    def test_purchase_method(self):
        """
        Test de la méthode purchase
        """
        user_accessory = UserAccessory.objects.create(
            student=self.student,
            accessory=self.accessory,
            status='unlocked'
        )

        # Donner assez de points
        self.student.points = 150
        self.student.save()

        # Effectuer l'achat
        result = user_accessory.purchase()
        self.assertTrue(result)
        self.assertEqual(user_accessory.status, 'owned')
        self.assertIsNotNone(user_accessory.date_obtained)

        # Vérifier que les points ont été déduits
        self.student.refresh_from_db()
        self.assertEqual(self.student.points, 50)

    def test_purchase_insufficient_points(self):
        """
        Test d'achat avec points insuffisants
        """
        user_accessory = UserAccessory.objects.create(
            student=self.student,
            accessory=self.accessory,
            status='unlocked'
        )

        # Pas assez de points
        self.student.points = 50
        self.student.save()

        # Tenter l'achat
        result = user_accessory.purchase()
        self.assertFalse(result)
        self.assertEqual(user_accessory.status, 'unlocked')

    def test_equip_method(self):
        """
        Test de la méthode equip
        """
        user_accessory = UserAccessory.objects.create(
            student=self.student,
            accessory=self.accessory,
            status='owned'
        )

        # Équiper l'accessoire
        result = user_accessory.equip(self.avatar)
        self.assertTrue(result)
        self.assertEqual(user_accessory.status, 'equipped')
        # Vérifier que l'accessoire est dans les accessoires équipés de l'avatar
        self.assertIn(self.accessory, self.avatar.accessories.all())

    def test_unequip_method(self):
        """
        Test de la méthode unequip
        """
        user_accessory = UserAccessory.objects.create(
            student=self.student,
            accessory=self.accessory,
            status='equipped'
        )
        # Ajouter l'accessoire à l'avatar
        self.avatar.accessories.add(self.accessory)

        # Déséquiper l'accessoire
        result = user_accessory.unequip(self.avatar)
        self.assertTrue(result)
        self.assertEqual(user_accessory.status, 'owned')
        # Vérifier que l'accessoire n'est plus dans les accessoires équipés de l'avatar
        self.assertNotIn(self.accessory, self.avatar.accessories.all())
