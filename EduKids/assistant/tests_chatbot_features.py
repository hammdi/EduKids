"""
Tests de base pour les nouvelles fonctionnalités du chatbot EduKids

Pour exécuter ces tests:
    python manage.py test assistant.tests_chatbot_features

Ou directement avec pytest:
    pytest assistant/tests_chatbot_features.py -v
"""
import unittest
from assistant.context_manager import (
    get_session, update_history, set_current_topic, 
    get_current_topic, set_quiz, get_quiz, clear_session
)
from assistant.reference_resolver import resolve_reference
from assistant.quiz_manager import generate_quiz, grade_answer


class ContextManagerTests(unittest.TestCase):
    """Tests pour le gestionnaire de contexte en mémoire"""
    
    def setUp(self):
        self.conv_id = 9999  # ID de test
        clear_session(self.conv_id)
    
    def tearDown(self):
        clear_session(self.conv_id)
    
    def test_session_creation(self):
        """Test création session"""
        session = get_session(self.conv_id)
        self.assertIsNotNone(session)
        self.assertIn('history', session)
        self.assertIn('current_topic', session)
    
    def test_update_history(self):
        """Test ajout messages à l'historique"""
        update_history(self.conv_id, 'student', 'Bonjour')
        update_history(self.conv_id, 'assistant', 'Salut!')
        session = get_session(self.conv_id)
        self.assertEqual(len(session['history']), 2)
        self.assertEqual(session['history'][0], ('student', 'Bonjour'))
    
    def test_current_topic(self):
        """Test stockage et récupération du sujet actuel"""
        set_current_topic(self.conv_id, 'Harry Potter')
        topic = get_current_topic(self.conv_id)
        self.assertEqual(topic, 'Harry Potter')
    
    def test_quiz_storage(self):
        """Test stockage quiz dans session"""
        quiz = {'title': 'Test Quiz', 'questions': []}
        set_quiz(self.conv_id, quiz)
        retrieved = get_quiz(self.conv_id)
        self.assertEqual(retrieved['title'], 'Test Quiz')


class ReferenceResolverTests(unittest.TestCase):
    """Tests pour la résolution de références implicites"""
    
    def test_no_implicit_reference(self):
        """Test message sans référence implicite"""
        message = "Qui est Albert Einstein ?"
        session = {'current_topic': 'Physique', 'history': []}
        result = resolve_reference(message, session)
        # Devrait rester inchangé (nom propre présent)
        self.assertEqual(result, message)
    
    def test_implicit_pronoun(self):
        """Test résolution pronoms implicites"""
        message = "C'est quoi ses livres ?"
        session = {'current_topic': 'Sujet: Freud et Psychologie', 'history': []}
        result = resolve_reference(message, session)
        # Devrait ajouter contexte
        self.assertIn('Freud', result)
        self.assertIn('ses livres', result)
    
    def test_empty_session(self):
        """Test avec session vide"""
        message = "C'est quoi ça ?"
        session = {'current_topic': None, 'history': []}
        result = resolve_reference(message, session)
        # Sans contexte, devrait rester inchangé
        self.assertEqual(result, message)


class QuizManagerTests(unittest.TestCase):
    """Tests pour le gestionnaire de quiz"""
    
    def test_quiz_generation_fallback(self):
        """Test génération quiz (fallback si pas d'API)"""
        # Même sans clé Mistral, le fallback devrait fonctionner
        quiz = generate_quiz(topic='Test', num_questions=2, age=10)
        self.assertIsNotNone(quiz)
        self.assertIn('title', quiz)
        self.assertIn('questions', quiz)
        self.assertEqual(len(quiz['questions']), 2)
    
    def test_grade_answer_numeric(self):
        """Test correction réponse numérique"""
        quiz = {
            'questions': [{
                'id': 1,
                'question': 'Test question',
                'choices': ['A', 'B', 'C', 'D'],
                'answer_index': 1
            }]
        }
        # Bonne réponse (index 1 en 1-based = '2')
        result = grade_answer(quiz, 1, '2')
        self.assertTrue(result['is_correct'])
        self.assertEqual(result['user_index'], 1)
    
    def test_grade_answer_text(self):
        """Test correction réponse texte"""
        quiz = {
            'questions': [{
                'id': 1,
                'question': 'Capitale de France ?',
                'choices': ['Londres', 'Paris', 'Berlin', 'Rome'],
                'answer_index': 1
            }]
        }
        # Bonne réponse en texte
        result = grade_answer(quiz, 1, 'Paris')
        self.assertTrue(result['is_correct'])
    
    def test_grade_answer_wrong(self):
        """Test correction mauvaise réponse"""
        quiz = {
            'questions': [{
                'id': 1,
                'question': 'Test',
                'choices': ['A', 'B', 'C'],
                'answer_index': 0
            }]
        }
        result = grade_answer(quiz, 1, '2')  # Mauvais (index 1 au lieu de 0)
        self.assertFalse(result['is_correct'])
        self.assertIn('explanation', result)


class IntegrationTests(unittest.TestCase):
    """Tests d'intégration des fonctionnalités"""
    
    def test_full_conversation_flow(self):
        """Test flux complet: contexte + résolution + quiz"""
        conv_id = 8888
        clear_session(conv_id)
        
        # 1. Conversation initiale
        update_history(conv_id, 'student', 'Parle-moi de Freud')
        update_history(conv_id, 'assistant', 'Freud était un psychanalyste...')
        set_current_topic(conv_id, 'Sujet: Freud et Psychologie')
        
        # 2. Question avec référence implicite
        question = "C'est quoi ses théories ?"
        session = get_session(conv_id)
        resolved = resolve_reference(question, session)
        self.assertIn('Freud', resolved)
        
        # 3. Quiz sur le sujet
        quiz = generate_quiz(topic='Freud', num_questions=3, age=12)
        set_quiz(conv_id, quiz)
        stored_quiz = get_quiz(conv_id)
        self.assertIsNotNone(stored_quiz)
        
        # 4. Nettoyage
        clear_session(conv_id)


if __name__ == '__main__':
    # Exécuter tests
    unittest.main(verbosity=2)
