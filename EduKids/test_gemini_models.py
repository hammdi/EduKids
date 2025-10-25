"""
Script pour tester et lister les modèles Gemini disponibles
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduKids.settings')
django.setup()

from django.conf import settings
import google.generativeai as genai

def list_available_models():
    """Liste tous les modèles Gemini disponibles"""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        print("❌ GEMINI_API_KEY non configurée")
        return
    
    genai.configure(api_key=api_key)
    
    print("🔍 Listing des modèles Gemini disponibles...\n")
    print("=" * 80)
    
    try:
        models = genai.list_models()
        
        generate_content_models = []
        other_models = []
        
        for model in models:
            model_name = model.name
            supported_methods = model.supported_generation_methods
            
            if 'generateContent' in supported_methods:
                generate_content_models.append(model)
            else:
                other_models.append(model)
        
        # Afficher les modèles qui supportent generateContent
        print("\n✅ Modèles supportant generateContent:")
        print("-" * 80)
        for model in generate_content_models:
            print(f"  📌 {model.name}")
            print(f"     Display Name: {model.display_name}")
            print(f"     Description: {model.description}")
            print(f"     Methods: {', '.join(model.supported_generation_methods)}")
            print()
        
        # Afficher les autres modèles
        if other_models:
            print("\n⚠️  Autres modèles (ne supportent PAS generateContent):")
            print("-" * 80)
            for model in other_models:
                print(f"  📌 {model.name}")
                print(f"     Methods: {', '.join(model.supported_generation_methods)}")
                print()
        
        print("=" * 80)
        print(f"\n📊 Total: {len(generate_content_models)} modèles supportant generateContent")
        print(f"📊 Total: {len(other_models)} autres modèles")
        
        # Recommandation
        if generate_content_models:
            recommended = generate_content_models[0].name
            print(f"\n💡 Modèle recommandé: {recommended}")
            return recommended
        else:
            print("\n❌ Aucun modèle supportant generateContent trouvé")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des modèles: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_model(model_name):
    """Teste un modèle spécifique"""
    api_key = settings.GEMINI_API_KEY
    genai.configure(api_key=api_key)
    
    print(f"\n🧪 Test du modèle: {model_name}")
    print("=" * 80)
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Dis bonjour en français")
        
        print(f"✅ Le modèle {model_name} fonctionne!")
        print(f"📝 Réponse: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur avec le modèle {model_name}: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test des modèles Gemini pour EduKids\n")
    
    # Lister les modèles
    recommended_model = list_available_models()
    
    # Tester le modèle recommandé
    if recommended_model:
        test_model(recommended_model)
    
    # Tester des modèles spécifiques
    print("\n" + "=" * 80)
    print("🧪 Test de modèles spécifiques")
    print("=" * 80)
    
    models_to_test = [
        'models/gemini-1.5-pro',
        'models/gemini-1.5-flash',
        'models/gemini-pro',
        'models/gemini-pro-vision',
    ]
    
    for model_name in models_to_test:
        try:
            test_model(model_name)
        except Exception as e:
            print(f"❌ {model_name}: {e}")
        print()
