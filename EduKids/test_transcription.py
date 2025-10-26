#!/usr/bin/env python3
"""
Script de test pour vérifier la transcription
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduKids.settings')
django.setup()

from assessments.views import try_whisper_transcription, try_multiple_transcription_services
from django.core.files.uploadedfile import SimpleUploadedFile

def test_transcription():
    """Tester la transcription avec un fichier audio"""
    print("🧪 Test de la transcription...")
    
    # Créer un fichier audio de test (simulé)
    test_audio_content = b"fake audio content for testing"
    test_audio = SimpleUploadedFile(
        "test_recording.wav",
        test_audio_content,
        content_type="audio/wav"
    )
    
    print("🔄 Test avec Whisper...")
    result = try_whisper_transcription(test_audio, "fr-FR")
    print(f"Résultat Whisper: {result}")
    
    print("\n🔄 Test avec multiple services...")
    result = try_multiple_transcription_services(test_audio, "fr-FR")
    print(f"Résultat multiple services: {result}")
    
    if result.get('success'):
        print("✅ Transcription fonctionnelle!")
        print(f"📝 Transcription: {result['transcription']}")
        print(f"🎯 Méthode: {result['method']}")
        print(f"📊 Confiance: {result['confidence']}")
    else:
        print("❌ Transcription non fonctionnelle")
        print(f"Erreur: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_transcription()
