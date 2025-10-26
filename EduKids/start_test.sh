#!/bin/bash

echo "🚀 Démarrage du serveur EduKids pour tests AssemblyAI..."
echo ""
echo "📍 URL de test: http://127.0.0.1:8000/assessments/voice/"
echo ""
echo "📖 Guides disponibles:"
echo "   - GUIDE_TEST_ASSEMBLYAI.md (Scénarios de test)"
echo "   - SYSTEME_ASSEMBLYAI_RESUME.md (Documentation complète)"
echo ""
echo "🎤 AssemblyAI API Key: 31139210ac044722a0c9dee5b135e4b6"
echo "⏱️ Quota: 5 heures/mois (vos 4-5 tests = 10-15 minutes)"
echo ""
echo "============================================================"
echo "🔥 LOGS EN DIRECT - Vous verrez:"
echo "============================================================"
echo "   🎤 Transcription AssemblyAI RÉELLE"
echo "   🧠 Analyse VoiceAnalyzer détaillée"
echo "   🌍 Détection de langue"
echo "   🚨 Détection de tricherie"
echo "   📊 Scores calculés (0-100)"
echo "============================================================"
echo ""

# Activer l'environnement virtuel
source ../venv/bin/activate

# Démarrer le serveur Django
python manage.py runserver 8000
