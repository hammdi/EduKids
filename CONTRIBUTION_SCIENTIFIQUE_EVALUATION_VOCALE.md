# 🎤 Contribution Scientifique : Évaluation Vocale par IA

## 📋 **Résumé Exécutif**

Ce document présente l'innovation scientifique intégrée au projet **EduKids** : un système d'**évaluation automatique des productions orales** des élèves du primaire, basé sur l'intelligence artificielle et l'analyse acoustique multidimensionnelle.

---

## 🎯 **Problématique**

### **Contexte Éducatif**
L'évaluation des compétences orales dans l'enseignement primaire représente un défi majeur :
- **Temps limité** des enseignants pour évaluer individuellement chaque élève
- **Subjectivité** inhérente à l'évaluation humaine
- **Manque de feedback immédiat** pour les élèves
- **Difficulté à quantifier** les aspects paraverbaux (intonation, rythme)

### **Question de Recherche**
**Comment automatiser l'évaluation des productions orales des élèves en intégrant des critères multidimensionnels (originalité, communication verbale et paraverbale) grâce à l'intelligence artificielle ?**

---

## 🔬 **Méthodologie Scientifique**

### **1. Cadre Théorique**

Notre système s'appuie sur trois dimensions d'évaluation issues de la recherche en linguistique et pédagogie :

#### **A. Originalité de l'Idée (30%)**
**Base théorique** : Créativité linguistique (Guilford, 1950; Torrance, 1974)

**Métriques implémentées** :
- **Diversité lexicale** : Type-Token Ratio (TTR)
  ```
  TTR = Nombre de mots uniques / Nombre total de mots
  ```
- **Mots-clés uniques** : Extraction de termes absents de la question
- **Entités nommées** : Identification de concepts via NLP (spaCy)
- **Connexions créatives** : Détection de métaphores et comparaisons

#### **B. Communication Verbale (40%)**
**Base théorique** : Compétences linguistiques (Chomsky, 1965; Halliday, 1973)

**Sous-dimensions** :

**B.1 Structure (15%)**
- Nombre de phrases
- Connecteurs logiques (donc, alors, parce que...)
- Présence introduction/conclusion
- Longueur moyenne des phrases

**B.2 Fluidité (15%)**
- Hésitations (euh, hum, ben...)
- Répétitions de mots
- Faux départs
- Ratio hésitations/mots totaux

**B.3 Vocabulaire (10%)**
- Richesse lexicale (TTR)
- Longueur moyenne des mots
- Proportion de mots "complexes" (>7 lettres)

#### **C. Communication Paraverbale (30%)**
**Base théorique** : Prosodie et communication non-verbale (Mehrabian, 1971)

**C.1 Intonation (12%)**
- Analyse via ponctuation détectée par Speech-to-Text
- Questions (?) : engagement
- Exclamations (!) : expressivité
- Virgules/points : pauses naturelles

**C.2 Rythme (10%)**
- Débit de parole (mots/minute)
- Plage optimale enfants : 100-150 mots/min
- Extraction via durée audio / nombre de mots

**C.3 Temporalité (8%)**
- Détection des pauses (librosa.effects.split)
- Durée moyenne des pauses
- Distribution des segments de parole

---

### **2. Architecture Technique**

```
┌─────────────────────────────────────────────────────────────┐
│                    ÉVALUATION VOCALE IA                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 1: CAPTURE AUDIO                                      │
│  - Enregistrement navigateur (Web Audio API)                 │
│  - Format: WAV/MP3, 16kHz, mono                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 2: TRANSCRIPTION (Speech-to-Text)                     │
│  - OpenAI Whisper API / Google Speech API                    │
│  - Transcription avec ponctuation                            │
│  - Horodatage des segments                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 3: ANALYSE MULTIDIMENSIONNELLE                        │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  ANALYSE TEXTE   │  │  ANALYSE AUDIO   │                │
│  │  (NLP)           │  │  (DSP)           │                │
│  └──────────────────┘  └──────────────────┘                │
│           │                      │                           │
│           ▼                      ▼                           │
│  ┌──────────────────────────────────────────┐              │
│  │  A. Originalité (spaCy, NLTK)            │              │
│  │  - Diversité lexicale                    │              │
│  │  - Mots-clés uniques                     │              │
│  │  - Entités nommées                       │              │
│  └──────────────────────────────────────────┘              │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────┐              │
│  │  B. Communication Verbale                │              │
│  │  - Structure (connecteurs, organisation) │              │
│  │  - Fluidité (hésitations, répétitions)   │              │
│  │  - Vocabulaire (TTR, complexité)         │              │
│  └──────────────────────────────────────────┘              │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────┐              │
│  │  C. Communication Paraverbale            │              │
│  │  - Intonation (ponctuation)              │              │
│  │  - Rythme (librosa: débit parole)        │              │
│  │  - Temporalité (pauses, segments)        │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 4: SCORING PONDÉRÉ                                    │
│                                                              │
│  Score Global = (A × 0.30) + (B × 0.40) + (C × 0.30)       │
│                                                              │
│  Où:                                                         │
│  A = Originalité (0-100)                                     │
│  B = (Structure×0.15 + Fluidité×0.15 + Vocab×0.10) / 0.40  │
│  C = (Intonation×0.12 + Rythme×0.10 + Timing×0.08) / 0.30  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 5: GÉNÉRATION FEEDBACK IA                             │
│  - Analyse des forces/faiblesses                             │
│  - Recommandations personnalisées                            │
│  - Comparaison avec pairs (anonymisée)                       │
└─────────────────────────────────────────────────────────────┘
```

---

### **3. Implémentation Technique**

#### **Technologies Utilisées**

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| **Backend** | Django 5.2.6 | Framework principal |
| **Base de données** | PostgreSQL | Stockage évaluations |
| **Speech-to-Text** | OpenAI Whisper | Transcription audio |
| **NLP** | spaCy 3.8+, NLTK | Analyse linguistique |
| **Audio Processing** | Librosa 0.10.2 | Extraction features audio |
| **Prosodie** | Praat-Parselmouth | Analyse pitch/intonation |
| **Signal Processing** | SciPy 1.15.1 | Traitement du signal |

#### **Modèles de Données**

**VoiceAssessment** (Table principale)
```python
class VoiceAssessment(models.Model):
    student = ForeignKey(Student)
    prompt = TextField()  # Question posée
    audio_file = FileField()
    transcription = TextField()
    
    # Scores (0-100)
    originality_score = FloatField()
    verbal_structure_score = FloatField()
    verbal_fluency_score = FloatField()
    verbal_vocabulary_score = FloatField()
    paraverbal_intonation_score = FloatField()
    paraverbal_rhythm_score = FloatField()
    paraverbal_timing_score = FloatField()
    overall_score = FloatField()
    
    # Analyses détaillées (JSON)
    originality_analysis = JSONField()
    verbal_analysis = JSONField()
    paraverbal_analysis = JSONField()
    audio_metrics = JSONField()
    
    # Feedback IA
    ai_feedback = TextField()
```

---

## 📊 **Résultats Attendus**

### **Avantages Pédagogiques**

1. **Objectivité** : Évaluation standardisée et reproductible
2. **Rapidité** : Feedback immédiat (< 30 secondes)
3. **Granularité** : 7 critères distincts vs évaluation globale traditionnelle
4. **Traçabilité** : Historique complet des progrès
5. **Personnalisation** : Recommandations adaptées aux faiblesses détectées

### **Métriques de Performance**

| Métrique | Valeur Cible |
|----------|--------------|
| Temps de traitement | < 30 secondes |
| Précision transcription | > 95% (Whisper) |
| Corrélation avec évaluation humaine | > 0.80 (Pearson) |
| Satisfaction enseignants | > 85% |
| Amélioration élèves (3 mois) | > 20% |

---

## 🎓 **Contribution Scientifique**

### **Originalité de la Recherche**

1. **Approche multidimensionnelle** : Intégration de 3 dimensions (originalité, verbal, paraverbal) dans un seul système
2. **Adaptation au primaire** : Critères spécifiques pour enfants 6-12 ans
3. **Analyse paraverbale automatisée** : Extraction d'intonation via ponctuation (innovation méthodologique)
4. **Système complet** : De la capture audio au feedback personnalisé

### **Applications Futures**

- **Détection précoce** de troubles du langage
- **Évaluation à distance** (e-learning)
- **Formation des enseignants** (analyse de leurs propres pratiques)
- **Recherche longitudinale** sur le développement langagier

---

## 📚 **Références Bibliographiques**

1. Guilford, J. P. (1950). *Creativity*. American Psychologist, 5(9), 444-454.
2. Chomsky, N. (1965). *Aspects of the Theory of Syntax*. MIT Press.
3. Mehrabian, A. (1971). *Silent Messages*. Wadsworth.
4. Torrance, E. P. (1974). *Torrance Tests of Creative Thinking*. Personnel Press.
5. Halliday, M. A. K. (1973). *Explorations in the Functions of Language*. Edward Arnold.
6. Radford, A. et al. (2022). *Robust Speech Recognition via Large-Scale Weak Supervision*. OpenAI.

---

## 🚀 **Perspectives PFE**

### **Possibilités de Publication**

1. **Conférence** : EIAH (Environnements Informatiques pour l'Apprentissage Humain)
2. **Journal** : STICEF (Sciences et Technologies de l'Information et de la Communication pour l'Éducation et la Formation)
3. **Workshop** : AIED (Artificial Intelligence in Education)

### **Extensions Possibles**

- Comparaison avec évaluation humaine (étude de validation)
- Analyse de corpus (1000+ évaluations)
- Modèle prédictif de réussite scolaire
- Interface de visualisation des progrès

---

## ✅ **Conclusion**

Ce système d'évaluation vocale par IA représente une **contribution scientifique significative** dans le domaine des EIAH (Environnements Informatiques pour l'Apprentissage Humain), combinant :

- **Rigueur méthodologique** (critères multidimensionnels fondés sur la recherche)
- **Innovation technique** (analyse automatisée complète)
- **Applicabilité pédagogique** (feedback immédiat et personnalisé)

Le projet **EduKids** constitue ainsi une base solide pour un **Projet de Fin d'Études** et une potentielle **publication scientifique**.

---

**Auteur** : Hamdi  
**Encadrant** : [Nom de l'enseignante]  
**Institution** : [Votre université]  
**Date** : Octobre 2025  
**Projet** : EduKids - Hub Éducatif Multimodal

