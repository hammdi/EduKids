"""
Script de test pour la fonctionnalité IA Avatar
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduKids.settings')
django.setup()

from gamification.services import AIAvatarService
from PIL import Image
import io


def test_ai_service():
    """Test du service IA"""
    print("🧪 Test du service IA Avatar...")
    
    try:
        # Initialiser le service
        ai_service = AIAvatarService()
        print("✅ Service IA initialisé")
        
        # Créer des images de test
        avatar_img = Image.new('RGB', (200, 200), color='lightblue')
        accessory_img = Image.new('RGBA', (100, 100), color='red')
        
        print("✅ Images de test créées")
        
        # Tester le composite
        result = ai_service.equip_accessory_with_ai(
            avatar_image=avatar_img,
            accessory_image=accessory_img,
            accessory_type='head',
            accessory_name='Chapeau Test'
        )
        
        if result['success']:
            print("✅ Composite réussi!")
            print(f"   Message: {result['message']}")
            
            # Sauvegarder l'image de test
            test_output = 'test_avatar_output.jpg'
            result['image'].save(test_output)
            print(f"✅ Image sauvegardée: {test_output}")
        else:
            print(f"❌ Échec: {result['message']}")
            
    except ValueError as e:
        print(f"⚠️  Configuration manquante: {e}")
        print("   Ajoute GEMINI_API_KEY dans .env ou settings.py")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_endpoints():
    """Test des endpoints (nécessite serveur lancé)"""
    print("\n🧪 Test des endpoints...")
    print("⚠️  Lance le serveur avec: python manage.py runserver")
    print("⚠️  Puis teste manuellement:")
    print("   1. POST /api/gamification/equip/1/")
    print("   2. POST /api/gamification/ai/equip/1/")
    print("   3. POST /api/gamification/unequip/1/")


def check_models():
    """Vérifier les modèles"""
    print("\n🧪 Vérification des modèles...")
    
    from gamification.models import Accessory, StudentAccessory, Avatar
    from students.models import StudentProfile
    
    print(f"✅ Accessory: {Accessory.objects.count()} accessoires")
    print(f"✅ StudentAccessory: {StudentAccessory.objects.count()} possessions")
    print(f"✅ Avatar: {Avatar.objects.count()} avatars")
    print(f"✅ StudentProfile: {StudentProfile.objects.count()} étudiants")


if __name__ == '__main__':
    print("=" * 60)
    print("🎨 TEST IA AVATAR - EDUKIDS")
    print("=" * 60)
    
    # Test 1: Service IA
    test_ai_service()
    
    # Test 2: Modèles
    check_models()
    
    # Test 3: Endpoints
    test_endpoints()
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés!")
    print("=" * 60)
