# ✅ Checklist Tests - Gamification Student Space

## 🔐 Sécurité & Permissions

### Test 1 : Vérification du rôle Student
- [ ] Se connecter en tant qu'admin → Accéder à `/student/dashboard/`
  - **Attendu** : Redirection vers `/` avec message "Cette page est réservée aux élèves uniquement."
- [ ] Se connecter en tant que teacher → Accéder à `/student/customize/`
  - **Attendu** : Redirection vers `/` avec message d'erreur
- [ ] Se connecter en tant que student → Accéder à `/student/dashboard/`
  - **Attendu** : Affichage du dashboard

### Test 2 : Authentification requise
- [ ] Sans connexion → Accéder à `/student/store/`
  - **Attendu** : Redirection vers `/login/` avec message "Connecte-toi pour accéder à ton espace !"

### Test 3 : Profil student_profile requis
- [ ] Créer un User avec user_type='student' SANS profil Student
- [ ] Se connecter et accéder à `/student/dashboard/`
  - **Attendu** : Message "Aucun profil élève trouvé. Contacte un administrateur."

---

## 🎮 Dashboard Student (`/student/dashboard/`)

### Test 4 : Affichage des stats
- [ ] Vérifier l'affichage du nombre de points
- [ ] Vérifier l'affichage du nombre de badges
- [ ] Vérifier l'affichage du nombre de missions complétées
- [ ] Vérifier la barre de progression du niveau

### Test 5 : Affichage de l'avatar
- [ ] Student SANS avatar uploadé
  - **Attendu** : Placeholder emoji 🎓
- [ ] Student AVEC avatar uploadé
  - **Attendu** : Image affichée (120x120px, rond)

### Test 6 : Accessoires équipés
- [ ] Student sans accessoires
  - **Attendu** : Section non affichée
- [ ] Student avec accessoires équipés
  - **Attendu** : Liste des accessoires affichée

### Test 7 : Missions actives
- [ ] Student avec missions en cours
  - **Attendu** : Affichage des 3 premières missions avec progression

### Test 8 : Badges récents
- [ ] Student avec badges
  - **Attendu** : Affichage des 5 derniers badges avec icônes

### Test 9 : Actions rapides
- [ ] Cliquer sur "Boutique"
  - **Attendu** : Redirection vers `/student/store/`
- [ ] Cliquer sur "Personnaliser"
  - **Attendu** : Redirection vers `/student/customize/`

---

## 🎨 Personnalisation Avatar (`/student/customize/`)

### Test 10 : Upload avatar - Drag & Drop
- [ ] Glisser une image JPG valide (< 2MB)
  - **Attendu** : Preview instantanée affichée
- [ ] Glisser une image PNG valide
  - **Attendu** : Preview instantanée affichée

### Test 11 : Upload avatar - Click
- [ ] Cliquer sur la zone d'upload
  - **Attendu** : Sélecteur de fichier s'ouvre
- [ ] Sélectionner une image valide
  - **Attendu** : Preview instantanée

### Test 12 : Validation fichier - Taille
- [ ] Sélectionner une image > 2MB
  - **Attendu** : Message "❌ Fichier trop volumineux. Maximum 2MB."
  - **Attendu** : Bouton "Uploader" désactivé

### Test 13 : Validation fichier - Format
- [ ] Sélectionner un fichier .gif
  - **Attendu** : Message "❌ Format non autorisé. Utilise JPG ou PNG."
- [ ] Sélectionner un fichier .bmp
  - **Attendu** : Message d'erreur format

### Test 14 : Upload réussi
- [ ] Uploader une image valide
  - **Attendu** : Toast "🎉 Super ! Ton avatar a été mis à jour avec succès !"
  - **Attendu** : Animation confetti
  - **Attendu** : Aperçu principal mis à jour SANS refresh
  - **Attendu** : Preview temporaire disparaît

### Test 15 : Équiper un accessoire
- [ ] Cliquer sur "Équiper" pour un accessoire possédé
  - **Attendu** : Toast "✨ Accessoire équipé avec succès !"
  - **Attendu** : Animation confetti
  - **Attendu** : Bouton devient "✓ Équipé"
  - **Attendu** : Carte accessoire marquée comme équipée

### Test 16 : Déséquiper un accessoire
- [ ] Cliquer sur "Retirer" pour un accessoire équipé
  - **Attendu** : Toast "Accessoire retiré."
  - **Attendu** : Page rechargée
  - **Attendu** : Accessoire redevient "Équiper"

### Test 17 : Slot unique par type
- [ ] Équiper un chapeau
- [ ] Équiper un autre chapeau
  - **Attendu** : Premier chapeau automatiquement déséquipé
  - **Attendu** : Un seul chapeau équipé à la fois

### Test 18 : Aucun accessoire possédé
- [ ] Student sans accessoires
  - **Attendu** : Message "Tu n'as pas encore d'accessoires."
  - **Attendu** : Bouton "Aller à la boutique"

---

## 🛍️ Boutique (`/student/store/`)

### Test 19 : Affichage des points
- [ ] Vérifier l'affichage du solde de points en haut
  - **Attendu** : Nombre correct de points

### Test 20 : Catalogue d'accessoires
- [ ] Vérifier l'affichage de tous les accessoires actifs
- [ ] Vérifier l'affichage du prix de chaque accessoire
- [ ] Vérifier l'affichage de la description

### Test 21 : Accessoire déjà possédé
- [ ] Accessoire déjà acheté
  - **Attendu** : Badge "✓ Déjà possédé"
  - **Attendu** : Pas de bouton "Acheter"
  - **Attendu** : Carte avec fond vert

### Test 22 : Points suffisants
- [ ] Accessoire avec prix < points disponibles
  - **Attendu** : Bouton "Acheter" actif
  - **Attendu** : Pas de message d'insuffisance

### Test 23 : Points insuffisants
- [ ] Accessoire avec prix > points disponibles
  - **Attendu** : Bouton "Points insuffisants" désactivé
  - **Attendu** : Message "Continue à apprendre ! Il te faut encore X points."

### Test 24 : Achat réussi
- [ ] Cliquer sur "Acheter" (avec points suffisants)
- [ ] Confirmer l'achat dans la popup
  - **Attendu** : Toast "🎉 Bravo ! Tu as débloqué..."
  - **Attendu** : Animation confetti
  - **Attendu** : Points décrémentés dynamiquement (sans refresh)
  - **Attendu** : Bouton devient "✓ Déjà possédé"
  - **Attendu** : Carte devient verte

### Test 25 : Achat annulé
- [ ] Cliquer sur "Acheter"
- [ ] Annuler dans la popup de confirmation
  - **Attendu** : Aucun achat effectué
  - **Attendu** : Points inchangés

### Test 26 : Achat avec points insuffisants (bypass client)
- [ ] Modifier le DOM pour activer le bouton
- [ ] Cliquer sur "Acheter"
  - **Attendu** : Toast "💰 Continue à apprendre ! Il te faut encore X points."
  - **Attendu** : Aucun achat effectué (validation backend)

### Test 27 : Boutique vide
- [ ] Désactiver tous les accessoires dans l'admin
- [ ] Accéder à `/student/store/`
  - **Attendu** : Message "La boutique est vide pour le moment"

---

## 👤 Profil Gamification (`/student/profile/gamification/`)

### Test 28 : Affichage des badges
- [ ] Student avec badges
  - **Attendu** : Grille de badges avec icônes et dates

### Test 29 : Affichage des missions
- [ ] Student avec missions
  - **Attendu** : Liste des missions avec statut
  - **Attendu** : Missions terminées en vert

### Test 30 : Compteur d'accessoires
- [ ] Vérifier le nombre total d'accessoires possédés
  - **Attendu** : Nombre correct affiché

---

## 🎯 UX & Animations

### Test 31 : Toasts
- [ ] Vérifier que les toasts apparaissent en haut à droite
- [ ] Vérifier l'animation slideIn
- [ ] Vérifier l'auto-dismiss après 5 secondes
- [ ] Vérifier le bouton de fermeture manuel

### Test 32 : Confetti
- [ ] Upload avatar réussi
  - **Attendu** : Animation confetti
- [ ] Achat accessoire réussi
  - **Attendu** : Animation confetti
- [ ] Équipement accessoire
  - **Attendu** : Animation confetti

### Test 33 : Responsive
- [ ] Tester sur mobile (< 768px)
  - **Attendu** : Layout adapté, cartes empilées
- [ ] Tester sur tablette (768px - 1024px)
  - **Attendu** : Layout 2 colonnes
- [ ] Tester sur desktop (> 1024px)
  - **Attendu** : Layout complet

### Test 34 : Navigation
- [ ] Vérifier tous les liens "Retour au Dashboard"
- [ ] Vérifier les liens dans les actions rapides
- [ ] Vérifier la navigation entre les pages

---

## 🔌 API Endpoints

### Test 35 : Upload avatar API
```bash
POST /gamification/api/avatars/my-avatar/upload_image/
Content-Type: multipart/form-data
Body: image=<file>
```
- [ ] Avec image valide
  - **Attendu** : 200, `{"image_url": "..."}`
- [ ] Sans image
  - **Attendu** : 400, `{"error": "Image requise"}`
- [ ] Image > 2MB
  - **Attendu** : 400, `{"error": "Fichier trop volumineux..."}`
- [ ] Format invalide
  - **Attendu** : 400, `{"error": "Format non autorisé..."}`

### Test 36 : Achat accessoire API
```bash
POST /gamification/api/user-accessories/
Content-Type: application/json
Body: {"accessory": <id>}
```
- [ ] Avec points suffisants
  - **Attendu** : 201, objet UserAccessory créé
- [ ] Points insuffisants
  - **Attendu** : 400, `{"error": "Points insuffisants..."}`
- [ ] Accessoire déjà possédé
  - **Attendu** : 400, `{"error": "Tu possèdes déjà..."}`

### Test 37 : Équiper accessoire API
```bash
POST /gamification/api/avatars/my-avatar/equip_accessory/
Content-Type: application/json
Body: {"accessory_id": <id>}
```
- [ ] Accessoire possédé
  - **Attendu** : 200, avatar mis à jour
- [ ] Accessoire non possédé
  - **Attendu** : 403, `{"error": "Accessoire non possédé"}`

### Test 38 : Déséquiper accessoire API
```bash
POST /gamification/api/avatars/my-avatar/unequip_accessory/
Content-Type: application/json
Body: {"accessory_id": <id>}
```
- [ ] Accessoire équipé
  - **Attendu** : 200, accessoire déséquipé
- [ ] Accessoire non équipé
  - **Attendu** : 403, `{"error": "Accessoire non équipé"}`

---

## 🐛 Tests de régression

### Test 39 : Admins ne voient pas la gamification
- [ ] Se connecter en tant qu'admin
- [ ] Vérifier qu'aucun lien gamification n'apparaît dans la navbar
- [ ] Tenter d'accéder manuellement aux URLs
  - **Attendu** : Redirection systématique

### Test 40 : Teachers ne voient pas la gamification
- [ ] Se connecter en tant que teacher
- [ ] Vérifier l'absence de liens gamification
- [ ] Tenter d'accéder aux URLs
  - **Attendu** : Redirection

### Test 41 : Isolation des données
- [ ] Créer 2 students (A et B)
- [ ] Student A achète un accessoire
- [ ] Se connecter en tant que Student B
  - **Attendu** : Student B ne voit PAS l'accessoire de A comme possédé

### Test 42 : Concurrence (2 achats simultanés)
- [ ] Student avec 100 points
- [ ] Ouvrir 2 onglets
- [ ] Acheter un accessoire à 60 points dans chaque onglet simultanément
  - **Attendu** : Un seul achat réussit (validation backend)

---

## 📊 Performance

### Test 43 : Temps de chargement
- [ ] Dashboard avec 50 badges
  - **Attendu** : < 2 secondes
- [ ] Boutique avec 100 accessoires
  - **Attendu** : < 2 secondes

### Test 44 : Requêtes DB
- [ ] Activer Django Debug Toolbar
- [ ] Charger le dashboard
  - **Attendu** : < 20 requêtes SQL (utilisation de select_related/prefetch_related)

---

## 🎨 Accessibilité

### Test 45 : Contraste des couleurs
- [ ] Vérifier le contraste texte/fond (WCAG AA)
- [ ] Vérifier la lisibilité sur fond coloré

### Test 46 : Navigation clavier
- [ ] Naviguer avec Tab
  - **Attendu** : Tous les boutons/liens accessibles
- [ ] Activer avec Entrée/Espace
  - **Attendu** : Actions déclenchées

---

## 📱 Tests navigateurs

### Test 47 : Chrome
- [ ] Toutes les fonctionnalités

### Test 48 : Firefox
- [ ] Toutes les fonctionnalités

### Test 49 : Safari
- [ ] Toutes les fonctionnalités

### Test 50 : Edge
- [ ] Toutes les fonctionnalités

---

## ✅ Résumé

**Total tests** : 50  
**Tests passés** : ___  
**Tests échoués** : ___  
**Bloquants** : ___  

**Date des tests** : ___________  
**Testeur** : ___________  
**Environnement** : ___________

---

## 🚀 Commandes utiles

### Créer un student de test
```python
python manage.py shell

from users.models import User
from students.models import Student

user = User.objects.create_user(
    username='student_test',
    email='student@test.com',
    password='test123',
    user_type='student',
    first_name='Test',
    last_name='Student'
)

student = Student.objects.create(
    user=user,
    grade_level='CE2',
    total_points=500
)
```

### Créer des accessoires
```python
from gamification.models import Accessory

Accessory.objects.create(
    name='Chapeau de pirate',
    accessory_type='hat',
    points_required=100,
    description='Un super chapeau de pirate !',
    is_active=True
)
```

### Donner des points
```python
student = Student.objects.get(user__username='student_test')
student.total_points += 100
student.save()
```
