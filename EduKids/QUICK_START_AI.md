# 🚀 Quick Start - IA Avatar

Guide rapide pour tester la fonctionnalité d'équipement d'accessoires avec IA.

---

## 📦 Installation

### 1. Installer les dépendances
```bash
pip install google-generativeai>=0.3.0
pip install Pillow>=10.0.0
```

### 2. Configurer l'API Gemini

Créer un fichier `.env` à la racine :
```bash
GEMINI_API_KEY=your-gemini-api-key-here
```

Ou ajouter directement dans `settings.py` :
```python
GEMINI_API_KEY = 'your-gemini-api-key-here'
```

**Obtenir une clé API :**
1. Aller sur https://makersuite.google.com/app/apikey
2. Créer une clé API
3. Copier la clé

---

## 🧪 Test rapide

### 1. Tester le service IA
```bash
python test_ai_avatar.py
```

**Résultat attendu :**
```
🧪 Test du service IA Avatar...
✅ Service IA initialisé
✅ Images de test créées
✅ Composite réussi!
   Message: 🎉 Chapeau Test équipé avec style !
✅ Image sauvegardée: test_avatar_output.jpg
```

### 2. Lancer le serveur
```bash
python manage.py runserver
```

### 3. Tester dans le navigateur

#### Étape 1 : Upload un avatar
```
http://127.0.0.1:8000/student/customize/
→ Upload une image d'avatar
```

#### Étape 2 : Acheter un accessoire
```
http://127.0.0.1:8000/student/store/
→ Acheter un accessoire (ex: chapeau)
```

#### Étape 3 : Équiper avec IA
```
http://127.0.0.1:8000/student/inventory/
→ Cliquer sur "✨ IA Style"
→ Voir l'avatar se modifier en temps réel !
```

---

## 🎯 Endpoints disponibles

### Équiper manuellement
```bash
curl -X POST http://127.0.0.1:8000/api/gamification/equip/1/ \
  -H "X-CSRFToken: <token>" \
  -H "Cookie: sessionid=<session>"
```

### Équiper avec IA
```bash
curl -X POST http://127.0.0.1:8000/api/gamification/ai/equip/1/ \
  -H "X-CSRFToken: <token>" \
  -H "Cookie: sessionid=<session>"
```

### Déséquiper
```bash
curl -X POST http://127.0.0.1:8000/api/gamification/unequip/1/ \
  -H "X-CSRFToken: <token>" \
  -H "Cookie: sessionid=<session>"
```

---

## 🐛 Troubleshooting

### Erreur : "GEMINI_API_KEY non configurée"
**Solution :**
```bash
# Ajouter dans .env
echo "GEMINI_API_KEY=your-key-here" >> .env

# Ou dans settings.py
GEMINI_API_KEY = 'your-key-here'
```

### Erreur : "Module 'google.generativeai' not found"
**Solution :**
```bash
pip install google-generativeai
```

### Erreur : "Upload d'abord une photo d'avatar"
**Solution :**
1. Aller sur `/student/customize/`
2. Upload une image
3. Réessayer

### Avatar ne se met pas à jour
**Solution :**
1. Vérifier les permissions du dossier `media/`
```bash
chmod 755 media/
chmod 755 media/avatars/
```

2. Vérifier que `MEDIA_ROOT` et `MEDIA_URL` sont configurés dans `settings.py`

---

## ✅ Checklist de validation

- [ ] Service IA initialisé sans erreur
- [ ] Test `test_ai_avatar.py` réussi
- [ ] Serveur lancé
- [ ] Avatar uploadé
- [ ] Accessoire acheté
- [ ] Bouton "✨ IA Style" visible
- [ ] Clic sur "✨ IA Style" → Loading overlay
- [ ] Avatar modifié et sauvegardé
- [ ] Effets visuels (halo, vibration, confetti)
- [ ] Message motivant affiché
- [ ] Badge "✓ ÉQUIPÉ" visible après rechargement

---

## 📚 Documentation complète

Voir `AI_AVATAR_IMPLEMENTATION.md` pour :
- Architecture détaillée
- API complète
- Animations CSS
- JavaScript
- Tests manuels

---

## 🎨 Démo visuelle

### Avant équipement IA
```
┌─────────────────────┐
│   Avatar simple     │
│                     │
│        😊          │
│                     │
└─────────────────────┘
```

### Pendant traitement
```
┌─────────────────────┐
│  🎨 L'IA travaille  │
│                     │
│    ⚙️ Loading...    │
│                     │
└─────────────────────┘
```

### Après équipement
```
┌─────────────────────┐
│   Avatar stylé      │
│       🎩            │
│        😊          │
│   ✨ Halo ✨       │
└─────────────────────┘
🎉 Confetti explosif !
```

---

## 🚀 Prêt à tester !

```bash
# 1. Installer
pip install -r requirements_ai.txt

# 2. Configurer
echo "GEMINI_API_KEY=your-key" > .env

# 3. Tester
python test_ai_avatar.py

# 4. Lancer
python manage.py runserver

# 5. Profiter !
# http://127.0.0.1:8000/student/inventory/
```

**Bon test ! 🎨✨**
