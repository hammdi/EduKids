# 🎓 EduKids - Hub Éducatif Multimodal

## 📋 **Vue d'Ensemble du Projet**

**EduKids** est une plateforme éducative Django pour l'enseignement primaire (6-12 ans) avec :
- 🤖 Assistant virtuel intelligent
- 📝 Génération automatique d'exercices  
- 📊 Évaluation et suivi des progrès
- **🎤 Évaluation vocale par IA** (Innovation scientifique - Contribution PFE)
- 🎮 Gamification pour motiver les élèves

### **Public Cible :**
- CP-CE1 (6-8 ans)
- CE2-CM1 (8-10 ans) 
- CM2 (10-12 ans)

### **Technologies :**
- **Backend** : Django 5.2.6 (100% Django)
- **Base de données** : SQLite (développement) / PostgreSQL (production)
- **IA** : OpenAI API, spaCy, NLTK, Mistral
- **Cache** : Redis (optionnel)

## 🚀 **DÉMARRAGE RAPIDE**

### **Option 1 : Script automatique (Recommandé)**
```bash
cd "/Users/hamdi/5Twin4 Framework Python/EduKids"
./start.sh
```

### **Option 2 : Manuel**
```bash
# 1. Activer l'environnement virtuel
cd "/Users/hamdi/5Twin4 Framework Python"
source venv/bin/activate
cd EduKids

# 2. Installer Django
pip install Django==5.2.6

# 3. Créer les migrations
python manage.py makemigrations
python manage.py migrate

# 4. Créer un superutilisateur
python manage.py createsuperuser

# 5. Lancer le serveur
python manage.py runserver
```

### **Accès :**
- **Application** : http://localhost:8000
- **Admin Django** : http://localhost:8000/admin
- **Login** : admin / admin123

## 📁 **Structure du Projet**

```
EduKids/
├── EduKids/              # Configuration Django
├── students/             # Gestion utilisateurs (élèves, enseignants, parents)
├── exercises/            # Exercices et contenus éducatifs
├── assistant/            # Assistant virtuel IA
├── assessments/          # Évaluations et suivi des progrès
├── gamification/         # Badges, récompenses, défis
├── manage.py
├── db.sqlite3           # Base SQLite par défaut
└── README.md            # Ce fichier
```

## 🏗️ **Architecture des Applications**

### **students/** - Gestion des Utilisateurs
- `User` : Modèle utilisateur personnalisé
- `Student` : Profil élève avec niveau scolaire
- `Teacher` : Profil enseignant avec matières
- `Parent` : Profil parent avec enfants
- `Classroom` : Classes scolaires

### **exercises/** - Exercices et Contenus
- `Subject` : Matières (Français, Mathématiques, etc.)
- `Topic` : Thèmes par matière
- `Exercise` : Exercices avec 10+ types
- `Question` : Questions individuelles
- `Answer` : Réponses avec correction
- `ContentLibrary` : Bibliothèque de ressources

### **assistant/** - Assistant Virtuel IA
- `VirtualAssistant` : Configuration de l'IA
- `Conversation` : Conversations élèves/IA
- `Message` : Messages (texte, audio, image)
- `KnowledgeBase` : Base de connaissances
- `AssistantInteraction` : Historique d'apprentissage

### **assessments/** - Évaluations
- `Assessment` : Évaluations des exercices
- `StudentResponse` : Réponses des élèves
- `Progress` : Suivi des progrès
- `Report` : Rapports générés
- `Recommendation` : Recommandations IA

### **gamification/** - Motivation
- `Badge` : Badges à gagner
- `Reward` : Récompenses déblocables
- `Challenge` : Défis quotidiens/hebdomadaires
- `Leaderboard` : Classements
- `Notification` : Notifications de progression

## ⚙️ **Configuration PostgreSQL (Optionnel)**

### **Installation avec Docker (Recommandé)**
```bash
# Démarrer PostgreSQL + Redis + pgAdmin
docker-compose up -d

# Vérifier les services
docker-compose ps
```

**Services disponibles :**
- **PostgreSQL** : localhost:5432
- **Redis** : localhost:6379  
- **pgAdmin** : http://localhost:8080

### **Activer PostgreSQL dans Django**
Décommentez dans `EduKids/settings.py` :
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'edukids_db',
        'USER': 'postgres',
        'PASSWORD': 'edukids_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🔧 **Dépannage**

### **Erreurs Courantes :**

**"No module named 'students'"**
```bash
# Vérifier que vous êtes dans le bon dossier
pwd
# Devrait afficher : /Users/hamdi/5Twin4 Framework Python/EduKids
```

**"Port already in use"**
```bash
lsof -i :8000
kill -9 <PID>
```

**"Permission denied" sur les scripts**
```bash
chmod +x start.sh
```

### **Réinitialisation complète :**
```bash
# Supprimer la base
rm db.sqlite3

# Recréer les migrations
python manage.py makemigrations
python manage.py migrate

# Recréer le superutilisateur
python manage.py createsuperuser
```

## 📊 **Dépendances**

### **Dépendances de base (requises) :**
```bash
pip install Django==5.2.6
pip install Pillow==11.3.0
```

### **PostgreSQL (optionnel) :**
```bash
pip install psycopg2-binary==2.9.10
```

### **IA et NLP (optionnel) :**
```bash
pip install openai==1.54.5
pip install spacy>=3.8.7
pip install nltk==3.9.1
pip install scikit-learn==1.6.1
```

## 🎯 **Prochaines Étapes**

### **Phase 1 : Configuration Admin Django**
- Créer les ModelAdmin pour chaque application
- Personnaliser l'interface d'administration
- Ajouter des filtres et recherches

### **Phase 2 : Interface Utilisateur**
- Créer les templates Django
- Interface pour élèves, enseignants, parents
- Dashboard avec Bootstrap 5

### **Phase 3 : Intégration IA**
- Connecter OpenAI API
- Implémenter l'assistant virtuel
- Générateur d'exercices automatique

### **Phase 4 : Tests et Déploiement**
- Tests unitaires
- Tests d'intégration
- Déploiement sur serveur

## 📈 **Statistiques du Projet**

- **31 models Django** au total
- **5 applications** spécialisées
- **200+ champs** et relations
- **10+ types d'exercices** différents
- **Système de gamification** complet

## 🎓 **Alignement avec le Sujet**

✅ **Hub Éducatif Multimodal** - Plateforme complète
✅ **Assistant Virtuel** - Module assistant/ 
✅ **Coaching** - Recommandations personnalisées
✅ **Évaluation** - Suivi des progrès
✅ **Génération d'Exercices** - IA automatique
✅ **Public Primaire** - CP à CM2
✅ **100% Django** - Framework principal

---

## 🚀 **Prêt à Démarrer !**

Votre projet EduKids est **parfaitement structuré** et prêt pour le développement !

**Commencez par :**
1. Lancer `./start.sh`
2. Aller sur http://localhost:8000/admin
3. Explorer les modèles créés
4. Commencer le développement de l'interface

**Bon développement sur EduKids !** 🎯✨
