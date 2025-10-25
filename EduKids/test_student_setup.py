"""
Script de test pour créer un student et des accessoires
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduKids.settings')
django.setup()

from users.models import User
from students.models import Student
from gamification.models import Accessory, Avatar

# Créer un student de test
print("🔍 Vérification des utilisateurs existants...")
student_user = User.objects.filter(username='student_test').first()

if not student_user:
    print("✨ Création d'un student de test...")
    student_user = User.objects.create_user(
        username='student_test',
        email='student@test.com',
        password='test123',
        user_type='student',
        first_name='Alice',
        last_name='Dupont'
    )
    print(f"✅ User créé: {student_user.username}")
else:
    print(f"✅ User existant: {student_user.username}")

# Créer le profil student
try:
    student = student_user.student_profile
    print(f"✅ Profil Student existant: {student}")
except Student.DoesNotExist:
    print("✨ Création du profil Student...")
    student = Student.objects.create(
        user=student_user,
        grade_level='CE2',
        total_points=500
    )
    print(f"✅ Profil Student créé: {student}")

# Créer ou récupérer l'avatar
avatar, created = Avatar.objects.get_or_create(
    student=student,
    defaults={'level': 1}
)
if created:
    print(f"✅ Avatar créé: {avatar}")
else:
    print(f"✅ Avatar existant: {avatar}")

# Créer des accessoires de test
print("\n🛍️ Création des accessoires...")
accessories_data = [
    {'name': 'Chapeau de pirate', 'type': 'hat', 'points': 100, 'desc': 'Un super chapeau de pirate !'},
    {'name': 'Lunettes de soleil', 'type': 'glasses', 'points': 50, 'desc': 'Des lunettes stylées'},
    {'name': 'Cape de super-héros', 'type': 'outfit', 'points': 200, 'desc': 'Une cape magique'},
    {'name': 'Couronne dorée', 'type': 'hat', 'points': 150, 'desc': 'Une couronne de champion'},
    {'name': 'Écharpe colorée', 'type': 'accessory', 'points': 75, 'desc': 'Une écharpe arc-en-ciel'},
]

for acc_data in accessories_data:
    acc, created = Accessory.objects.get_or_create(
        name=acc_data['name'],
        defaults={
            'accessory_type': acc_data['type'],
            'points_required': acc_data['points'],
            'description': acc_data['desc'],
            'is_active': True
        }
    )
    if created:
        print(f"  ✅ Créé: {acc.name} ({acc.points_required} points)")
    else:
        print(f"  ℹ️  Existant: {acc.name}")

print("\n" + "="*60)
print("✅ Configuration terminée !")
print("="*60)
print(f"\n📝 Informations de connexion:")
print(f"   Username: student_test")
print(f"   Password: test123")
print(f"   Points: {student.total_points}")
print(f"\n🌐 URLs à tester:")
print(f"   Dashboard: http://127.0.0.1:8000/student/dashboard/")
print(f"   Gamification: http://127.0.0.1:8000/student/gamification/")
print(f"   Boutique: http://127.0.0.1:8000/student/store/")
print(f"   Personnalisation: http://127.0.0.1:8000/student/customize/")
print("\n" + "="*60)
