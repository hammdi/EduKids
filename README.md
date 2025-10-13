# EduKids - Hub Éducatif Multimodal

## 🎓 Description

**EduKids** est une plateforme éducative intelligente développée avec Django, dédiée à l'enseignement primaire (élèves de 6 à 12 ans). Elle intègre un assistant virtuel IA, un générateur automatique d'exercices, un système d'évaluation adaptatif et un module de gamification pour motiver les élèves.

### Thématique
Hub Éducatif ou Créatif Multimodal : Assistant Virtuel pour l'Éducation, le Coaching et l'Évaluation avec Génération Automatique d'Exercices

## ✨ Fonctionnalités Principales

### 🤖 Assistant Virtuel Intelligent
- Réponses contextuelles adaptées aux enfants de 6-12 ans
- Support multilingue
- Interface conversationnelle naturelle
- Disponibilité 24/7

### 📝 Générateur Automatique d'Exercices
- Création d'exercices adaptés au niveau de l'élève
- Support de multiples formats : QCM, texte à trous, dictées, problèmes mathématiques
- Adaptation continue de la difficulté basée sur les performances
- Alignement avec le programme officiel français

### 📊 Système d'Évaluation Intelligente
- Correction automatique avec feedback personnalisé
- **🎤 Évaluation vocale par IA** (Innovation scientifique)
  - Analyse de l'originalité des idées
  - Évaluation de la communication verbale (structure, fluidité, vocabulaire)
  - Analyse paraverbale (intonation, rythme, temporalité)
- Analyse des patterns d'erreurs
- Recommandations basées sur l'IA
- Suivi détaillé des progrès

### 🎮 Gamification
- Système de points et niveaux
- Badges et récompenses à débloquer
- Défis quotidiens et hebdomadaires
- Classements amicaux
- Avatars personnalisables

## 🏗️ Architecture

### Structure du Projet

```
EduKids/
├── students/          # Gestion des utilisateurs (élèves, enseignants, parents)
├── exercises/         # Exercices, questions, matières
├── assistant/         # Assistant virtuel et conversations
├── assessments/       # Évaluations et suivi des progrès
├── gamification/      # Badges, récompenses, défis
└── EduKids/          # Configuration principale Django
```

### Stack Technologique

**Backend:**
- Django 5.2.6
- Django REST Framework
- PostgreSQL
- Redis (cache & Celery)

**IA & Machine Learning:**
- OpenAI API
- spaCy (NLP)
- NLTK
- scikit-learn
- Mistral
**Traitement Asynchrone:**
- Celery
- Redis

**Frontend:**
- Django Templates
- Bootstrap 5
- JavaScript/AJAX
- Chart.js (graphiques)

## 🚀 Installation

### Prérequis
- Python 3.13+
- PostgreSQL
- Redis

### Étapes d'installation

1. **Cloner le repository**
```bash
cd "/Users/hamdi/5Twin4 Framework Python"
```

2. **Créer et activer l'environnement virtuel**
```bash
source venv/bin/activate  # Sur macOS/Linux
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration de la base de données**
```bash
cd EduKids
python manage.py makemigrations
python manage.py migrate
```

5. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

6. **Télécharger les modèles spaCy**
```bash
python -m spacy download fr_core_news_sm
```

7. **Lancer le serveur de développement**
```bash
python manage.py runserver
```

8. **Accéder à l'application**
- Application: http://localhost:8000
- Admin Django: http://localhost:8000/admin

## 📱 Public Cible

### Élèves du Primaire (6-12 ans)
- **CP-CE1** (6-8 ans) : Apprentissage de la lecture, calcul de base
- **CE2-CM1** (8-10 ans) : Consolidation des fondamentaux
- **CM2** (10-12 ans) : Préparation au collège

### Enseignants
- Gain de temps sur la correction et la préparation
- Outils d'analyse et de suivi
- Génération automatique d'exercices

### Parents
- Suivi des progrès de leurs enfants
- Outils pour l'aide aux devoirs
- Communication avec les enseignants

## 🎤 **Innovation : Évaluation Vocale par IA**

### **Contribution Scientifique Unique**

EduKids intègre un système innovant d'**évaluation automatique des productions orales** des élèves, basé sur l'intelligence artificielle et l'analyse acoustique.

#### **Critères d'Évaluation Multidimensionnels :**

**1. Originalité de l'Idée (30%)**
- Détection de mots-clés uniques
- Analyse de la diversité lexicale (Type-Token Ratio)
- Identification de concepts innovants
- Mesure des connexions créatives

**2. Communication Verbale (40%)**
- **Structure** (15%): Organisation, cohérence, connecteurs logiques
- **Fluidité** (15%): Hésitations, répétitions, faux départs
- **Vocabulaire** (10%): Richesse lexicale, complexité des mots

**3. Communication Paraverbale (30%)**
- **Intonation** (12%): Variation tonale via ponctuation détectée
- **Rythme** (10%): Débit de parole (mots/minute)
- **Temporalité** (8%): Pauses et segments temporels

#### **Technologies Utilisées :**
- **Speech-to-Text**: OpenAI Whisper / Google Speech API
- **Analyse Audio**: Librosa, Praat-Parselmouth
- **NLP**: spaCy, NLTK, TextBlob
- **Traitement Signal**: SciPy, Python Speech Features

#### **Applications Pédagogiques :**
- Évaluation objective des présentations orales
- Feedback immédiat et personnalisé
- Suivi de la progression en expression orale
- Détection précoce de difficultés d'élocution

---

## 🎯 Modules Principaux

### 1. Students (Utilisateurs)
- Gestion des élèves, enseignants, parents
- Profils personnalisés
- Classes et groupes

### 2. Exercises (Exercices)
- Matières et thèmes
- Questions et réponses
- Bibliothèque de contenus
- 10+ types d'exercices différents

### 3. Assistant (Assistant Virtuel)
- Conversations intelligentes
- Base de connaissances
- Historique des interactions
- Apprentissage continu

### 4. Assessments (Évaluations)
- Correction automatique
- Suivi des progrès par matière
- Rapports détaillés
- Recommandations personnalisées

### 5. Gamification (Motivation)
- Badges et accomplissements
- Récompenses déblocables
- Défis quotidiens/hebdomadaires
- Classements et compétitions amicales
- Notifications de progression

## 📊 Modèles de Données

### Modèles Principaux

**Students:**
- User (utilisateur personnalisé)
- Student (élève)
- Teacher (enseignant)
- Parent
- Classroom (classe)

**Exercises:**
- Subject (matière)
- Topic (thème)
- Exercise
- Question
- Answer
- ContentLibrary

**Assistant:**
- VirtualAssistant
- Conversation
- Message
- KnowledgeBase
- AssistantInteraction

**Assessments:**
- Assessment (évaluation)
- StudentResponse
- Progress
- Report
- Recommendation

**Gamification:**
- Badge
- StudentBadge
- Reward
- Challenge
- Leaderboard
- Notification

## 🔐 Sécurité

- Authentification Django intégrée
- Protection CSRF
- Validation des entrées
- Chiffrement des mots de passe
- Conformité RGPD pour les données des enfants

## 📈 Roadmap

### Phase 1 (Actuelle)
- ✅ Structure du projet Django
- ✅ Modèles de données
- ✅ Applications de base
- 🔄 Interface admin Django

### Phase 2 (Prochaine)
- Interface web responsive
- Intégration de l'IA OpenAI
- Générateur d'exercices basique
- Système d'évaluation

### Phase 3
- Analytics avancés
- Recommandations intelligentes
- Application mobile (React Native)
- Tests utilisateurs

### Phase 4
- Réalité augmentée
- Gamification avancée
- Intégration avec systèmes scolaires
- Déploiement en production

## 👥 Contributeurs

Projet développé dans le cadre du framework Python 5Twin4

## 📄 License

Ce projet est développé à des fins éducatives.

## 🤝 Support

Pour toute question ou suggestion, veuillez ouvrir une issue sur le repository.

---

**EduKids** - Révolutionner l'apprentissage au primaire avec l'intelligence artificielle 🚀

