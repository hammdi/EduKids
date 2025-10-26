Configuration Mistral pour EduKids

But
----
Permettre à l'application Django de lire automatiquement la clé MISTRAL_API_KEY
quand vous lancez `python manage.py runserver` depuis votre environnement virtuel
(sans Docker, sans autres commandes additionnelles).

Étapes
------
1. Créez un fichier `.env` à la racine du projet (même dossier que `manage.py`).
   Vous pouvez copier l'exemple fourni :

   ```powershell
   copy .env.example .env
   ```

2. Ouvrez `.env` et remplacez la valeur de `MISTRAL_API_KEY` par votre clé réelle :

   ```text
   MISTRAL_API_KEY=sk_...votre_cle...
   ```

3. Lancez votre serveur (depuis l'environnement virtuel) :

   ```powershell
   (venv) PS C:\Users\hadid\Downloads\ahmed\EduKids\Edukids> python manage.py runserver
   ```

Ce que fait le code
-------------------
- `EduKids/settings.py` charge automatiquement le fichier `.env` (via `python-dotenv`) au
  démarrage. Ainsi `os.environ.get('MISTRAL_API_KEY')` dans `assistant/mistral_client.py`
  retournera la valeur fournie dans `.env` sans autre action.

Vérification rapide
------------------
- Dans PowerShell (même session), vous pouvez vérifier que la variable est bien lue par Python :

  ```powershell
  python -c "import os; print('MISTRAL_API_KEY=', os.environ.get('MISTRAL_API_KEY'))"
  ```

- Après avoir redémarré le serveur, surveillez les logs : l'erreur `MISTRAL_API_KEY not set in environment`
  devrait disparaître et l'assistant pourra appeler l'API Mistral.

Sécurité
--------
- Ne commitez jamais votre `.env` contenant la clé réelle. Utilisez `.env.example` pour partager la structure.
- En production, préférez des variables d'environnement du système ou un secret manager.
