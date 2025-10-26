# 🔍 Guide d'Utilisation de la Recherche - EduKids Chatbot

## Vue d'Ensemble

La nouvelle barre de recherche permet aux utilisateurs de retrouver facilement leurs conversations passées en cherchant par mots-clés, exactement comme dans ChatGPT.

## 🎨 Interface Visuelle

```
┌─────────────────────────────────────────────────────────────┐
│  🎓 Assistant EduKids 🤖✨                                   │
├─────────────────────────────────────────────────────────────┤
│  🌍 Langue: [Français ▼]  🔊 Lecture vocale [✓]           │
├─────────────────────────────────────────────────────────────┤
│  🔍 Recherche: [________________] [🔎 Chercher]             │
│                [🗑️ Anciennes] [❌ Tout supprimer]          │
└─────────────────────────────────────────────────────────────┘
```

## 📝 Étapes d'Utilisation

### 1️⃣ Accéder à la Recherche
- La barre de recherche se trouve **en haut** de l'interface du chat
- Elle est visible **en permanence** avec un fond violet dégradé
- Le champ affiche le placeholder : "Rechercher dans l'historique..."

### 2️⃣ Effectuer une Recherche

**Méthode 1 : Clavier**
1. Cliquez dans le champ de recherche 🔍
2. Tapez vos mots-clés (ex: "Harry Potter", "mathématiques", "Freud")
3. Appuyez sur **Entrée** ⏎

**Méthode 2 : Souris**
1. Cliquez dans le champ de recherche 🔍
2. Tapez vos mots-clés
3. Cliquez sur le bouton **🔎 Chercher**

### 3️⃣ Visualiser les Résultats

Après la recherche, vous verrez :

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 Résultats de recherche pour "Harry Potter" (3 trouvés)  │
├─────────────────────────────────────────────────────────────┤
│  📁 Quiz sur Harry Potter                     [🗑️ Supprimer]│
│     25 oct. 2025, 14:32                                     │
├─────────────────────────────────────────────────────────────┤
│  📁 Discussion sur Poudlard                   [🗑️ Supprimer]│
│     24 oct. 2025, 10:15                                     │
├─────────────────────────────────────────────────────────────┤
│  📁 Les maisons de Poudlard                   [🗑️ Supprimer]│
│     23 oct. 2025, 16:45                                     │
├─────────────────────────────────────────────────────────────┤
│                  [❌ Effacer la recherche]                   │
└─────────────────────────────────────────────────────────────┘
```

### 4️⃣ Ouvrir une Conversation
- Cliquez sur le **titre** (📁 lien bleu) de n'importe quel résultat
- La conversation complète s'affiche dans la zone de messages
- La zone de recherche reste visible en haut

### 5️⃣ Supprimer une Conversation
- Cliquez sur **🗑️ Supprimer** à droite du résultat
- Une confirmation s'affiche : "Supprimer cette conversation ?"
- Cliquez **OK** pour confirmer
- Les résultats se mettent à jour automatiquement

### 6️⃣ Effacer la Recherche
- Cliquez sur **❌ Effacer la recherche** en bas des résultats
- OU effacez le texte dans le champ et appuyez sur Entrée
- L'historique complet se réaffiche (groupé par sujets)

## 🎯 Types de Recherches Supportées

### Recherche par Sujet
```
Exemples:
- "mathématiques"
- "Harry Potter"
- "sciences"
- "histoire"
```

### Recherche par Mots-Clés
```
Exemples:
- "quiz"
- "exercices"
- "Freud"
- "animaux"
```

### Recherche par Phrases
```
Exemples:
- "C'est quoi Poudlard"
- "les livres de Freud"
- "multiplication de nombres"
```

## 💡 Fonctionnalités Avancées

### Recherche Intelligente
- ✅ **Insensible à la casse** : "harry" = "Harry" = "HARRY"
- ✅ **Recherche dans titres** : trouve les titres de conversations
- ✅ **Recherche dans messages** : trouve les messages contenant les mots
- ✅ **Recherche dans sujets** : trouve par sujet classifié (ex: "Psychologie")

### Messages d'Aide
- **"Aucun résultat trouvé"** : aucune conversation ne correspond
  - Suggestion : "Essayez des mots-clés différents"
- **"Erreur de recherche"** : problème de connexion
  - Suggestion : "Veuillez réessayer"

### Effets Visuels
- 🎨 **Hover** : les résultats changent de couleur au survol
- 🔵 **Focus** : le champ de recherche s'illumine quand actif
- ✨ **Animations** : transitions douces pour meilleure UX

## 📊 Limites de Recherche

### Paramètres par Défaut
- **Maximum de résultats** : 20 conversations
- **Tri** : du plus récent au plus ancien
- **Timeout** : recherche rapide (< 2 secondes normalement)

### Que Faire Si...

**❓ "Je ne trouve pas ma conversation"**
- Essayez des mots-clés plus courts
- Vérifiez l'orthographe
- Utilisez des synonymes
- La conversation existe-t-elle encore ? (pas supprimée)

**❓ "Trop de résultats"**
- Soyez plus spécifique dans vos mots-clés
- Ajoutez plusieurs mots : "Harry Potter quiz"
- Utilisez des termes uniques de cette conversation

**❓ "La recherche est lente"**
- Vérifiez votre connexion internet
- Le serveur peut être occupé
- Attendez quelques secondes et réessayez

## 🚀 Raccourcis Clavier

| Raccourci | Action |
|-----------|--------|
| `Entrée` ⏎ | Lancer la recherche |
| `Échap` ⎋ | (Futur) Effacer le champ |

## 🔧 Gestion de l'Historique

### Boutons Additionnels

**🗑️ Anciennes**
- Supprime conversations anciennes (> N jours)
- Ou garde seulement les N plus récentes
- Prompt : "Supprimer plus vieux que 30 jours" ou "garder:10"

**❌ Tout supprimer**
- Supprime TOUTES les conversations (irréversible !)
- Confirmation requise
- Utile pour reset complet

## 💻 Pour les Développeurs

### API Backend
```javascript
// Endpoint de recherche
GET /assistant/api/search/
  ?student_id=<user_id>
  &q=<query>
  &limit=<max_results>

// Réponse
{
  "results": [
    {
      "id": 123,
      "title": "Quiz Harry Potter",
      "started_at": "2025-10-25T14:32:00"
    },
    ...
  ]
}
```

### Fonction JavaScript
```javascript
function doSearch() {
  const q = searchInput.value.trim();
  fetch(`/assistant/api/search/?student_id=${studentId}&q=${q}&limit=20`)
    .then(r => r.json())
    .then(data => {
      // Afficher résultats...
    });
}
```

## 🎓 Conseils d'Utilisation pour Enseignants

### Suivi des Élèves
1. **Rechercher par nom d'élève** : si inclus dans titre
2. **Rechercher par sujet de cours** : "multiplication", "grammaire"
3. **Rechercher par type** : "quiz", "exercice", "discussion"

### Organisation
1. **Nommer les conversations** : titres descriptifs
2. **Supprimer régulièrement** : anciennes conversations (> 30 jours)
3. **Archiver important** : exporter PDF avant suppression

### Statistiques
- Voir combien de conversations sur un sujet
- Identifier sujets populaires
- Suivre progression élève

## 📱 Responsive Design

La recherche est optimisée pour :
- 💻 **Desktop** : barre large, tous boutons visibles
- 📱 **Tablette** : barre adaptative, boutons empilés
- 📲 **Mobile** : champ pleine largeur, boutons en colonnes

## ✨ Améliorations Futures Possibles

1. **Filtres avancés** : par date, par type de message, par score quiz
2. **Recherche floue** : corrections orthographiques automatiques
3. **Historique de recherches** : suggestions basées sur recherches précédentes
4. **Export résultats** : PDF ou CSV des résultats trouvés
5. **Raccourcis clavier** : Ctrl+F pour focus sur recherche
6. **Recherche vocale** : parler au lieu de taper
7. **Tags/Labels** : étiqueter conversations pour filtrage

---

**Version** : 1.0  
**Date** : 25 octobre 2025  
**Compatibilité** : Chrome, Firefox, Safari, Edge (versions récentes)
