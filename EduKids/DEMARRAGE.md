# Guide de démarrage EduKids

## 🚀 Démarrer le serveur avec support WebSocket

### Méthode recommandée (utilise Daphne pour WebSocket)

Depuis le dossier `Edukids`, lancez le script PowerShell :

```powershell
.\start_server.ps1
```

Ce script :
- Configure automatiquement la clé API Mistral
- Arrête tout serveur existant sur le port 8000
- Lance Daphne (serveur ASGI) qui supporte les WebSockets
- Affiche les URLs d'accès

### Alternative manuelle

Si vous préférez lancer manuellement :

```powershell
# 1. Activer le venv (si pas déjà fait)
cd C:\Users\hadid\Downloads\ahmed\EduKids
.\venv\Scripts\Activate.ps1

# 2. Aller dans le dossier du projet
cd Edukids

# 3. Configurer la clé Mistral
$env:MISTRAL_API_KEY = '2WC2TOx7fBperEqMgasE390GYC0Isenq'

# 4. Lancer Daphne (PAS python manage.py runserver)
python -m daphne -b 127.0.0.1 -p 8000 EduKids.asgi:application
```

## ⚠️ Important

**NE PAS utiliser `python manage.py runserver`** pour l'assistant virtuel car il ne supporte pas les WebSockets.

Utilisez toujours :
- Le script `start_server.ps1` (recommandé)
- OU la commande `python -m daphne -b 127.0.0.1 -p 8000 EduKids.asgi:application`

## 🔍 Vérification

Une fois le serveur démarré, ouvrez http://127.0.0.1:8000 dans votre navigateur.

Pour tester le WebSocket :
1. Connectez-vous avec un compte utilisateur
2. Allez sur la page d'exercices ou du chat assistant
3. Ouvrez la console du navigateur (F12)
4. Vous devriez voir "Connecté à l'assistant…" au lieu de "Déconnecté"

## 🐛 Résolution de problèmes

### Le port 8000 est déjà utilisé

```powershell
# Trouver le processus
Get-NetTCPConnection -LocalPort 8000

# Tuer le processus (remplacez XXXX par l'ID du processus)
Stop-Process -Id XXXX -Force
```

### "Student profile not found"

L'utilisateur doit avoir un profil Student dans la base de données :

1. Allez sur http://127.0.0.1:8000/admin/
2. Connectez-vous
3. Allez dans "Élèves" → "Ajouter un élève"
4. Sélectionnez l'utilisateur, remplissez les champs requis (grade_level, birth_date)
5. Enregistrez

## 📝 Fichiers modifiés pour le WebSocket

- `assistant/consumers.py` : Consumer WebSocket avec streaming en temps réel
- `assistant/mistral_client.py` : Client pour l'API Mistral
- `assistant/routing.py` : Configuration des routes WebSocket
- `EduKids/asgi.py` : Configuration ASGI
- `static/js/assistant_chat.js` : Client WebSocket avec reconnexion automatique
- `assistant/templates/assistant/chat.html` : Injection automatique du student_id
