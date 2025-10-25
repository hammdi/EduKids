# 🎮 Améliorations Gamification - EduKids

## 📌 Vue d'ensemble

Ce document détaille les améliorations apportées au système de gamification pour l'espace Student d'EduKids, en se concentrant sur la personnalisation d'avatar et la boutique d'accessoires.

---

## 🎨 Fonctionnalités implémentées

### 1. Affichage Avatar sur le Dashboard

**Fichier modifié :** `templates/base/profile.html`

**Changements :**
- Affichage de l'avatar uploadé depuis `student_profile.avatar.image`
- Fallback vers emoji par défaut si aucun avatar
- Style responsive avec `object-fit: cover` (120px max)
- ID `profile-avatar-display` pour mise à jour dynamique

**Code clé :**
```django
{% if student_profile and student_profile.avatar.image %}
    <img src="{{ student_profile.avatar.image.url }}" alt="Mon avatar" 
         style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover;">
{% elif user.user_type == 'student' %}
    🎓
{% endif %}
```

---

### 2. Upload Avatar avec Preview Instantanée

**Fichier modifié :** `templates/gamification/avatar.html`

**Fonctionnalités :**
- ✅ Preview instantanée avant upload (JavaScript FileReader)
- ✅ Validation client-side : taille max 2MB, formats JPG/PNG
- ✅ Messages d'erreur clairs et visuels
- ✅ Bouton désactivé si validation échoue
- ✅ Toast de succès après upload
- ✅ Mise à jour de l'avatar sans refresh complet

**JavaScript clé :**
```javascript
// Preview instantanée
document.getElementById('avatar-image').addEventListener('change', function(e) {
    const file = e.target.files[0];
    
    // Validation taille (2MB max)
    if (file.size > 2 * 1024 * 1024) {
        fileError.textContent = '❌ Fichier trop volumineux. Maximum 2MB.';
        return;
    }
    
    // Validation format
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
        fileError.textContent = '❌ Format non autorisé. Utilise JPG ou PNG.';
        return;
    }
    
    // Afficher preview
    const reader = new FileReader();
    reader.onload = function(e) {
        imagePreview.src = e.target.result;
        previewContainer.style.display = 'block';
    };
    reader.readAsDataURL(file);
});
```

---

### 3. Boutique Accessoires - Achat

**Fichier modifié :** `gamification/views/__init__.py`

**Endpoint API :** `POST /gamification/api/user-accessories/`

**Améliorations :**
- ✅ Validation des points côté serveur
- ✅ Messages d'erreur positifs et encourageants
- ✅ Décrémentation dynamique des points dans l'UI
- ✅ Changement automatique du bouton "Acheter" → "Équiper"
- ✅ Vérification qu'on ne peut pas acheter 2 fois le même accessoire

**Code backend :**
```python
@action(detail=False, methods=['post'])
def purchase(self, request):
    accessory_id = request.data.get('accessory')
    student = request.user.student_profile
    
    # Vérifier les points
    if student.total_points < accessory.points_required:
        points_needed = accessory.points_required - student.total_points
        return Response({
            'error': f'Points insuffisants. Il te faut encore {points_needed} points.'
        }, status=400)
    
    # Effectuer l'achat
    student.total_points -= accessory.points_required
    student.save()
    
    user_accessory = UserAccessory.objects.create(
        student=student,
        accessory=accessory,
        status='owned'
    )
    
    return Response(serializer.data, status=201)
```

**Code frontend :**
```javascript
// Vérification côté client
if (currentPoints < pointsRequired) {
    showToast(`💰 Continue à apprendre ! Il te faut encore ${pointsRequired - currentPoints} points.`, 'info');
    return;
}

// Mise à jour dynamique après achat
const newPoints = currentPoints - pointsRequired;
document.getElementById('points-value').textContent = newPoints;

// Changer le bouton
btnElement.outerHTML = `
    <button class="btn btn-outline-kids btn-sm equip-btn" data-accessory-id="${accessoryId}">
        <i class="fas fa-plus me-1"></i>Équiper
    </button>
`;
```

---

### 4. Équipement d'Accessoires

**Endpoint API :** `POST /gamification/api/avatars/my-avatar/equip_accessory/`

**Fonctionnalités :**
- ✅ Vérification que l'accessoire est possédé
- ✅ Déséquipement automatique des accessoires du même type
- ✅ Un seul accessoire par slot (chapeau, lunettes, etc.)
- ✅ Changement visuel immédiat "Équiper" → "✓ Équipé"
- ✅ Toast de succès

**Code backend :**
```python
@action(detail=True, methods=['post'])
def equip_accessory(self, request, pk=None):
    avatar = self.get_object()
    student = request.user.student_profile
    
    user_accessory = UserAccessory.objects.get(
        student=student,
        accessory_id=accessory_id,
        status='owned'
    )
    
    # La méthode equip() gère automatiquement le déséquipement
    # des accessoires du même type
    success = user_accessory.equip(avatar)
    
    return Response(serializer.data)
```

**Logique dans le modèle :**
```python
def equip(self, avatar):
    """Équiper l'accessoire sur l'avatar"""
    if self.status == 'owned':
        # Déséquiper les autres accessoires du même type
        same_type_accessories = UserAccessory.objects.filter(
            student=self.student,
            accessory__accessory_type=self.accessory.accessory_type,
            status='equipped'
        )
        for ua in same_type_accessories:
            ua.unequip(avatar)
        
        # Équiper le nouvel accessoire
        self.status = 'equipped'
        self.save()
        avatar.accessories.add(self.accessory)
        avatar.save()
        return True
    return False
```

---

## 🎯 Messages UX Positifs

Tous les messages ont été conçus pour être encourageants et positifs :

| Situation | Message |
|-----------|---------|
| Upload réussi | 🎉 Super ! Ton avatar a été mis à jour avec succès ! |
| Achat réussi | 🎉 Bravo ! Accessoire débloqué avec succès ! Tu peux maintenant l'équiper. |
| Équipement réussi | ✨ Accessoire équipé avec succès ! Ton avatar est encore plus cool ! |
| Points insuffisants | 💰 Continue à apprendre ! Il te faut encore X points pour débloquer cet accessoire. |
| Fichier trop gros | ❌ Fichier trop volumineux. Maximum 2MB. |
| Format invalide | ❌ Format non autorisé. Utilise JPG ou PNG. |

---

## 🔧 Système de Toasts

**Fonction JavaScript :**
```javascript
function showToast(message, type) {
    const typeColors = {
        'success': 'success',
        'danger': 'danger',
        'info': 'info',
        'warning': 'warning'
    };
    
    const toastDiv = document.createElement('div');
    toastDiv.className = `alert alert-${typeColors[type]} alert-dismissible fade show position-fixed shadow-lg`;
    toastDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 320px; animation: slideInRight 0.3s ease-out;';
    toastDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close ms-2" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(toastDiv);
    
    // Auto-dismiss après 5 secondes
    setTimeout(() => {
        toastDiv.classList.remove('show');
        setTimeout(() => toastDiv.remove(), 300);
    }, 5000);
}
```

**Animation CSS :**
```css
@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

---

## 📊 Architecture des données

### Modèles utilisés

**Avatar** (gamification/models.py)
```python
class Avatar(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='avatar')
    image = models.ImageField(upload_to='avatars/custom/', blank=True, null=True)
    level = models.IntegerField(default=1)
    accessories = models.ManyToManyField('Accessory', blank=True, related_name='equipped_on')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
```

**Accessory**
```python
class Accessory(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='accessories/')
    accessory_type = models.CharField(max_length=20, choices=ACCESSORY_TYPE_CHOICES)
    points_required = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
```

**UserAccessory**
```python
class UserAccessory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='user_accessories')
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE, related_name='user_ownerships')
    status = models.CharField(max_length=10, choices=[('unlocked', 'Débloqué'), ('owned', 'Possédé'), ('equipped', 'Équipé')])
    date_obtained = models.DateTimeField(default=timezone.now)
```

**Student** (students/models.py)
```python
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    total_points = models.IntegerField(default=0)
    # ... autres champs
```

---

## 🔐 Sécurité

### Validations backend
1. **Upload avatar :**
   - Taille max : 2MB
   - Formats autorisés : JPG, PNG
   - Validation du content-type

2. **Achat accessoire :**
   - Vérification des points disponibles
   - Vérification que l'accessoire existe et est actif
   - Vérification qu'il n'est pas déjà possédé

3. **Équipement :**
   - Vérification de propriété
   - Vérification du profil étudiant
   - Gestion automatique des conflits de slots

### Permissions
- Tous les endpoints nécessitent `IsAuthenticated`
- Vérification du profil `student_profile` sur chaque requête
- CSRF tokens sur tous les formulaires

---

## 🚀 Déploiement

### Fichiers modifiés
```
✓ templates/base/profile.html
✓ templates/gamification/avatar.html
✓ gamification/views/__init__.py
✓ gamification/README_IMPROVEMENTS.md (nouveau)
✓ GAMIFICATION_TESTS.md (nouveau)
```

### Migrations nécessaires
Aucune migration nécessaire - les modèles existaient déjà.

### Configuration MEDIA
Assurez-vous que `MEDIA_URL` et `MEDIA_ROOT` sont configurés dans `settings.py` :
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

Et dans `urls.py` principal :
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... vos urls
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 📈 Améliorations futures possibles

1. **Affichage visuel des accessoires sur l'avatar**
   - Overlay CSS pour superposer les accessoires
   - Canvas HTML5 pour composition dynamique

2. **Animations**
   - Transition animée lors de l'équipement
   - Particules lors de l'achat

3. **Système de niveaux**
   - Débloquer des accessoires selon le niveau
   - Accessoires premium/rares

4. **Partage social**
   - Partager son avatar sur les réseaux
   - Galerie des avatars de la classe

5. **Achievements**
   - Badges pour collections complètes
   - Récompenses pour premières personnalisations

---

## 📞 Support

Pour toute question ou bug, consultez :
- `GAMIFICATION_TESTS.md` pour les tests
- `gamification/models.py` pour la structure des données
- `gamification/views/__init__.py` pour la logique API

---

**Version :** 1.0  
**Date :** Janvier 2025  
**Statut :** ✅ Production Ready
