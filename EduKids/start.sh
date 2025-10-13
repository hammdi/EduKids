#!/bin/bash

# EduKids - Script de démarrage complet avec PostgreSQL
echo "🚀 Démarrage d'EduKids - Hub Éducatif Multimodal avec Évaluation Vocale IA"
echo "=========================================================================="

# Vérifier si Docker est en cours d'exécution
if command -v docker &> /dev/null; then
    echo "🐳 Vérification de Docker..."
    if docker info &> /dev/null; then
        echo "✅ Docker est actif"
        
        # Démarrer PostgreSQL + Redis avec Docker Compose
        echo "🚢 Démarrage de PostgreSQL et Redis..."
        docker-compose up -d
        
        echo "⏳ Attente que PostgreSQL soit prêt (10 secondes)..."
        sleep 10
    else
        echo "⚠️  Docker n'est pas actif, utilisation de SQLite"
    fi
else
    echo "⚠️  Docker non installé, utilisation de SQLite"
fi

# Activer l'environnement virtuel
echo "🐍 Activation de l'environnement virtuel..."
source ../venv/bin/activate

# Installer toutes les dépendances
echo "📦 Installation des dépendances complètes..."
pip install -q Django==5.2.6 Pillow==11.3.0 psycopg2-binary==2.9.10

# Créer les migrations
echo "📋 Création des migrations Django..."
python manage.py makemigrations

# Appliquer les migrations
echo "🗄️  Application des migrations..."
python manage.py migrate

# Créer un superutilisateur si nécessaire
echo "👤 Création du superutilisateur..."
python manage.py shell << EOF
from students.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@edukids.com',
        password='admin123',
        user_type='admin'
    )
    print("✅ Superutilisateur créé : admin / admin123")
else:
    print("✅ Superutilisateur déjà existant")
EOF

# Lancer le serveur
echo "🌟 Lancement du serveur Django..."
echo "=========================================================================="
echo "🎓 EduKids est maintenant accessible sur :"
echo "   📱 Application : http://localhost:8000"
echo "   🔧 Admin Django : http://localhost:8000/admin"
echo "   🎤 Évaluation Vocale IA : http://localhost:8000/voice-assessment/"
echo ""
if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
    echo "🐳 Services Docker (si actifs) :"
    echo "   🗄️  PostgreSQL : localhost:5432"
    echo "   📊 pgAdmin : http://localhost:8080 (admin@edukids.com / admin123)"
    echo "   💾 Redis : localhost:6379"
fi
echo ""
echo "👤 Connexions :"
echo "   Admin Django : admin / admin123"
echo "   Commande seeding : python manage.py seed"
echo "=========================================================================="
echo ""

python manage.py runserver
