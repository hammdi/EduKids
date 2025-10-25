"""
Configuration OpenAI
"""
import os

# Configuration OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-proj-your-key-here')

# Remplacez par votre vraie clé OpenAI
# Vous pouvez aussi l'ajouter dans vos variables d'environnement
if OPENAI_API_KEY == 'sk-proj-your-key-here':
    print("⚠️  ATTENTION: Veuillez configurer votre clé OpenAI dans openai_config.py")
    print("   Ou définissez la variable d'environnement OPENAI_API_KEY")
