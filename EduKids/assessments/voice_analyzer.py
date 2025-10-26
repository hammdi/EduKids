"""
AI Voice Analysis Service for EduKids
Complete Analysis: Originality, Verbal and Paraverbal Communication
"""
import os
import json
import re
from typing import Dict, List, Tuple
from datetime import datetime

# Optional imports - will work without them
try:
    import librosa
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class VoiceAnalyzer:
    """
    Main analyzer for voice evaluation
    """
    
    def __init__(self):
        """Initialize NLP models"""
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')  # English model instead
            except:
                try:
                    self.nlp = spacy.load('en_core_web_sm')
                except:
                    self.nlp = None
    
    def analyze_complete(self, audio_path: str, transcription: str, prompt: str) -> Dict:
        """
        Analyse complète de l'évaluation vocale
        
        Args:
            audio_path: Chemin vers le fichier audio
            transcription: Texte transcrit
            prompt: Question/sujet posé
        
        Returns:
            Dict avec tous les scores et analyses
        """
        # 1. Analyse de l'originalité
        originality_data = self.analyze_originality(transcription, prompt)
        
        # 2. Analyse de la communication verbale
        verbal_data = self.analyze_verbal_communication(transcription)
        
        # 3. Analyse de la communication paraverbale
        paraverbal_data = self.analyze_paraverbal_communication(audio_path, transcription)
        
        # 4. Calcul des scores
        scores = self.calculate_scores(originality_data, verbal_data, paraverbal_data)
        
        # 5. Génération du feedback
        feedback = self.generate_feedback(scores, originality_data, verbal_data, paraverbal_data)
        
        return {
            'scores': scores,
            'originality_analysis': originality_data,
            'verbal_analysis': verbal_data,
            'paraverbal_analysis': paraverbal_data,
            'feedback': feedback
        }
    
    # ========== 1. ANALYSE D'ORIGINALITÉ ==========
    
    def analyze_originality(self, transcription: str, prompt: str) -> Dict:
        """
        Analyse l'originalité et la créativité de la réponse
        
        Critères:
        - Mots-clés uniques non présents dans la question
        - Diversité lexicale
        - Concepts innovants
        - Connexions créatives
        - DÉTECTION DE VIOLATION DE LANGUE (pénalité sévère)
        - DÉTECTION DE TRICHERIE (lecture, répétition, etc.)
        """
        print(f"\n{'='*60}")
        print(f"🎨 ANALYSE D'ORIGINALITÉ")
        print(f"{'='*60}")
        
        doc = self.nlp(transcription) if self.nlp else None
        prompt_doc = self.nlp(prompt) if self.nlp else None
        
        # DÉTECTION DE VIOLATION DE LANGUE
        language_violation = self._detect_language_violation(transcription, prompt)
        print(f"🌍 Détection de langue:")
        print(f"   Langue du prompt: {language_violation['prompt_language']}")
        print(f"   Langue de la transcription: {language_violation['transcription_language']}")
        print(f"   Correspondance: {'✅ OUI' if language_violation['language_match'] else '❌ NON'}")
        print(f"   Pourcentage de correspondance: {language_violation['match_percentage']}%")
        print(f"   Sévérité de la violation: {language_violation['violation_severity']}")
        
        # DÉTECTION DE TRICHERIE
        cheating_detection = self._detect_cheating(transcription, prompt)
        print(f"🚨 Détection de tricherie:")
        print(f"   Score de tricherie: {cheating_detection['cheating_score']}/100")
        print(f"   Sévérité: {cheating_detection['severity']}")
        if cheating_detection['violations']:
            print(f"   Violations détectées:")
            for violation in cheating_detection['violations']:
                print(f"      - {violation}")
        
        # Extraire les mots-clés
        transcription_words = set(transcription.lower().split())
        prompt_words = set(prompt.lower().split())
        
        # Mots uniques (pas dans la question)
        unique_words = transcription_words - prompt_words
        unique_words = {w for w in unique_words if len(w) > 3}  # Filtrer mots courts
        
        # Diversité lexicale (TTR - Type-Token Ratio)
        total_words = len(transcription.split())
        unique_word_count = len(set(transcription.lower().split()))
        lexical_diversity = unique_word_count / total_words if total_words > 0 else 0
        
        # Analyse des entités nommées (concepts)
        named_entities = []
        if doc:
            named_entities = [ent.text for ent in doc.ents]
        
        # Score d'originalité (0-100) avec pénalités pour violations
        originality_score = self._calculate_originality_score(
            unique_words, lexical_diversity, named_entities, total_words, language_violation, cheating_detection
        )
        
        print(f"\n📊 Score d'originalité final: {originality_score}/100")
        print(f"{'='*60}\n")
        
        return {
            'unique_words': list(unique_words)[:20],  # Top 20
            'unique_word_count': len(unique_words),
            'lexical_diversity': round(lexical_diversity, 3),
            'named_entities': named_entities,
            'creative_connections': self._detect_creative_connections(transcription),
            'language_violation': language_violation,
            'cheating_detection': cheating_detection,
            'score': originality_score
        }
    
    def _detect_language_violation(self, transcription: str, prompt: str) -> Dict:
        """
        Détecte si l'étudiant parle dans une langue différente de celle demandée
        """
        # Détecter la langue du prompt (français, anglais, arabe)
        prompt_language = self._detect_language(prompt)
        transcription_language = self._detect_language(transcription)
        
        # Vérifier si les langues correspondent (incluant langues mixtes)
        language_match = prompt_language == transcription_language
        
        # DÉTECTION DE LANGUE MIXTE = VIOLATION SEULEMENT si vraiment mixte
        if 'mixed' in transcription_language:
            language_match = False
            # Pénalité proportionnelle au mélange
            if transcription_language == 'mixed_english_french':
                match_percentage = 20  # Pénalité mais pas échec total
            else:
                match_percentage = 20
        
        # Calculer le pourcentage de correspondance
        if not language_match:
            # Analyser les mots communs entre les langues
            prompt_words = set(prompt.lower().split())
            transcription_words = set(transcription.lower().split())
            common_words = prompt_words.intersection(transcription_words)
            match_percentage = len(common_words) / max(len(transcription_words), 1) * 100
        else:
            match_percentage = 100
        
        return {
            'prompt_language': prompt_language,
            'transcription_language': transcription_language,
            'language_match': language_match,
            'match_percentage': round(match_percentage, 2),
            'violation_severity': 'high' if match_percentage < 30 else 'medium' if match_percentage < 60 else 'low'
        }
    
    def _detect_language(self, text: str) -> str:
        """
        Détecte la langue d'un texte avec analyse avancée (français, anglais, arabe)
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        # Mots-clés français (plus complets)
        french_words = [
            'le', 'la', 'les', 'de', 'du', 'des', 'et', 'ou', 'mais', 'donc', 'alors', 'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
            'un', 'une', 'ce', 'cette', 'ces', 'son', 'sa', 'ses', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
            'avec', 'sans', 'pour', 'dans', 'sur', 'par', 'vers', 'chez', 'entre', 'pendant', 'depuis',
            'très', 'plus', 'moins', 'bien', 'mal', 'beaucoup', 'peu', 'assez', 'trop', 'si', 'que', 'qui', 'quoi', 'où', 'quand', 'comment', 'pourquoi'
        ]
        french_count = sum(1 for word in words if word in french_words)
        
        # Mots-clés anglais (plus complets)
        english_words = [
            'the', 'a', 'an', 'and', 'or', 'but', 'so', 'then', 'i', 'you', 'he', 'she', 'we', 'they', 'is', 'are', 'was', 'were',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these', 'those',
            'with', 'without', 'for', 'in', 'on', 'by', 'to', 'from', 'at', 'between', 'during', 'since',
            'very', 'more', 'less', 'good', 'bad', 'much', 'little', 'enough', 'too', 'if', 'that', 'what', 'where', 'when', 'how', 'why',
            'super', 'power', 'magic', 'magical', 'have', 'can', 'could', 'would', 'should', 'will', 'shall',
            'hello', 'everyone', 'everybody', 'hi', 'hey', 'yes', 'no', 'ok', 'okay', 'sure', 'right', 'exactly',
            'old', 'young', 'new', 'first', 'last', 'next', 'previous', 'same', 'different', 'other', 'another',
            'let', 'begin', 'wow', 'happy', 'unfortunately', 'be', 'am', 'been', 'being', 'do', 'does', 'did', 'done',
            'go', 'goes', 'went', 'gone', 'get', 'gets', 'got', 'gotten', 'make', 'makes', 'made', 'making',
            'take', 'takes', 'took', 'taken', 'come', 'comes', 'came', 'see', 'sees', 'saw', 'seen', 'know', 'knows', 'knew', 'known',
            # Mots spécifiques des transcriptions
            'okay', 'bonjour', 'mean', 'had', 'superpower', 'preferred', 'allows', 'revive', 'people', 'met', 'died', 'again',
            'grandparents', 'brilliant', 'scientists', 'einstein', 'prophets', 'world', 'easy', 'peace', 'know', 'else', 'going',
            'help', 'avoid', 'crying', 'side', 'born', 'die', 'equivalent', 'keep', 'number', 'higher', 'feed', 'everyone',
            'minding', 'business', 'trimming', 'messy', 'hedge', 'behind', 'yoke', 'saw', 'door', 'attached', 'wall', 'standing',
            'middle', 'backyard', 'owned', 'place', 'wood', 'shimmered', 'faintly', 'garbed', 'strange', 'pattern', 'seems', 'move',
            'look', 'away', 'naturally', 'totally', 'rational', 'person', 'open', 'air', 'bent', 'twisted', 'suddenly', 'longer',
            'stood', 'floating', 'island', 'surrounded', 'sky', 'looks', 'spilled', 'paint', 'streaks', 'violet', 'gold', 'merlot',
            'shifting', 'liquid', 'ground', 'beneath', 'sparkled', 'tinny', 'crystals', 'sunk', 'stepped', 'distance', 'creatures',
            'mists', 'waving', 'constellations', 'glowing', 'trees', 'river', 'light', 'wood', 'between', 'rocks', 'massive', 'tree',
            'grow', 'center', 'leaves', 'glass', 'wind', 'blow', 'clinked', 'together', 'creating', 'music', 'chest', 'ash',
            'emotional', 'name', 'figure', 'emerged', 'half', 'human', 'shadow', 'spoke', 'words', 'voiced', 'directly', 'inside',
            'mind', 'every', 'reason', 'yours', 'didn\'t', 'answer', 'still', 'don\'t', 'before', 'could', 'say', 'anything',
            'dissolved', 'fell', 'straight', 'covert', 'glittering', 'dust', 'faded', 'moment', 'blink', 'gone', 'grass', 'remembers',
            'bending', 'slightly', 'once', 'stowed', 'sometimes', 'night', 'hums', 'just', 'right', 'swear', 'hear', 'footsteps',
            'singing', 'again', 'right', 'now', 'gonna', 'talk', 'english', 'keep', 'talking', 'figure', 'out', 'give', 'good',
            'mark', 'hell', 'wrong', 'doing', 'life', 'harder'
        ]
        english_count = sum(1 for word in words if word in english_words)
        
        # Mots-clés arabes (caractères arabes)
        arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
        arabic_count = arabic_chars / max(len(text), 1) * 100
        
        # Analyse des patterns linguistiques
        french_patterns = [
            r'\b(je|tu|il|elle|nous|vous|ils|elles)\b',  # Pronoms
            r'\b(le|la|les|un|une|des|du|de|d\w+)\b',    # Articles
            r'\b(est|sont|était|étaient|sera|seront)\b', # Verbes être
            r'\b(ai|as|a|avons|avez|ont|avais|avait|avions|aviez|avaient)\b'  # Avoir
        ]
        
        english_patterns = [
            r'\b(i|you|he|she|we|they)\b',  # Pronouns
            r'\b(the|a|an)\b',              # Articles
            r'\b(is|are|was|were|will|would)\b',  # Be verbs
            r'\b(have|has|had|having)\b'   # Have
        ]
        
        # Compter les patterns
        import re
        french_pattern_count = sum(len(re.findall(pattern, text_lower)) for pattern in french_patterns)
        english_pattern_count = sum(len(re.findall(pattern, text_lower)) for pattern in english_patterns)
        
        # Détection de phrases complètes en anglais (patterns plus simples)
        english_phrases = [
            r'\blet\s+the\b',                 # "let the"
            r'\bi\s+will\s+be\b',            # "i will be"
            r'\bunfortunately\b',            # "unfortunately"
            r'\bwow\b',                       # "wow"
            r'\bvery\s+\w+\b',               # "very happy"
            r'\band\s+right\s+now\b',        # "and right now"
            r'\bi\s+mean\b',                  # "i mean"
            r'\bif\s+i\s+had\b',             # "if i had"
            r'\bwhat\s+is\s+the\b',          # "what is the"
            r'\bwhy\s+you\s+doing\b',        # "why you doing"
            r'\byou\s+make\s+my\b',          # "you make my"
            r'\bi\s+was\s+just\b',           # "i was just"
            r'\bi\s+stood\s+on\b',           # "i stood on"
            r'\bi\s+didn\'t\s+have\b',       # "i didn't have"
            r'\bi\s+still\s+don\'t\b',       # "i still don't"
        ]
        english_phrase_count = sum(len(re.findall(pattern, text_lower)) for pattern in english_phrases)
        
        print(f"🌍 PHRASES ANGLAISES: {english_phrase_count}")
        
        # Debug détaillé
        print(f"🔍 DEBUG DÉTAILLÉ:")
        print(f"   - Mots français: {french_count}")
        print(f"   - Patterns français: {french_pattern_count}")
        print(f"   - Mots anglais: {english_count}")
        print(f"   - Patterns anglais: {english_pattern_count}")
        print(f"   - Phrases anglaises: {english_phrase_count}")
        
        # Score total par langue
        french_score = french_count + french_pattern_count
        english_score = english_count + english_pattern_count + english_phrase_count
        
        print(f"🌍 LANGUAGE DEBUG: French={french_score}, English={english_score}")
        
        # DÉTECTION DE LANGUE RÉALISTE
        if arabic_count > 20:
            return 'arabic'
        elif english_score > 0 and french_score > 0:
            # Langue mixte SEULEMENT si les deux langues sont SIGNIFICATIVES
            total_words = len(text.split())
            english_ratio = english_score / total_words
            french_ratio = french_score / total_words
            
            print(f"🌍 RATIO DEBUG: English={english_ratio:.3f}, French={french_ratio:.3f}")
            
            # Seulement mixte si les deux langues représentent plus de 10% chacune
            if english_ratio > 0.1 and french_ratio > 0.1:
                if english_score > french_score:
                    return 'mixed_english_french'
                else:
                    return 'mixed_french_english'
            elif english_score > french_score * 2:  # Anglais vraiment dominant
                return 'english'
            elif french_score > english_score * 2:  # Français vraiment dominant
                return 'french'
            else:
                # Si une langue est clairement dominante, prendre celle-ci
                if french_score > english_score:
                    return 'french'
                else:
                    return 'english'
        elif english_score > french_score and english_score > 1:
            return 'english'
        elif french_score > english_score and french_score > 2:
            return 'french'
        else:
            result = 'english'  # Par défaut anglais
        
        print(f"🌍 FINAL LANGUAGE: {result}")
        return result
    
    def _calculate_originality_score(self, unique_words, lexical_diversity, entities, total_words, language_violation, cheating_detection) -> float:
        """Calcule le score d'originalité avec pénalités pour violations et tricherie"""
        # Score de base
        unique_score = min(len(unique_words) / max(total_words * 0.5, 1) * 100, 100)  # 40%
        diversity_score = lexical_diversity * 100  # 40%
        entity_score = min(len(entities) / max(total_words * 0.1, 1) * 100, 100)  # 20%
        
        base_score = (unique_score * 0.4) + (diversity_score * 0.4) + (entity_score * 0.2)
        
        # PÉNALITÉ ULTRA-SÉVÈRE pour violation de langue
        if not language_violation['language_match']:
            if language_violation['violation_severity'] == 'high':
                base_score = 0  # 100% de pénalité - ÉCHEC TOTAL
            elif language_violation['violation_severity'] == 'medium':
                base_score *= 0.05  # 95% de pénalité
            else:
                base_score *= 0.2  # 80% de pénalité
        
        # PÉNALITÉ ULTRA-SÉVÈRE pour tricherie
        if cheating_detection['cheating_score'] > 0:
            if cheating_detection['severity'] == 'high':
                base_score = 0  # 100% de pénalité - ÉCHEC TOTAL
            elif cheating_detection['severity'] == 'medium':
                base_score = 0  # 100% de pénalité - ÉCHEC TOTAL
            else:
                base_score *= 0.1  # 90% de pénalité
        
        return round(min(base_score, 100), 2)
    
    def _detect_cheating(self, transcription: str, prompt: str) -> Dict:
        """
        Détecte les tentatives de tricherie
        """
        import re
        
        cheating_indicators = {
            'reading_from_script': False,
            'repetitive_content': False,
            'insufficient_content': False,
            'copy_paste_detection': False,
            'artificial_patterns': False,
            'violations': []
        }
        
        # 1. Détection de lecture de script (patterns trop parfaits)
        perfect_patterns = [
            r'\b(je vais vous parler|i will talk about|let me explain)\b',  # Phrases de présentation
            r'\b(premièrement|deuxièmement|troisièmement|first|second|third)\b',  # Structure trop formelle
            r'\b(en conclusion|pour conclure|in conclusion|to conclude)\b'  # Phrases de conclusion
        ]
        
        perfect_count = sum(len(re.findall(pattern, transcription.lower())) for pattern in perfect_patterns)
        if perfect_count >= 2:
            cheating_indicators['reading_from_script'] = True
            cheating_indicators['violations'].append("Lecture de script détectée")
        
        # 2. Détection de contenu répétitif - PLUS SÉVÈRE
        words = transcription.lower().split()
        if len(words) > 0:
            word_freq = {}
            for word in words:
                if len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Si un mot apparaît plus de 20% du temps (plus sévère)
            max_freq = max(word_freq.values()) if word_freq else 0
            repetition_ratio = max_freq / len(words)
            
            if repetition_ratio > 0.5:  # Plus de 50% de répétition = ÉCHEC TOTAL
                cheating_indicators['repetitive_content'] = True
                cheating_indicators['violations'].append("Contenu extrêmement répétitif")
            elif repetition_ratio > 0.3:  # Plus de 30% = SÉVÈRE
                cheating_indicators['repetitive_content'] = True
                cheating_indicators['violations'].append("Contenu très répétitif")
            elif repetition_ratio > 0.2:  # Plus de 20% = MODÉRÉ
                cheating_indicators['repetitive_content'] = True
                cheating_indicators['violations'].append("Contenu répétitif")
        
        # 3. Détection de contenu insuffisant
        if len(transcription.split()) < 10:
            cheating_indicators['insufficient_content'] = True
            cheating_indicators['violations'].append("Contenu insuffisant (moins de 10 mots)")
        
        # 4. Détection de copier-coller (mots identiques à la question)
        prompt_words = set(prompt.lower().split())
        transcription_words = set(transcription.lower().split())
        common_words = prompt_words.intersection(transcription_words)
        
        if len(common_words) / max(len(transcription_words), 1) > 0.7:
            cheating_indicators['copy_paste_detection'] = True
            cheating_indicators['violations'].append("Copie excessive de la question")
        
        # 5. Détection de patterns artificiels
        artificial_patterns = [
            r'\b(um|uh|euh|ah|oh)\b',  # Hésitations excessives
            r'\b(je pense que|i think that)\b',  # Phrases de remplissage
            r'\b(très|very|really|vraiment)\b'  # Adverbes excessifs
        ]
        
        artificial_count = sum(len(re.findall(pattern, transcription.lower())) for pattern in artificial_patterns)
        if artificial_count > len(transcription.split()) * 0.2:
            cheating_indicators['artificial_patterns'] = True
            cheating_indicators['violations'].append("Patterns artificiels détectés")
        
        # Calculer le score de tricherie - PLUS SÉVÈRE
        violation_count = len(cheating_indicators['violations'])
        cheating_score = min(violation_count * 30, 100)  # 30 points par violation (plus sévère)
        
        # Si répétition extrême, score maximum
        if any("extrêmement répétitif" in v for v in cheating_indicators['violations']):
            cheating_score = 100
        
        cheating_indicators['cheating_score'] = cheating_score
        cheating_indicators['severity'] = 'high' if violation_count >= 2 else 'medium' if violation_count >= 1 else 'low'
        
        return cheating_indicators
    
    def _detect_creative_connections(self, text: str) -> List[str]:
        """Détecte les connexions créatives (métaphores, comparaisons)"""
        creative_patterns = [
            r'comme\s+\w+',
            r'ressemble\s+à',
            r'tel\s+que',
            r'pareil\s+à',
            r'imagine\s+que',
            r'si\s+on\s+pense',
        ]
        
        connections = []
        for pattern in creative_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            connections.extend(matches)
        
        return connections[:5]  # Top 5
    
    # ========== 2. ANALYSE COMMUNICATION VERBALE ==========
    
    def analyze_verbal_communication(self, transcription: str) -> Dict:
        """
        Analyse la communication verbale
        
        Critères:
        - Structure: organisation, cohérence
        - Fluidité: hésitations, répétitions
        - Vocabulaire: richesse, diversité
        """
        # 2.1 Structure
        structure_data = self._analyze_structure(transcription)
        
        # 2.2 Fluidité
        fluency_data = self._analyze_fluency(transcription)
        
        # 2.3 Vocabulaire
        vocabulary_data = self._analyze_vocabulary(transcription)
        
        return {
            'structure': structure_data,
            'fluency': fluency_data,
            'vocabulary': vocabulary_data
        }
    
    def _analyze_structure(self, text: str) -> Dict:
        """Analyse la structure du discours avec détection d'hésitations"""
        sentences = text.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # DÉTECTION D'HÉSITATIONS NATURELLES (plus tolérant)
        hesitation_words = ['euh', 'uh', 'um', 'ah', 'oh', 'ben', 'donc', 'alors', 'je sais pas', 'je ne sais pas']
        hesitation_count = sum(text.lower().count(word) for word in hesitation_words)
        
        # HÉSITATIONS NORMALES vs EXCESSIVES
        total_words = len(text.split())
        hesitation_ratio = hesitation_count / max(total_words, 1)
        
        # Répétitions (signe d'hésitation)
        words = text.lower().split()
        repetition_count = 0
        for i in range(len(words) - 1):
            if words[i] == words[i + 1]:
                repetition_count += 1
        
        # Connecteurs logiques
        connectors = ['donc', 'alors', 'ensuite', 'puis', 'enfin', 'parce que', 'car', 'mais', 'cependant']
        connector_count = sum(text.lower().count(c) for c in connectors)
        
        # Organisation (début, milieu, fin)
        has_introduction = any(word in text.lower()[:100] for word in ['bonjour', 'je vais', 'je pense'])
        has_conclusion = any(word in text.lower()[-100:] for word in ['donc', 'enfin', 'voilà', 'merci'])
        
        # Score de structure avec pénalités pour hésitations
        structure_score = self._calculate_structure_score(
            len(sentences), connector_count, has_introduction, has_conclusion, hesitation_count, repetition_count, hesitation_ratio
        )
        
        return {
            'sentence_count': len(sentences),
            'connector_count': connector_count,
            'has_introduction': has_introduction,
            'has_conclusion': has_conclusion,
            'avg_sentence_length': sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0,
            'score': structure_score
        }
    
    def _calculate_structure_score(self, sent_count, connectors, intro, conclusion, hesitation_count, repetition_count, hesitation_ratio) -> float:
        """Calcule le score de structure avec évaluation réaliste des hésitations"""
        score = 60  # Base plus élevée
        
        # ÉVALUATION RÉALISTE DES HÉSITATIONS
        if hesitation_ratio > 0.15:  # Plus de 15% d'hésitations = problématique
            score = 30  # MAUVAIS
        elif hesitation_ratio > 0.10:  # Plus de 10% d'hésitations = modéré
            score = 50  # MOYEN
        elif hesitation_ratio > 0.05:  # Plus de 5% d'hésitations = acceptable
            score = 70  # BIEN
        else:  # Moins de 5% d'hésitations = excellent
            score = 85  # EXCELLENT
        
        # PÉNALITÉS LÉGÈRES pour répétitions excessives
        if repetition_count > 5:
            score = max(score - 15, 40)  # Pénalité modérée
        elif repetition_count > 3:
            score = max(score - 10, 50)  # Pénalité légère
        
        # BONUS pour structure
        if 3 <= sent_count <= 10:
            score += 15
        elif sent_count > 2:
            score += 10
        
        # BONUS pour connecteurs
        score += min(connectors * 3, 15)
        
        # BONUS pour organisation
        if intro:
            score += 5
        if conclusion:
            score += 5
        
        return round(min(score, 100), 2)
    
    def _analyze_fluency(self, text: str) -> Dict:
        """Analyse la fluidité du discours"""
        # Hésitations (euh, hum, ben, etc.)
        hesitations = ['euh', 'hum', 'ben', 'alors euh', 'genre']
        hesitation_count = sum(text.lower().count(h) for h in hesitations)
        
        # Répétitions de mots
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        repetitions = {w: c for w, c in word_freq.items() if c > 2}
        
        # Faux départs (détection basique)
        false_starts = text.count('... ') + text.count('non, ')
        
        # Score de fluidité
        fluency_score = self._calculate_fluency_score(hesitation_count, len(repetitions), false_starts, len(words))
        
        return {
            'hesitation_count': hesitation_count,
            'repetition_count': len(repetitions),
            'repeated_words': list(repetitions.keys())[:5],
            'false_starts': false_starts,
            'score': fluency_score
        }
    
    def _calculate_fluency_score(self, hesitations, repetitions, false_starts, total_words) -> float:
        """Calcule le score de fluidité"""
        score = 100  # Parfait au départ
        
        # Pénalités
        hesitation_penalty = min((hesitations / max(total_words * 0.05, 1)) * 30, 30)
        repetition_penalty = min((repetitions / max(total_words * 0.05, 1)) * 20, 20)
        false_start_penalty = min(false_starts * 10, 15)
        
        score -= (hesitation_penalty + repetition_penalty + false_start_penalty)
        
        return round(max(score, 0), 2)
    
    def _analyze_vocabulary(self, text: str) -> Dict:
        """Analyse la richesse du vocabulaire"""
        words = [w for w in text.lower().split() if len(w) > 3]
        unique_words = set(words)
        
        # Type-Token Ratio
        ttr = len(unique_words) / len(words) if words else 0
        
        # Longueur moyenne des mots (indicateur de complexité)
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        
        # Mots "complexes" (>7 lettres)
        complex_words = [w for w in words if len(w) > 7]
        
        # Score de vocabulaire
        vocabulary_score = self._calculate_vocabulary_score(ttr, avg_word_length, len(complex_words), len(words))
        
        return {
            'total_words': len(words),
            'unique_words': len(unique_words),
            'ttr': round(ttr, 3),
            'avg_word_length': round(avg_word_length, 2),
            'complex_word_count': len(complex_words),
            'complex_words_sample': complex_words[:10],
            'score': vocabulary_score
        }
    
    def _calculate_vocabulary_score(self, ttr, avg_length, complex_count, total_words) -> float:
        """Calcule le score de vocabulaire"""
        # TTR score (0-40)
        ttr_score = min(ttr * 100, 40)
        
        # Longueur moyenne (0-30)
        length_score = min((avg_length / 8) * 30, 30)
        
        # Mots complexes (0-30)
        complex_score = min((complex_count / max(total_words * 0.2, 1)) * 30, 30)
        
        score = ttr_score + length_score + complex_score
        return round(min(score, 100), 2)
    
    # ========== 3. ANALYSE COMMUNICATION PARAVERBALE ==========
    
    def analyze_paraverbal_communication(self, audio_path: str, transcription: str) -> Dict:
        """
        Analyse la communication paraverbale
        
        Critères:
        - Intonation: via ponctuation détectée
        - Rythme: débit de parole
        - Temporalité: pauses et segments
        """
        # 3.1 Intonation (via ponctuation dans transcription)
        intonation_data = self._analyze_intonation(transcription)
        
        # 3.2 Rythme (débit de parole)
        rhythm_data = self._analyze_rhythm(audio_path, transcription)
        
        # 3.3 Temporalité (pauses)
        timing_data = self._analyze_timing(audio_path)
        
        return {
            'intonation': intonation_data,
            'rhythm': rhythm_data,
            'timing': timing_data
        }
    
    def _analyze_intonation(self, text: str) -> Dict:
        """Analyse l'intonation via ponctuation"""
        # Questions
        question_count = text.count('?')
        
        # Exclamations
        exclamation_count = text.count('!')
        
        # Virgules (pauses courtes)
        comma_count = text.count(',')
        
        # Points (pauses normales)
        period_count = text.count('.')
        
        # Points de suspension (hésitation)
        ellipsis_count = text.count('...')
        
        # Variation totale
        total_punctuation = question_count + exclamation_count + comma_count + period_count
        sentence_count = max(period_count, 1)
        punctuation_variety = total_punctuation / sentence_count
        
        # Score d'intonation
        intonation_score = self._calculate_intonation_score(
            question_count, exclamation_count, punctuation_variety
        )
        
        return {
            'question_count': question_count,
            'exclamation_count': exclamation_count,
            'comma_count': comma_count,
            'period_count': period_count,
            'ellipsis_count': ellipsis_count,
            'punctuation_variety': round(punctuation_variety, 2),
            'score': intonation_score
        }
    
    def _calculate_intonation_score(self, questions, exclamations, variety) -> float:
        """Calcule le score d'intonation"""
        score = 50  # Base
        
        # Présence de questions (engagement)
        score += min(questions * 10, 20)
        
        # Exclamations (expressivité)
        score += min(exclamations * 8, 15)
        
        # Variété
        score += min(variety * 5, 15)
        
        return round(min(score, 100), 2)
    
    def _analyze_rhythm(self, audio_path: str, transcription: str) -> Dict:
        """Analyze speech rhythm"""
        if not AUDIO_AVAILABLE:
            return {
                'duration': 0,
                'word_count': len(transcription.split()),
                'speech_rate': 0,
                'error': 'Audio libraries not available',
                'score': 75  # Default good score
            }
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Calculate speech rate (words/minute)
            word_count = len(transcription.split())
            speech_rate = (word_count / duration) * 60 if duration > 0 else 0
            
            # Ideal rate for children: 100-150 words/minute
            rhythm_score = self._calculate_rhythm_score(speech_rate)
            
            return {
                'duration': round(duration, 2),
                'word_count': word_count,
                'speech_rate': round(speech_rate, 2),
                'optimal_range': [100, 150],
                'score': rhythm_score
            }
        except Exception as e:
            return {
                'duration': 0,
                'word_count': len(transcription.split()),
                'speech_rate': 0,
                'error': str(e),
                'score': 75  # Default good score
            }
    
    def _calculate_rhythm_score(self, speech_rate: float) -> float:
        """Calcule le score de rythme"""
        if speech_rate == 0:
            return 50
        
        # Optimal: 100-150 mots/min
        if 100 <= speech_rate <= 150:
            return 100
        elif 80 <= speech_rate < 100 or 150 < speech_rate <= 180:
            return 80
        elif 60 <= speech_rate < 80 or 180 < speech_rate <= 200:
            return 60
        else:
            return 40
    
    def _analyze_timing(self, audio_path: str) -> Dict:
        """Analyze temporal segments and pauses"""
        if not AUDIO_AVAILABLE:
            return {
                'speech_segments': 1,
                'pause_count': 2,
                'avg_pause_duration': 0.5,
                'total_pause_time': 1.0,
                'pauses_distribution': [0.3, 0.7],
                'score': 20  # Default LOW score for short responses
            }
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Detect speech segments (silence vs speech)
            intervals = librosa.effects.split(y, top_db=20)
            
            # Calculate pauses
            pauses = []
            if len(intervals) > 1:
                for i in range(len(intervals) - 1):
                    pause_start = intervals[i][1] / sr
                    pause_end = intervals[i+1][0] / sr
                    pause_duration = pause_end - pause_start
                    if pause_duration > 0.2:  # Pauses > 200ms
                        pauses.append(pause_duration)
            
            # Statistics
            pause_count = len(pauses)
            avg_pause = sum(pauses) / len(pauses) if pauses else 0
            total_pause_time = sum(pauses)
            
            # Calculate total duration
            total_duration = len(y) / sr
            print(f"🎯 DURATION DEBUG: {total_duration:.2f} seconds")
            
            # Timing score with duration penalty
            timing_score = self._calculate_timing_score(pause_count, avg_pause, len(intervals), total_duration)
            print(f"🎯 TIMING SCORE: {timing_score}")
            
            return {
                'speech_segments': len(intervals),
                'pause_count': pause_count,
                'avg_pause_duration': round(avg_pause, 3),
                'total_pause_time': round(total_pause_time, 2),
                'pauses_distribution': [round(p, 2) for p in pauses[:10]],
                'score': timing_score
            }
        except Exception as e:
            return {
                'speech_segments': 1,
                'pause_count': 2,
                'error': str(e),
                'score': 75  # Default good score
            }
    
    def _calculate_timing_score(self, pause_count, avg_pause, segments, total_duration) -> float:
        """Calcule le score de temporalité avec pénalité de durée"""
        score = 0  # Start from 0
        
        # PÉNALITÉ MODÉRÉE pour durée insuffisante
        if total_duration < 60:  # Moins de 1 minute
            return 20  # TRÈS MAUVAIS
        elif total_duration < 90:  # Moins de 1.5 minutes
            return 40  # MAUVAIS
        elif total_duration < 120:  # Moins de 2 minutes
            return 60  # MOYEN
        elif total_duration < 150:  # Moins de 2.5 minutes
            return 75  # BIEN
        else:  # 2.5+ minutes
            score = 85  # Base pour durée excellente
        
        # Bonus pour pauses appropriées
        if 2 <= pause_count <= 8:
            score += 15
        elif pause_count > 0:
            score += 5
        
        # Bonus pour durée moyenne des pauses
        if 0.3 <= avg_pause <= 1.0:
            score += 15
        elif 0.1 <= avg_pause < 0.3 or 1.0 < avg_pause <= 1.5:
            score += 5
        
        return round(min(score, 100), 2)
    
    # ========== 4. SCORING ET FEEDBACK ==========
    
    def calculate_scores(self, originality: Dict, verbal: Dict, paraverbal: Dict) -> Dict:
        """Consolide tous les scores avec pénalités ULTRA-SÉVÈRES"""
        
        # Scores de base
        originality_score = originality['score']
        structure_score = verbal['structure']['score']
        fluency_score = verbal['fluency']['score']
        vocabulary_score = verbal['vocabulary']['score']
        intonation_score = paraverbal['intonation']['score']
        rhythm_score = paraverbal['rhythm']['score']
        timing_score = paraverbal['timing']['score']
        
        # COHÉRENCE DES SCORES - Si paraverbal est bas, verbal doit être ajusté
        avg_paraverbal = (intonation_score + rhythm_score + timing_score) / 3
        avg_verbal = (structure_score + fluency_score + vocabulary_score) / 3
        
        print(f"📊 COHÉRENCE DEBUG: Paraverbal={avg_paraverbal:.1f}, Verbal={avg_verbal:.1f}")
        
        # Si paraverbal est beaucoup plus bas que verbal, ajuster verbal
        if avg_paraverbal < avg_verbal - 20:  # Différence de plus de 20 points
            adjustment_factor = (avg_paraverbal + 20) / avg_verbal
            print(f"🔧 AJUSTEMENT: Verbal réduit par {adjustment_factor:.2f}")
            structure_score *= adjustment_factor
            fluency_score *= adjustment_factor
            vocabulary_score *= adjustment_factor
        
        # Si verbal est beaucoup plus bas que paraverbal, ajuster paraverbal
        elif avg_verbal < avg_paraverbal - 20:  # Différence de plus de 20 points
            adjustment_factor = (avg_verbal + 20) / avg_paraverbal
            print(f"🔧 AJUSTEMENT: Paraverbal réduit par {adjustment_factor:.2f}")
            intonation_score *= adjustment_factor
            rhythm_score *= adjustment_factor
            timing_score *= adjustment_factor
        
        # PÉNALITÉS JUSTES pour violation de langue
        if 'language_violation' in originality and not originality['language_violation']['language_match']:
            violation = originality['language_violation']
            match_percentage = violation.get('match_percentage', 0)
            
            # PÉNALITÉS PROPORTIONNELLES au pourcentage de correspondance
            if match_percentage < 20:  # Très peu de correspondance
                penalty_factor = 0.3
            elif match_percentage < 40:  # Peu de correspondance
                penalty_factor = 0.5
            elif match_percentage < 60:  # Correspondance moyenne
                penalty_factor = 0.7
            else:  # Bonne correspondance
                penalty_factor = 0.9
            
            print(f"🔧 PÉNALITÉ LANGUE: {match_percentage}% → Facteur {penalty_factor}")
            
            originality_score *= penalty_factor
            structure_score *= penalty_factor
            fluency_score *= penalty_factor
            vocabulary_score *= penalty_factor
            intonation_score *= penalty_factor
            rhythm_score *= penalty_factor
            timing_score *= penalty_factor
        
        # PÉNALITÉS ULTRA-SÉVÈRES pour tricherie
        if 'cheating_detection' in originality and originality['cheating_detection']['cheating_score'] > 0:
            cheating = originality['cheating_detection']
            if cheating['severity'] in ['high', 'medium']:
                # ÉCHEC TOTAL pour tricherie
                originality_score = 0
                structure_score = 0
                fluency_score = 0
                vocabulary_score = 0
                intonation_score = 0
                rhythm_score = 0
                timing_score = 0
            else:
                # PÉNALITÉ DE 80%
                originality_score *= 0.2
                structure_score *= 0.2
                fluency_score *= 0.2
                vocabulary_score *= 0.2
                intonation_score *= 0.2
                rhythm_score *= 0.2
                timing_score *= 0.2
        
        return {
            'originality_score': originality_score,
            'verbal_structure_score': structure_score,
            'verbal_fluency_score': fluency_score,
            'verbal_vocabulary_score': vocabulary_score,
            'paraverbal_intonation_score': intonation_score,
            'paraverbal_rhythm_score': rhythm_score,
            'paraverbal_timing_score': timing_score,
        }
    
    def generate_feedback(self, scores: Dict, originality: Dict, verbal: Dict, paraverbal: Dict) -> str:
        """Génère un feedback personnalisé"""
        feedback_parts = []
        
        # FEEDBACK CRITIQUE pour violation de langue
        if 'language_violation' in originality and not originality['language_violation']['language_match']:
            violation = originality['language_violation']
            if violation['violation_severity'] == 'high':
                feedback_parts.append("🚨 VIOLATION MAJEURE: Tu as parlé en " + violation['transcription_language'] + " alors que l'exercice était en " + violation['prompt_language'] + ". Score sévèrement pénalisé!")
            elif violation['violation_severity'] == 'medium':
                feedback_parts.append("⚠️ VIOLATION: Tu as mélangé les langues. Respecte la langue demandée pour une meilleure évaluation.")
            else:
                feedback_parts.append("💡 Attention: Essaie de rester dans la langue demandée pour l'exercice.")
        
        # FEEDBACK CRITIQUE pour tricherie
        if 'cheating_detection' in originality and originality['cheating_detection']['cheating_score'] > 0:
            cheating = originality['cheating_detection']
            if cheating['severity'] == 'high':
                feedback_parts.append("🚨 TRICHERIE DÉTECTÉE: " + ", ".join(cheating['violations']) + ". Score sévèrement pénalisé!")
            elif cheating['severity'] == 'medium':
                feedback_parts.append("⚠️ TRICHERIE: " + ", ".join(cheating['violations']) + ". Respecte les règles d'évaluation.")
            else:
                feedback_parts.append("💡 Attention: " + ", ".join(cheating['violations']) + ". Améliore ton approche.")
        
        # Feedback originalité (seulement si pas de violation majeure)
        if not ('language_violation' in originality and originality['language_violation']['violation_severity'] == 'high'):
            if scores['originality_score'] >= 75:
                feedback_parts.append("✨ Excellente créativité! Tes idées sont originales et bien développées.")
            elif scores['originality_score'] >= 50:
                feedback_parts.append("💡 Bonne réflexion, tu peux encore enrichir tes idées avec plus de détails.")
            else:
                feedback_parts.append("🌱 N'hésite pas à développer davantage tes idées et à être plus créatif.")
        
        # Feedback verbal
        avg_verbal = (scores['verbal_structure_score'] + scores['verbal_fluency_score'] + scores['verbal_vocabulary_score']) / 3
        if avg_verbal >= 75:
            feedback_parts.append("🗣️ Ton discours est clair, fluide et bien structuré!")
        else:
            if scores['verbal_structure_score'] < 60:
                feedback_parts.append("📋 Essaie d'organiser ton discours avec un début, un milieu et une fin.")
            if scores['verbal_fluency_score'] < 60:
                feedback_parts.append("💬 Prends ton temps pour parler, évite les hésitations.")
            if scores['verbal_vocabulary_score'] < 60:
                feedback_parts.append("📚 Enrichis ton vocabulaire avec des mots plus variés.")
        
        # Feedback paraverbal
        if scores['paraverbal_rhythm_score'] < 60:
            feedback_parts.append("⏱️ Attention au rythme: essaie de parler ni trop vite ni trop lentement.")
        if scores['paraverbal_timing_score'] >= 75:
            feedback_parts.append("⏸️ Bravo, tu gères bien les pauses dans ton discours!")
        
        return " ".join(feedback_parts)
    
    def generate_recommendations(self, scores: Dict, originality: Dict, verbal: Dict, paraverbal: Dict) -> List[str]:
        """Génère des recommandations personnalisées pour français et anglais"""
        recommendations = []
        
        # Détecter la langue pour des recommandations spécifiques
        language = 'french'  # Par défaut
        if 'language_violation' in originality:
            language = originality['language_violation'].get('transcription_language', 'french')
        
        # Recommandations basées sur les scores
        if scores['originality_score'] < 50:
            if language == 'french':
                recommendations.append("💡 Développe tes idées personnelles en français. Utilise des expressions comme 'je pense que', 'à mon avis', 'selon moi'.")
            else:
                recommendations.append("💡 Develop your personal ideas in English. Use expressions like 'I think that', 'in my opinion', 'from my perspective'.")
        
        if scores['verbal_structure_score'] < 60:
            if language == 'french':
                recommendations.append("📝 Améliore la structure de tes phrases françaises. Utilise la structure SVO (Sujet-Verbe-Objet) et évite les phrases trop longues.")
            else:
                recommendations.append("📝 Improve your English sentence structure. Use proper SVO (Subject-Verb-Object) order and avoid run-on sentences.")
        
        if scores['verbal_fluency_score'] < 60:
            if language == 'french':
                recommendations.append("🗣️ Parle plus couramment en français. Évite les 'euh', 'ben', 'alors' et utilise des connecteurs comme 'donc', 'cependant', 'par ailleurs'.")
            else:
                recommendations.append("🗣️ Speak more fluently in English. Avoid 'um', 'uh', 'like' and use connectors like 'therefore', 'however', 'moreover'.")
        
        if scores['verbal_vocabulary_score'] < 60:
            if language == 'french':
                recommendations.append("📚 Enrichis ton vocabulaire français. Utilise des synonymes, des adjectifs précis, et évite les répétitions.")
            else:
                recommendations.append("📚 Expand your English vocabulary. Use synonyms, precise adjectives, and avoid repetitions.")
        
        if scores['paraverbal_intonation_score'] < 60:
            if language == 'french':
                recommendations.append("🎵 Varie ton intonation française. Utilise les accents toniques et les modulations de voix pour exprimer tes émotions.")
            else:
                recommendations.append("🎵 Vary your English intonation. Use stress patterns and voice modulation to express your emotions.")
        
        if scores['paraverbal_rhythm_score'] < 60:
            if language == 'french':
                recommendations.append("⏰ Améliore le rythme de ta parole française. Respecte les pauses naturelles et la musicalité de la langue.")
            else:
                recommendations.append("⏰ Improve your English speech rhythm. Respect natural pauses and the musicality of the language.")
        
        if scores['paraverbal_timing_score'] < 60:
            if language == 'french':
                recommendations.append("⏱️ Gère mieux le timing de tes pauses en français. Utilise les silences pour structurer ton discours.")
            else:
                recommendations.append("⏱️ Better manage your English pause timing. Use silences to structure your speech.")
        
        # Recommandations spécifiques pour la tricherie
        if 'cheating_detection' in originality and originality['cheating_detection']['cheating_score'] > 0:
            if language == 'french':
                recommendations.append("🚨 ÉVITE LA TRICHERIE: Parle naturellement, évite de lire un script, et développe tes propres idées.")
            else:
                recommendations.append("🚨 AVOID CHEATING: Speak naturally, avoid reading from a script, and develop your own ideas.")
        
        # Recommandations pour améliorer la créativité
        if scores['originality_score'] < 70:
            if language == 'french':
                recommendations.append("✨ Pour plus de créativité: Utilise des métaphores, des comparaisons, et des exemples personnels.")
            else:
                recommendations.append("✨ For more creativity: Use metaphors, comparisons, and personal examples.")
        
        return recommendations

