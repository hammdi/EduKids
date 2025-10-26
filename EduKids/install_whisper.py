#!/usr/bin/env python3
"""
Script pour installer et tester OpenAI Whisper pour la transcription
"""
import subprocess
import sys
import os

def install_whisper():
    """Installer OpenAI Whisper"""
    print("🔧 Installation d'OpenAI Whisper...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai-whisper"])
        print("✅ Whisper installé avec succès!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        return False

def test_whisper():
    """Tester Whisper avec un fichier audio simple"""
    try:
        import whisper
        print("✅ Whisper importé avec succès!")
        
        # Test avec un modèle simple
        print("🔄 Test du modèle Whisper...")
        model = whisper.load_model("base")
        print("✅ Modèle Whisper chargé avec succès!")
        
        return True
    except ImportError:
        print("❌ Whisper non installé")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    print("🚀 Installation et test d'OpenAI Whisper pour EduKids")
    print("=" * 50)
    
    # Installer Whisper
    if install_whisper():
        print("\n🧪 Test de Whisper...")
        if test_whisper():
            print("\n✅ Whisper est prêt pour la transcription!")
            print("\n📝 Instructions:")
            print("1. Redémarrez votre serveur Django")
            print("2. Testez l'enregistrement vocal")
            print("3. La transcription sera automatique avec Whisper")
        else:
            print("\n❌ Whisper n'est pas fonctionnel")
    else:
        print("\n❌ Installation échouée")

if __name__ == "__main__":
    main()
