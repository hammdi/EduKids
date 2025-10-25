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

### **🪟 Windows**

#### **Prérequis Windows :**
- **Python 3.11+** : [Télécharger depuis python.org](https://www.python.org/downloads/)
- **Git** : [Télécharger Git for Windows](https://git-scm.com/download/win)
- **Docker Desktop** (optionnel) : [Télécharger Docker Desktop](https://www.docker.com/products/docker-desktop/)

#### **Installation Windows :**
```cmd
# 1. Ouvrir PowerShell ou CMD en tant qu'administrateur
# 2. Naviguer vers le projet
cd "C:\Users\VotreNom\5Twin4 Framework Python\EduKids"

# 3. Créer l'environnement virtuel
python -m venv venv

# 4. Activer l'environnement virtuel
venv\Scripts\activate

# 5. Installer les dépendances
pip install -r requirements.txt

# 6. Créer les migrations
python manage.py makemigrations
python manage.py migrate

# 7. Créer les utilisateurs de test
python manage.py seed

# 8. Lancer le serveur
python manage.py runserver
```

#### **Script automatique Windows :**
```cmd
# Créer start.bat dans le dossier EduKids
@echo off
echo 🚀 Démarrage d'EduKids...
cd /d "%~dp0"
call venv\Scripts\activate
python manage.py runserver
pause
```

### **🍎 macOS / 🐧 Linux**

#### **Option 1 : Script automatique (Recommandé)**
```bash
cd "/Users/hamdi/5Twin4 Framework Python/EduKids"
./start.sh
```

#### **Option 2 : Manuel**
```bash
# 1. Activer l'environnement virtuel
cd "/Users/hamdi/5Twin4 Framework Python"
source venv/bin/activate
cd EduKids

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Créer les migrations
python manage.py makemigrations
python manage.py migrate

# 4. Créer les utilisateurs de test
python manage.py seed

# 5. Lancer le serveur
python manage.py runserver
```

### **Accès :**
- **Application** : http://localhost:8000
- **Admin Django** : http://localhost:8000/admin
- **Login** : http://localhost:8000/login
- **Registration** : http://localhost:8000/register

### **🔑 Comptes de Test :**
| Rôle | Utilisateur | Mot de passe | Accès |
|------|-------------|--------------|-------|
| 👑 **Admin** | `admin` | `admin123` | Tout + Admin Django |
| 👨‍🏫 **Enseignant** | `teacher` | `teacher123` | Dashboard enseignant |
| 🎓 **Élève** | `student` | `student123` | Dashboard élève |

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

## 👥 **Gestion des Utilisateurs**

### **🔐 Authentification**
- **Inscription** : Choix du rôle (Élève/Enseignant)
- **Connexion** : Authentification sécurisée
- **Profils** : Gestion complète des informations utilisateur
- **Déconnexion** : Sécurisée avec redirection

### **🎯 Rôles et Permissions**
- **👑 Administrateur** : Accès complet + Admin Django
- **👨‍🏫 Enseignant** : Gestion des classes et évaluations
- **🎓 Élève** : Accès aux exercices et progression

### **📊 Interface d'Administration**
- **Gestion des utilisateurs** : CRUD complet
- **Statistiques** : Nombre d'utilisateurs par rôle
- **Modération** : Activation/désactivation des comptes
- **Import/Export** : Gestion en masse des utilisateurs

## ⚙️ **Configuration PostgreSQL (Optionnel)**

### **🪟 Windows avec Docker Desktop**

#### **Installation Docker Desktop :**
1. Télécharger [Docker Desktop pour Windows](https://www.docker.com/products/docker-desktop/)
2. Installer et redémarrer l'ordinateur
3. Démarrer Docker Desktop

#### **Démarrage des services :**
```cmd
# Dans PowerShell ou CMD
cd "C:\Users\VotreNom\5Twin4 Framework Python\EduKids"
docker-compose up -d
docker-compose ps
```

### **🍎 macOS / 🐧 Linux avec Docker**

#### **Installation Docker :**
```bash
# macOS (avec Homebrew)
brew install docker

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install docker.io docker-compose
```

#### **Démarrage des services :**
```bash
# Démarrer PostgreSQL + Redis + pgAdmin
docker-compose up -d

# Vérifier les services
docker-compose ps
```

### **Services disponibles :**
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

### **🪟 Erreurs Windows :**

**"Python n'est pas reconnu"**
```cmd
# Ajouter Python au PATH ou utiliser le chemin complet
C:\Python311\python.exe -m venv venv
```

**"Port already in use"**
```cmd
# Trouver le processus utilisant le port 8000
netstat -ano | findstr :8000
# Tuer le processus (remplacer PID par le numéro affiché)
taskkill /PID <PID> /F
```

**"Permission denied" sur les scripts**
```cmd
# Exécuter PowerShell en tant qu'administrateur
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **🍎 macOS / 🐧 Linux - Erreurs Courantes :**

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

#### **🪟 Windows :**
```cmd
# Supprimer la base
del db.sqlite3

# Recréer les migrations
python manage.py makemigrations
python manage.py migrate

# Recréer les utilisateurs de test
python manage.py seed
```

#### **🍎 macOS / 🐧 Linux :**
```bash
# Supprimer la base
rm db.sqlite3

# Recréer les migrations
python manage.py makemigrations
python manage.py migrate

# Recréer les utilisateurs de test
python manage.py seed
```

## 📊 **Dépendances**

### **🪟 Windows :**
```cmd
# Activer l'environnement virtuel
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### **🍎 macOS / 🐧 Linux :**
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### **Dépendances principales :**
- **Django 5.2.6** : Framework web principal
- **Pillow 11.3.0** : Gestion des images
- **crispy-forms** : Formulaires stylisés
- **crispy-bootstrap5** : Interface Bootstrap 5

### **Base de données :**
- **psycopg2-binary** : PostgreSQL (optionnel)
- **django-redis** : Cache Redis (optionnel)

### **IA et Analyse vocale :**
- **openai** : API OpenAI pour l'assistant
- **spacy** : Traitement du langage naturel
- **librosa** : Analyse audio pour évaluation vocale
- **textblob** : Analyse de sentiment
- **scikit-learn** : Machine learning

### **Développement :**
- **django-debug-toolbar** : Debug en développement
- **pytest-django** : Tests automatisés
- **black, flake8** : Formatage et qualité du code
```

## 🧪 **Test du Système**

### **🔐 Test de l'Authentification**
1. **Accéder à** : http://localhost:8000/
2. **Tester l'inscription** : http://localhost:8000/register/
3. **Tester la connexion** : http://localhost:8000/login/
4. **Tester le profil** : http://localhost:8000/profile/

### **👥 Test des Rôles**
- **Admin** : Accès complet + interface admin Django
- **Enseignant** : Dashboard enseignant + gestion des classes
- **Élève** : Dashboard élève + exercices

### **📊 Test de l'Administration**
- **Gestion utilisateurs** : http://localhost:8000/admin/users/
- **Interface Django** : http://localhost:8000/admin/
- **CRUD complet** : Créer, modifier, supprimer des utilisateurs

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

### **🪟 Windows :**
**Commencez par :**
1. Ouvrir PowerShell en tant qu'administrateur
2. Naviguer vers le projet : `cd "C:\Users\VotreNom\5Twin4 Framework Python\EduKids"`
3. Activer l'environnement : `venv\Scripts\activate`
4. Lancer le serveur : `python manage.py runserver`
5. Aller sur http://localhost:8000/admin

### **🍎 macOS / 🐧 Linux :**
**Commencez par :**
1. Lancer `./start.sh`
2. Aller sur http://localhost:8000/admin
3. Explorer les modèles créés
4. Commencer le développement de l'interface

**Bon développement sur EduKids !** 🎯✨
