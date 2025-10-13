"""
Commande de seeding pour EduKids - Équivalent des seeders Laravel
Usage: python manage.py seed
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from students.models import Student, Teacher, Parent, Classroom
from exercises.models import Subject, Topic, Exercise, Question, Answer
from assistant.models import VirtualAssistant, KnowledgeBase
from gamification.models import Badge, Reward, Challenge
from datetime import date, datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed la base de données avec des données de démonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-only',
            action='store_true',
            help='Créer uniquement l\'administrateur',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Début du seeding...'))

        # Toujours créer l'admin
        self.create_admin()

        if not options['admin_only']:
            self.create_subjects()
            self.create_teachers()
            self.create_students()
            self.create_classrooms()
            self.create_topics_and_exercises()
            self.create_assistant()
            self.create_gamification()

        self.stdout.write(self.style.SUCCESS('✅ Seeding terminé avec succès !'))

    def create_admin(self):
        """Créer l'administrateur principal"""
        self.stdout.write('👤 Création de l\'administrateur...')
        
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('  ⚠️  Admin existe déjà'))
            return

        admin = User.objects.create_superuser(
            username='admin',
            email='admin@edukids.com',
            password='admin123',
            user_type='admin',
            first_name='Admin',
            last_name='EduKids'
        )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Admin créé : {admin.username} / admin123'))

    def create_subjects(self):
        """Créer les matières"""
        self.stdout.write('📚 Création des matières...')
        
        subjects_data = [
            {'name': 'Français', 'icon': 'fa-book', 'color': '#e74c3c', 'order': 1},
            {'name': 'Mathématiques', 'icon': 'fa-calculator', 'color': '#3498db', 'order': 2},
            {'name': 'Sciences', 'icon': 'fa-flask', 'color': '#2ecc71', 'order': 3},
            {'name': 'Histoire', 'icon': 'fa-landmark', 'color': '#f39c12', 'order': 4},
            {'name': 'Géographie', 'icon': 'fa-globe', 'color': '#1abc9c', 'order': 5},
        ]
        
        for data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created:
                self.stdout.write(f'  ✓ {subject.name}')

    def create_teachers(self):
        """Créer des enseignants"""
        self.stdout.write('👨‍🏫 Création des enseignants...')
        
        teachers_data = [
            {
                'username': 'mme.dubois',
                'email': 'dubois@edukids.com',
                'first_name': 'Marie',
                'last_name': 'Dubois',
                'specialties': ['Français', 'Histoire'],
                'experience': 10
            },
            {
                'username': 'm.martin',
                'email': 'martin@edukids.com',
                'first_name': 'Pierre',
                'last_name': 'Martin',
                'specialties': ['Mathématiques', 'Sciences'],
                'experience': 8
            },
        ]
        
        for data in teachers_data:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password='teacher123',
                    user_type='teacher',
                    first_name=data['first_name'],
                    last_name=data['last_name']
                )
                
                Teacher.objects.create(
                    user=user,
                    subject_specialties=data['specialties'],
                    teaching_experience=data['experience']
                )
                self.stdout.write(f'  ✓ {user.get_full_name()}')

    def create_students(self):
        """Créer des élèves"""
        self.stdout.write('👦👧 Création des élèves...')
        
        students_data = [
            {
                'username': 'lucas.petit',
                'first_name': 'Lucas',
                'last_name': 'Petit',
                'grade': 'CP',
                'birth': date(2018, 3, 15)
            },
            {
                'username': 'emma.bernard',
                'first_name': 'Emma',
                'last_name': 'Bernard',
                'grade': 'CE1',
                'birth': date(2017, 7, 22)
            },
            {
                'username': 'noah.thomas',
                'first_name': 'Noah',
                'last_name': 'Thomas',
                'grade': 'CE2',
                'birth': date(2016, 11, 8)
            },
            {
                'username': 'lea.robert',
                'first_name': 'Léa',
                'last_name': 'Robert',
                'grade': 'CM1',
                'birth': date(2015, 5, 30)
            },
            {
                'username': 'louis.richard',
                'first_name': 'Louis',
                'last_name': 'Richard',
                'grade': 'CM2',
                'birth': date(2014, 9, 12)
            },
        ]
        
        for data in students_data:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    email=f"{data['username']}@edukids.com",
                    password='student123',
                    user_type='student',
                    first_name=data['first_name'],
                    last_name=data['last_name']
                )
                
                Student.objects.create(
                    user=user,
                    grade_level=data['grade'],
                    birth_date=data['birth'],
                    learning_style='visual',
                    preferred_language='fr'
                )
                self.stdout.write(f'  ✓ {user.get_full_name()} ({data["grade"]})')

    def create_classrooms(self):
        """Créer des classes"""
        self.stdout.write('🏫 Création des classes...')
        
        grades = ['CP', 'CE1', 'CE2', 'CM1', 'CM2']
        
        for grade in grades:
            classroom, created = Classroom.objects.get_or_create(
                name=f'Classe {grade}',
                grade_level=grade,
                school_year='2024-2025',
                defaults={'max_students': 25}
            )
            
            # Assigner les élèves à leur classe
            students = Student.objects.filter(grade_level=grade)
            classroom.students.set(students)
            
            if created:
                self.stdout.write(f'  ✓ {classroom.name} ({students.count()} élèves)')

    def create_topics_and_exercises(self):
        """Créer des thèmes et exercices"""
        self.stdout.write('📝 Création des exercices...')
        
        # Français - CP
        francais = Subject.objects.get(name='Français')
        topic_cp, _ = Topic.objects.get_or_create(
            subject=francais,
            name='Les voyelles',
            grade_level='CP',
            defaults={'description': 'Apprendre les voyelles A, E, I, O, U'}
        )
        
        exercise, created = Exercise.objects.get_or_create(
            title='Reconnaître les voyelles',
            topic=topic_cp,
            defaults={
                'description': 'Identifier les voyelles dans les mots',
                'exercise_type': 'qcm',
                'difficulty_level': 1,
                'instructions': 'Choisis la bonne voyelle',
                'points': 10,
                'is_published': True
            }
        )
        
        if created:
            # Ajouter des questions
            q1 = Question.objects.create(
                exercise=exercise,
                question_text='Quelle est la première lettre du mot "Arbre"?',
                question_type='single_choice',
                points=2,
                order=1
            )
            Answer.objects.create(question=q1, answer_text='A', is_correct=True, order=1)
            Answer.objects.create(question=q1, answer_text='E', is_correct=False, order=2)
            Answer.objects.create(question=q1, answer_text='I', is_correct=False, order=3)
            
            self.stdout.write(f'  ✓ {exercise.title}')

        # Mathématiques - CP
        maths = Subject.objects.get(name='Mathématiques')
        topic_maths, _ = Topic.objects.get_or_create(
            subject=maths,
            name='Les nombres de 1 à 10',
            grade_level='CP',
            defaults={'description': 'Compter et reconnaître les nombres'}
        )
        
        exercise_maths, created = Exercise.objects.get_or_create(
            title='Compter jusqu\'à 10',
            topic=topic_maths,
            defaults={
                'description': 'Apprendre à compter',
                'exercise_type': 'calcul',
                'difficulty_level': 1,
                'instructions': 'Combien y a-t-il d\'objets?',
                'points': 10,
                'is_published': True
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ {exercise_maths.title}')

    def create_assistant(self):
        """Créer l'assistant virtuel"""
        self.stdout.write('🤖 Création de l\'assistant virtuel...')
        
        assistant, created = VirtualAssistant.objects.get_or_create(
            name='EduBot',
            defaults={
                'personality': 'friendly',
                'language': 'fr',
                'welcome_message': 'Bonjour! Je suis EduBot, ton assistant d\'apprentissage! 😊',
                'system_prompt': 'Tu es un assistant éducatif pour enfants de 6-12 ans. Sois patient, encourageant et utilise un langage simple.',
                'is_active': True
            }
        )
        
        if created:
            # Ajouter de la connaissance de base
            KnowledgeBase.objects.create(
                title='Les voyelles',
                category='francais',
                content='Les voyelles sont: A, E, I, O, U. On les utilise dans tous les mots français.',
                keywords=['voyelles', 'lettres', 'alphabet'],
                grade_levels=['CP', 'CE1']
            )
            
            self.stdout.write(f'  ✓ {assistant.name}')

    def create_gamification(self):
        """Créer les éléments de gamification"""
        self.stdout.write('🎮 Création des badges et récompenses...')
        
        # Badges
        badges_data = [
            {
                'name': 'Premier Pas',
                'description': 'Compléter ton premier exercice',
                'badge_type': 'achievement',
                'rarity': 'common',
                'icon': 'fa-star',
                'points_reward': 10
            },
            {
                'name': 'Matheux',
                'description': 'Réussir 10 exercices de mathématiques',
                'badge_type': 'mastery',
                'rarity': 'uncommon',
                'icon': 'fa-calculator',
                'points_reward': 50
            },
            {
                'name': 'Série de 7',
                'description': 'Se connecter 7 jours d\'affilée',
                'badge_type': 'streak',
                'rarity': 'rare',
                'icon': 'fa-fire',
                'points_reward': 100
            },
        ]
        
        for data in badges_data:
            badge, created = Badge.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created:
                self.stdout.write(f'  ✓ Badge: {badge.name}')

        # Récompenses
        rewards_data = [
            {'name': 'Avatar Robot', 'reward_type': 'avatar', 'cost_points': 50},
            {'name': 'Avatar Super-héros', 'reward_type': 'avatar', 'cost_points': 100},
            {'name': 'Thème Espace', 'reward_type': 'theme', 'cost_points': 200},
        ]
        
        for data in rewards_data:
            reward, created = Reward.objects.get_or_create(
                name=data['name'],
                defaults={**data, 'description': f'Débloquer {data["name"]}'}
            )
            if created:
                self.stdout.write(f'  ✓ Récompense: {reward.name}')

        # Défi
        challenge, created = Challenge.objects.get_or_create(
            title='Défi Hebdomadaire',
            defaults={
                'description': 'Complète 5 exercices cette semaine',
                'challenge_type': 'weekly',
                'difficulty': 'medium',
                'objective': {'exercises_count': 5},
                'points_reward': 75,
                'start_date': datetime.now(),
                'end_date': datetime.now() + timedelta(days=7),
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ Défi: {challenge.title}')

