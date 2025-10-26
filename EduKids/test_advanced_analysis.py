#!/usr/bin/env python3
"""
Script de test pour l'analyse avancée de voix avec détection de tricherie
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduKids.settings')
django.setup()

from assessments.voice_analyzer import VoiceAnalyzer

def test_language_detection():
    """Test de détection de langue"""
    print("🔍 Test de détection de langue...")
    
    analyzer = VoiceAnalyzer()
    
    # Test français
    french_text = "Je pense que c'est une excellente idée. Je vais vous expliquer pourquoi."
    detected = analyzer._detect_language(french_text)
    print(f"  Français: '{french_text}' → {detected}")
    
    # Test anglais
    english_text = "I think this is an excellent idea. I will explain why."
    detected = analyzer._detect_language(english_text)
    print(f"  Anglais: '{english_text}' → {detected}")
    
    # Test arabe
    arabic_text = "أعتقد أن هذه فكرة ممتازة. سأشرح لك السبب."
    detected = analyzer._detect_language(arabic_text)
    print(f"  Arabe: '{arabic_text}' → {detected}")

def test_cheating_detection():
    """Test de détection de tricherie"""
    print("\n🚨 Test de détection de tricherie...")
    
    analyzer = VoiceAnalyzer()
    
    # Test lecture de script
    script_reading = "Je vais vous parler de ce sujet. Premièrement, il faut comprendre que... Deuxièmement, nous devons considérer... En conclusion, je pense que..."
    cheating = analyzer._detect_cheating(script_reading, "Parlez de votre passion")
    print(f"  Lecture de script: {cheating['reading_from_script']} - Violations: {cheating['violations']}")
    
    # Test contenu répétitif
    repetitive = "très très très très très très très très très très très très très très très très très très très très"
    cheating = analyzer._detect_cheating(repetitive, "Parlez de votre passion")
    print(f"  Contenu répétitif: {cheating['repetitive_content']} - Violations: {cheating['violations']}")
    
    # Test contenu insuffisant
    insufficient = "oui non peut-être"
    cheating = analyzer._detect_cheating(insufficient, "Parlez de votre passion")
    print(f"  Contenu insuffisant: {cheating['insufficient_content']} - Violations: {cheating['violations']}")

def test_complete_analysis():
    """Test d'analyse complète"""
    print("\n🧠 Test d'analyse complète...")
    
    analyzer = VoiceAnalyzer()
    
    # Test avec violation de langue
    print("  Test 1: Violation de langue (français demandé, anglais parlé)")
    prompt_fr = "Parlez de votre passion en français"
    transcription_en = "I love music very much. It makes me feel happy and relaxed."
    
    try:
        results = analyzer.analyze_complete(
            audio_path="dummy.wav",  # Fichier fictif
            transcription=transcription_en,
            prompt=prompt_fr
        )
        
        print(f"    Score d'originalité: {results['scores']['originality_score']}")
        print(f"    Violation de langue: {results['originality_analysis']['language_violation']}")
        print(f"    Détection de tricherie: {results['originality_analysis']['cheating_detection']}")
        
    except Exception as e:
        print(f"    Erreur: {e}")
    
    # Test avec tricherie
    print("\n  Test 2: Tricherie détectée")
    prompt_fr2 = "Parlez de votre passion"
    transcription_cheating = "Je vais vous parler de ma passion. Premièrement, la musique est importante. Deuxièmement, elle me détend. En conclusion, j'aime la musique."
    
    try:
        results = analyzer.analyze_complete(
            audio_path="dummy.wav",
            transcription=transcription_cheating,
            prompt=prompt_fr2
        )
        
        print(f"    Score d'originalité: {results['scores']['originality_score']}")
        print(f"    Tricherie détectée: {results['originality_analysis']['cheating_detection']}")
        
    except Exception as e:
        print(f"    Erreur: {e}")

def test_recommendations():
    """Test des recommandations"""
    print("\n💡 Test des recommandations...")
    
    analyzer = VoiceAnalyzer()
    
    # Scores faibles pour tester les recommandations
    scores = {
        'originality_score': 30,
        'verbal_structure_score': 40,
        'verbal_fluency_score': 35,
        'verbal_vocabulary_score': 45,
        'paraverbal_intonation_score': 50,
        'paraverbal_rhythm_score': 55,
        'paraverbal_timing_score': 60
    }
    
    originality = {
        'language_violation': {'transcription_language': 'english'},
        'cheating_detection': {'cheating_score': 40, 'severity': 'medium'}
    }
    
    verbal = {}
    paraverbal = {}
    
    recommendations = analyzer.generate_recommendations(scores, originality, verbal, paraverbal)
    
    print("  Recommandations générées:")
    for i, rec in enumerate(recommendations, 1):
        print(f"    {i}. {rec}")

if __name__ == "__main__":
    print("🚀 Test du système d'analyse avancée de voix")
    print("=" * 50)
    
    try:
        test_language_detection()
        test_cheating_detection()
        test_complete_analysis()
        test_recommendations()
        
        print("\n✅ Tous les tests sont terminés!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
