@echo off
echo 🚀 Démarrage d'EduKids...
cd /d "%~dp0"

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou n'est pas dans le PATH
    pause
    exit /b 1
)

REM Vérifier si l'environnement virtuel existe
if not exist "venv" (
    echo ❌ Environnement virtuel non trouvé. Création en cours...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Erreur lors de la création de l'environnement virtuel
        pause
        exit /b 1
    )
    echo ✅ Environnement virtuel créé.
)

REM Activer l'environnement virtuel
call venv\Scripts\activate
if errorlevel 1 (
    echo ❌ Erreur lors de l'activation de l'environnement virtuel
    pause
    exit /b 1
)

REM Mettre à jour pip
echo 📦 Mise à jour de pip...
python -m pip install --upgrade pip

REM Installer les dépendances
echo 📦 Installation des dépendances...
pip install -r requirements.txt
if errorlevel 1 (
    echo ⚠️  Erreur lors de l'installation des dépendances, tentative alternative...
    echo 📦 Installation manuelle des dépendances principales...
    pip install Django==5.2.6 djangorestframework==3.15.2 spacy>=3.8.7 nltk==3.9.1
    pip install crispy-bootstrap5
)

REM Créer les migrations si nécessaire
echo 🔄 Création des migrations...
python manage.py makemigrations
python manage.py migrate

REM Vérifier si la commande seed existe
echo 👥 Vérification de la création des utilisateurs...
python manage.py seed >nul 2>&1
if errorlevel 1 (
    echo ℹ️  Commande 'seed' non trouvée, création du superutilisateur...
    echo.
    echo 👑 Création du compte administrateur:
    python manage.py createsuperuser
)

REM Télécharger le modèle spaCy
echo 🔄 Téléchargement du modèle spaCy...
python -m spacy download fr_core_news_sm

REM Lancer le serveur
echo.
echo ✅ EduKids est prêt !
echo 🌐 Application: http://localhost:8000
echo 👑 Admin: http://localhost:8000/admin
echo.
echo Appuyez sur Ctrl+C pour arrêter le serveur
echo.
python manage.py runserver

pause