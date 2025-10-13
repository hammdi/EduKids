#!/bin/bash

# EduKids - Script de démarrage simplifié (SQLite)
echo "🚀 Démarrage d'EduKids - Hub Éducatif Multimodal (Mode Simple)"
echo "=============================================================="

# Activer l'environnement virtuel
echo "🐍 Activation de l'environnement virtuel..."
source ../venv/bin/activate

# Installer les dépendances de base seulement
echo "📦 Installation des dépendances de base..."
pip install Django==5.2.6 Pillow==11.3.0

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
echo "=============================================================="
echo "🎓 EduKids est maintenant accessible sur :"
echo "   📱 Application : http://localhost:8000"
echo "   🔧 Admin : http://localhost:8000/admin"
echo ""
echo "👤 Connexion Admin Django : admin / admin123"
echo "=============================================================="
echo ""

python manage.py runserver
