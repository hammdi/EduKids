@echo off
echo 🚀 Démarrage d'EduKids...
cd /d "%~dp0"

REM Vérifier si l'environnement virtuel existe
if not exist "venv" (
    echo ❌ Environnement virtuel non trouvé. Création en cours...
    python -m venv venv
    echo ✅ Environnement virtuel créé.
)

REM Activer l'environnement virtuel
call venv\Scripts\activate

REM Installer les dépendances si nécessaire
echo 📦 Vérification des dépendances...
pip install -r requirements.txt

REM Créer les migrations si nécessaire
echo 🔄 Création des migrations...
python manage.py makemigrations
python manage.py migrate

REM Créer les utilisateurs de test
echo 👥 Création des utilisateurs de test...
python manage.py seed

REM Lancer le serveur
echo 🌐 Lancement du serveur...
echo.
echo ✅ EduKids est prêt !
echo 🌐 Application: http://localhost:8000
echo 👑 Admin: http://localhost:8000/admin
echo.
echo Appuyez sur Ctrl+C pour arrêter le serveur
echo.
python manage.py runserver

pause
