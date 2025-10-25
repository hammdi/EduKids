# Phase 2 - Avatars et Personnalisation - EduKids Gamification

## Vue d'ensemble

Phase 2 implémente le système d'avatars et de personnalisation pour la plateforme EduKids, permettant aux élèves de personnaliser leur expérience d'apprentissage.

## Modèles Implémentés

### Avatar
- **Description**: Avatars de base disponibles dans le système
- **Champs**:
  - `name`: Nom de l'avatar
  - `image`: Image de l'avatar
  - `avatar_type`: Type (base, premium, seasonal)
  - `level_required`: Niveau requis pour débloquer
  - `points_required`: Points requis pour débloquer
  - `is_active`: Statut d'activation

### StudentAvatar
- **Description**: Profil avatar de chaque élève
- **Champs**:
  - `student`: Référence vers l'élève
  - `current_avatar`: Avatar actuellement sélectionné
  - `unlocked_avatars`: Avatars débloqués (ManyToMany)
  - `equipped_accessories`: Accessoires équipés (JSON)
  - `customization_data`: Données de personnalisation (JSON)

### Accessory
- **Description**: Accessoires pour personnaliser les avatars
- **Champs**:
  - `name`: Nom de l'accessoire
  - `description`: Description
  - `image`: Image de l'accessoire
  - `accessory_type`: Type (hat, glasses, outfit, background, pet)
  - `points_required`: Points requis pour acheter
  - `level_required`: Niveau requis
  - `rarity`: Rareté (common, uncommon, rare, epic, legendary)

### UserAccessory
- **Description**: Accessoires possédés/équipés par les élèves
- **Champs**:
  - `student`: Élève propriétaire
  - `accessory`: Accessoire
  - `status`: Statut (unlocked, owned, equipped)
  - `unlocked_at`: Date de déblocage
  - `equipped_at`: Date d'équipement

## API Endpoints

### Avatars
- `GET /api/avatars/` - Liste des avatars disponibles
- `GET /api/avatars/unlocked/` - Avatars débloqués par l'utilisateur

### Profils Avatar
- `GET /api/student-avatars/` - Profil avatar de l'utilisateur
- `POST /api/student-avatars/` - Créer un profil avatar
- `POST /api/student-avatars/{id}/set_current_avatar/` - Changer d'avatar
- `POST /api/student-avatars/{id}/equip_accessory/` - Équiper un accessoire
- `POST /api/student-avatars/{id}/unequip_accessory/` - Déséquiper un accessoire

### Accessoires
- `GET /api/accessories/` - Liste des accessoires disponibles
- `GET /api/accessories/owned/` - Accessoires possédés

### Accessoires Utilisateur
- `GET /api/user-accessories/` - Accessoires de l'utilisateur
- `POST /api/user-accessories/{id}/purchase/` - Acheter un accessoire

## Fonctionnalités Clés

### Système d'Achat
- Achat d'accessoires avec des points
- Vérification des prérequis (points et niveau)
- Historique des achats

### Équipement d'Accessoires
- Équipement/déséquipement dynamique
- Stockage des accessoires équipés en JSON
- Mise à jour automatique du profil avatar

### Personnalisation
- Support pour données de personnalisation étendues
- Structure JSON flexible pour couleurs, positions, etc.

## Tests

18 tests unitaires couvrant :
- Création et validation des modèles
- Méthodes d'équipement/déséquipement
- Logique métier d'achat
- Intégration avec les profils avatar

## Sécurité

- Authentification requise pour tous les endpoints
- Validation des permissions d'accès
- Vérification des prérequis avant achats

## Prochaines Étapes (Phase 3)

- Interface frontend pour la boutique d'accessoires
- Système de quêtes et récompenses avancées
- Intégration avec le système de niveaux
- Interface de personnalisation visuelle