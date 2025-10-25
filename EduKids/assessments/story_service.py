"""
AI Story Generation Service using Gemini API
"""
import google.generativeai as genai
import json
from django.conf import settings


class StoryGeneratorService:
    """
    Service to generate stories using Gemini API
    """
    
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key="AIzaSyD19fEQdWAy8LMILMWvtKtWylTz7diTE6E")
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_story(self, theme, age_group='6-7', difficulty=1):
        """
        Generate a story with comprehension questions
        
        Args:
            theme: Story theme (teamwork, kindness, etc.)
            age_group: Target age group
            difficulty: Difficulty level 1-5
        
        Returns:
            dict: Story data with title, paragraphs, questions
        """
        
        prompt = f"""
        Create a short, fun, and educational story for children aged {age_group} about {theme}.
        
        Requirements:
        - 3-6 short paragraphs
        - Simple, playful, age-appropriate language
        - 1-2 main characters (kids, animals, or friendly robots)
        - Positive message about {theme}
        - Difficulty level: {difficulty}/5
        
        Also create 3 comprehension questions about the story with their answers.
        
        Return ONLY a valid JSON object in this exact format (no markdown, no extra text):
        {{
            "title": "Story Title Here",
            "story": ["Paragraph 1 text...", "Paragraph 2 text...", "Paragraph 3 text..."],
            "characters": ["Character 1", "Character 2"],
            "questions": [
                {{"question": "Question 1?", "answer": "Answer 1"}},
                {{"question": "Question 2?", "answer": "Answer 2"}},
                {{"question": "Question 3?", "answer": "Answer 3"}}
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse JSON
            story_data = json.loads(response_text)
            
            return story_data
            
        except Exception as e:
            print(f"Error generating story: {e}")
            # Return fallback story
            return self._get_fallback_story(theme)
    
    def _get_fallback_story(self, theme):
        """Fallback story if API fails"""
        return {
            "title": f"A Story About {theme.title()}",
            "story": [
                "Once upon a time, there was a little robot named Robo.",
                "Robo loved to help friends and learn new things every day.",
                "One day, Robo discovered something amazing about friendship!"
            ],
            "characters": ["Robo", "Friends"],
            "questions": [
                {"question": "What is the robot's name?", "answer": "Robo"},
                {"question": "What does Robo love to do?", "answer": "Help friends and learn"},
                {"question": "What did Robo discover?", "answer": "Something about friendship"}
            ]
        }
    
    def evaluate_answer(self, student_answer, correct_answer):
        """
        Use AI to evaluate if student's answer is correct
        
        Args:
            student_answer: Student's text answer
            correct_answer: Expected answer
        
        Returns:
            dict: {is_correct: bool, feedback: str}
        """
        
        prompt = f"""
        You are a kind teacher evaluating a child's answer to a comprehension question.
        
        Correct Answer: {correct_answer}
        Student's Answer: {student_answer}
        
        Is the student's answer correct or close enough? Consider:
        - Spelling mistakes are okay
        - Partial answers that show understanding are acceptable
        - Different wording with same meaning is correct
        
        Return ONLY a JSON object:
        {{
            "is_correct": true or false,
            "feedback": "Encouraging feedback message for the child"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean response
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            print(f"Error evaluating answer: {e}")
            # Simple fallback evaluation
            is_correct = student_answer.lower().strip() in correct_answer.lower()
            return {
                "is_correct": is_correct,
                "feedback": "Great try! Keep reading and learning!" if is_correct else "Good effort! Try reading the story again."
            }
    
    def generate_feedback(self, score, emotion=None):
        """
        Generate encouraging feedback based on score and emotion
        
        Args:
            score: Score out of 5
            emotion: Detected emotion (optional)
        
        Returns:
            str: Encouraging feedback message
        """
        
        emotion_context = f" You seem {emotion}!" if emotion else ""
        
        if score >= 4:
            messages = [
                f"🌟 Amazing work!{emotion_context} You're a super reader!",
                f"🎉 Fantastic! You understood the story so well!{emotion_context}",
                f"⭐ Excellent! You're becoming a reading star!{emotion_context}"
            ]
        elif score >= 3:
            messages = [
                f"👏 Great job!{emotion_context} You're doing really well!",
                f"🎈 Good work! Keep reading and learning!{emotion_context}",
                f"✨ Nice! You're making wonderful progress!{emotion_context}"
            ]
        elif score >= 2:
            messages = [
                f"💪 Good try!{emotion_context} Practice makes perfect!",
                f"🌈 You're learning! Try reading the story again!{emotion_context}",
                f"🎯 Keep going! Every story makes you smarter!{emotion_context}"
            ]
        else:
            messages = [
                f"🌻 That's okay!{emotion_context} Let's read together again!",
                f"💝 Don't worry! Every reader starts somewhere!{emotion_context}",
                f"🌟 You tried your best! Let's practice more!{emotion_context}"
            ]
        
        import random
        return random.choice(messages)
