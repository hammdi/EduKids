"""
Service d'analyse vocale par IA pour EduKids
Analyse complète: Originalité, Communication Verbale et Paraverbale
"""
import os
import json
import re
from typing import Dict, List, Tuple
from datetime import datetime
import librosa
import numpy as np
from textblob import TextBlob
import spacy


class VoiceAnalyzer:
    """
    Analyseur principal pour l'évaluation vocale
    """
    
    def __init__(self):
        """Initialiser les modèles NLP"""
        try:
            self.nlp = spacy.load('fr_core_news_sm')
        except:
            # Fallback si modèle français pas installé
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
        """
        doc = self.nlp(transcription) if self.nlp else None
        prompt_doc = self.nlp(prompt) if self.nlp else None
        
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
        
        # Score d'originalité (0-100)
        originality_score = self._calculate_originality_score(
            unique_words, lexical_diversity, named_entities, total_words
        )
        
        return {
            'unique_words': list(unique_words)[:20],  # Top 20
            'unique_word_count': len(unique_words),
            'lexical_diversity': round(lexical_diversity, 3),
            'named_entities': named_entities,
            'creative_connections': self._detect_creative_connections(transcription),
            'score': originality_score
        }
    
    def _calculate_originality_score(self, unique_words, lexical_diversity, entities, total_words) -> float:
        """Calcule le score d'originalité"""
        # Pondérations
        unique_score = min(len(unique_words) / max(total_words * 0.5, 1) * 100, 100)  # 40%
        diversity_score = lexical_diversity * 100  # 40%
        entity_score = min(len(entities) / max(total_words * 0.1, 1) * 100, 100)  # 20%
        
        final_score = (unique_score * 0.4) + (diversity_score * 0.4) + (entity_score * 0.2)
        return round(min(final_score, 100), 2)
    
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
        """Analyse la structure du discours"""
        sentences = text.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Connecteurs logiques
        connectors = ['donc', 'alors', 'ensuite', 'puis', 'enfin', 'parce que', 'car', 'mais', 'cependant']
        connector_count = sum(text.lower().count(c) for c in connectors)
        
        # Organisation (début, milieu, fin)
        has_introduction = any(word in text.lower()[:100] for word in ['bonjour', 'je vais', 'je pense'])
        has_conclusion = any(word in text.lower()[-100:] for word in ['donc', 'enfin', 'voilà', 'merci'])
        
        # Score de structure
        structure_score = self._calculate_structure_score(
            len(sentences), connector_count, has_introduction, has_conclusion
        )
        
        return {
            'sentence_count': len(sentences),
            'connector_count': connector_count,
            'has_introduction': has_introduction,
            'has_conclusion': has_conclusion,
            'avg_sentence_length': sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0,
            'score': structure_score
        }
    
    def _calculate_structure_score(self, sent_count, connectors, intro, conclusion) -> float:
        """Calcule le score de structure"""
        score = 50  # Base
        
        # Nombre de phrases approprié
        if 3 <= sent_count <= 10:
            score += 20
        elif sent_count > 2:
            score += 10
        
        # Connecteurs
        score += min(connectors * 5, 20)
        
        # Organisation
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
        """Analyse le rythme de parole"""
        try:
            # Charger l'audio
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Calculer le débit (mots/minute)
            word_count = len(transcription.split())
            speech_rate = (word_count / duration) * 60 if duration > 0 else 0
            
            # Débit idéal pour enfants: 100-150 mots/minute
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
                'score': 50  # Score neutre en cas d'erreur
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
        """Analyse les segments temporels et pauses"""
        try:
            # Charger l'audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Détecter les segments de parole (silence vs speech)
            intervals = librosa.effects.split(y, top_db=20)
            
            # Calculer les pauses
            pauses = []
            if len(intervals) > 1:
                for i in range(len(intervals) - 1):
                    pause_start = intervals[i][1] / sr
                    pause_end = intervals[i+1][0] / sr
                    pause_duration = pause_end - pause_start
                    if pause_duration > 0.2:  # Pauses > 200ms
                        pauses.append(pause_duration)
            
            # Statistiques
            pause_count = len(pauses)
            avg_pause = sum(pauses) / len(pauses) if pauses else 0
            total_pause_time = sum(pauses)
            
            # Score de temporalité
            timing_score = self._calculate_timing_score(pause_count, avg_pause, len(intervals))
            
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
                'speech_segments': 0,
                'pause_count': 0,
                'error': str(e),
                'score': 50
            }
    
    def _calculate_timing_score(self, pause_count, avg_pause, segments) -> float:
        """Calcule le score de temporalité"""
        score = 70  # Base
        
        # Présence de pauses appropriées
        if 2 <= pause_count <= 8:
            score += 15
        elif pause_count > 0:
            score += 5
        
        # Durée moyenne des pauses (0.3-1.0s optimal)
        if 0.3 <= avg_pause <= 1.0:
            score += 15
        elif 0.1 <= avg_pause < 0.3 or 1.0 < avg_pause <= 1.5:
            score += 5
        
        return round(min(score, 100), 2)
    
    # ========== 4. SCORING ET FEEDBACK ==========
    
    def calculate_scores(self, originality: Dict, verbal: Dict, paraverbal: Dict) -> Dict:
        """Consolide tous les scores"""
        return {
            'originality_score': originality['score'],
            'verbal_structure_score': verbal['structure']['score'],
            'verbal_fluency_score': verbal['fluency']['score'],
            'verbal_vocabulary_score': verbal['vocabulary']['score'],
            'paraverbal_intonation_score': paraverbal['intonation']['score'],
            'paraverbal_rhythm_score': paraverbal['rhythm']['score'],
            'paraverbal_timing_score': paraverbal['timing']['score'],
        }
    
    def generate_feedback(self, scores: Dict, originality: Dict, verbal: Dict, paraverbal: Dict) -> str:
        """Génère un feedback personnalisé"""
        feedback_parts = []
        
        # Feedback originalité
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

