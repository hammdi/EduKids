# Tests Gamification - EduKids Student Space

## 📋 Checklist des fonctionnalités implémentées

### 🎨 Partie Avatar

#### 1. Affichage de l'avatar sur le dashboard (profile.html)
- [x] **Implémenté** : Affichage de l'avatar uploadé depuis `student_profile.avatar.image`
- [x] **Fallback** : Affichage d'un emoji par défaut si aucun avatar n'existe
- [x] **Style** : Ratio respecté avec `object-fit: cover` et taille max 120px
- [x] **UI** : Centré et propre

**Tests à effectuer :**
```
1. Se connecter en tant qu'étudiant
2. Aller sur /profile/
3. Vérifier que l'avatar s'affiche (ou emoji par défaut)
4. Vérifier que l'image est bien centrée et de bonne taille
```

#### 2. Upload Avatar avec preview instantanée
- [x] **Bouton** : "Changer l'avatar" présent sur la page avatar
- [x] **Preview** : Aperçu instantané de l'image avant upload
- [x] **Validation taille** : Maximum 2MB avec message d'erreur clair
- [x] **Validation format** : Seulement .png et .jpg acceptés
- [x] **UX** : Toast de succès après upload
- [x] **Mise à jour** : Avatar mis à jour sans refresh complet (AJAX)

**Tests à effectuer :**
```
1. Aller sur /gamification/avatar/
2. Cliquer sur "Choisir un fichier"
3. Sélectionner une image valide (< 2MB, JPG/PNG)
   → Vérifier que la preview s'affiche immédiatement
4. Cliquer sur "Uploader mon image"
   → Vérifier le toast de succès
   → Vérifier que l'avatar principal est mis à jour sans refresh
5. Tester avec un fichier > 2MB
   → Vérifier le message d'erreur
6. Tester avec un format non autorisé (.gif, .bmp)
   → Vérifier le message d'erreur
```

**Endpoint API :**
- `POST /gamification/api/avatars/my-avatar/upload_image/`
- Validation backend : taille max 2MB, formats JPG/PNG uniquement

---

### 🛍️ Partie Boutique Accessoires

#### 3. Achat d'accessoire
- [x] **Boutique** : Liste des accessoires disponibles avec prix en points
- [x] **Bouton "Acheter"** : Actif si assez de points, désactivé sinon
- [x] **Message positif** : Si points insuffisants, message encourageant (pas d'erreur)
- [x] **Décrémentation dynamique** : Points mis à jour dans l'UI sans refresh
- [x] **État "Débloqué"** : Accessoire devient "Équiper" après achat

**Tests à effectuer :**
```
1. Aller sur /gamification/avatar/
2. Vérifier l'affichage des points en haut de page
3. Trouver un accessoire avec prix < points actuels
4. Cliquer sur "Acheter"
   → Vérifier le toast de succès "🎉 Bravo ! Accessoire débloqué..."
   → Vérifier que les points sont décrémentés dynamiquement
   → Vérifier que le bouton devient "Équiper"
5. Trouver un accessoire avec prix > points actuels
6. Cliquer sur "Acheter" (bouton désactivé normalement)
   → Si activé manuellement, vérifier le message positif
```

**Endpoint API :**
- `POST /gamification/api/user-accessories/`
- Body : `{"accessory": <id>}`
- Validation : points suffisants, accessoire non déjà possédé

#### 4. Équiper un accessoire
- [x] **Interface** : Bouton "Équiper" pour accessoires débloqués
- [x] **État visuel** : Badge "✓ Équipé" après équipement
- [x] **Affichage** : Accessoire visible sur l'avatar (logique backend)
- [x] **Slot unique** : Un seul item par type (chapeau, lunettes, etc.)

**Tests à effectuer :**
```
1. Acheter un accessoire (voir test précédent)
2. Cliquer sur "Équiper"
   → Vérifier le toast "✨ Accessoire équipé avec succès..."
   → Vérifier que le bouton devient "✓ Équipé"
3. Acheter un 2ème accessoire du même type (ex: 2 chapeaux)
4. Équiper le 2ème accessoire
   → Vérifier que le 1er est automatiquement déséquipé
   → Vérifier qu'un seul accessoire du même type est équipé
```

**Endpoint API :**
- `POST /gamification/api/avatars/my-avatar/equip_accessory/`
- Body : `{"accessory_id": <id>}`
- Logique : Déséquipe automatiquement les accessoires du même type

---

## 🧪 Tests automatiques recommandés

### Tests unitaires à créer (gamification/tests.py)

```python
class AvatarTestCase(TestCase):
    def test_avatar_default_display(self):
        """Vérifie l'affichage par défaut si pas d'avatar"""
        pass
    
    def test_avatar_upload_valid(self):
        """Vérifie l'upload d'une image valide"""
        pass
    
    def test_avatar_upload_invalid_size(self):
        """Vérifie le rejet d'une image > 2MB"""
        pass
    
    def test_avatar_upload_invalid_format(self):
        """Vérifie le rejet d'un format non autorisé"""
        pass


class AccessoryPurchaseTestCase(TestCase):
    def test_purchase_with_enough_points(self):
        """Vérifie l'achat avec points suffisants"""
        pass
    
    def test_purchase_without_enough_points(self):
        """Vérifie le message si points insuffisants"""
        pass
    
    def test_purchase_already_owned(self):
        """Vérifie qu'on ne peut pas acheter 2 fois"""
        pass


class AccessoryEquipmentTestCase(TestCase):
    def test_equip_owned_accessory(self):
        """Vérifie l'équipement d'un accessoire possédé"""
        pass
    
    def test_equip_not_owned_accessory(self):
        """Vérifie qu'on ne peut pas équiper un accessoire non possédé"""
        pass
    
    def test_equip_single_slot(self):
        """Vérifie qu'un seul accessoire par type est équipé"""
        pass
```

---

## 🎯 Points d'attention

### Sécurité
- ✅ Validation backend des fichiers uploadés (taille, format)
- ✅ Vérification des points avant achat (backend)
- ✅ Vérification de propriété avant équipement
- ✅ CSRF tokens sur tous les formulaires

### Performance
- ✅ Mise à jour dynamique sans refresh complet
- ✅ Prefetch des accessoires dans la vue Django
- ✅ Utilisation de select_related pour optimiser les requêtes

### UX
- ✅ Messages positifs et encourageants
- ✅ Toasts animés avec auto-dismiss
- ✅ Preview instantanée avant upload
- ✅ Feedback visuel sur tous les boutons (spinner pendant chargement)
- ✅ Boutons désactivés si action impossible

---

## 🚀 Commandes pour tester

### Lancer le serveur de développement
```bash
python manage.py runserver
```

### Créer un étudiant de test
```python
python manage.py shell

from users.models import User
from students.models import Student

# Créer un utilisateur
user = User.objects.create_user(
    username='student_test',
    email='student@test.com',
    password='test123',
    user_type='student',
    first_name='Test',
    last_name='Student'
)

# Créer le profil étudiant
student = Student.objects.create(
    user=user,
    grade_level='CE2',
    total_points=500  # Donner des points pour tester les achats
)
```

### Créer des accessoires de test
```python
from gamification.models import Accessory

# Créer quelques accessoires
Accessory.objects.create(
    name='Chapeau de pirate',
    accessory_type='hat',
    points_required=100,
    is_active=True
)

Accessory.objects.create(
    name='Lunettes de soleil',
    accessory_type='glasses',
    points_required=50,
    is_active=True
)

Accessory.objects.create(
    name='Cape de super-héros',
    accessory_type='outfit',
    points_required=200,
    is_active=True
)
```

---

## 📝 Notes techniques

### Structure des fichiers modifiés
```
EduKids/
├── templates/
│   ├── base/
│   │   └── profile.html (✓ modifié)
│   └── gamification/
│       └── avatar.html (✓ modifié)
├── gamification/
│   ├── models.py (déjà existant)
│   ├── views/
│   │   └── __init__.py (✓ modifié)
│   ├── serializers.py (déjà existant)
│   └── urls.py (déjà existant)
└── GAMIFICATION_TESTS.md (✓ nouveau)
```

### Endpoints API disponibles
- `GET /gamification/api/avatars/my-avatar/` - Récupérer l'avatar actuel
- `POST /gamification/api/avatars/my-avatar/upload_image/` - Upload avatar
- `GET /gamification/api/accessories/` - Liste des accessoires
- `POST /gamification/api/user-accessories/` - Acheter un accessoire
- `POST /gamification/api/avatars/my-avatar/equip_accessory/` - Équiper
- `POST /gamification/api/avatars/my-avatar/unequip_accessory/` - Déséquiper

### Variables de contexte dans les templates
- `user.student_profile` - Profil étudiant
- `user.student_profile.total_points` - Points totaux
- `student_profile.avatar` - Avatar de l'étudiant
- `student_profile.avatar.image` - Image uploadée

---

## ✅ Résumé des améliorations

### Front-end (HTML/CSS/JS)
1. ✅ Affichage avatar sur profile.html avec fallback
2. ✅ Preview instantanée avant upload
3. ✅ Validation client-side (taille, format)
4. ✅ Toasts animés pour feedback UX
5. ✅ Mise à jour dynamique des points
6. ✅ Changement d'état des boutons sans refresh

### Back-end (Django REST Framework)
1. ✅ Validation serveur (taille, format)
2. ✅ Endpoint purchase amélioré
3. ✅ Endpoint equip avec gestion des slots
4. ✅ Messages d'erreur clairs et positifs
5. ✅ Gestion correcte du profil student_profile

### Sécurité & Performance
1. ✅ Validation backend obligatoire
2. ✅ Vérification des permissions
3. ✅ Optimisation des requêtes DB
4. ✅ CSRF protection

---

**Date de création :** 2025-01-XX
**Auteur :** Cascade AI
**Version :** 1.0
